"""
Celery tasks for DocForge.

Sprint 1: scan_repo_task clones the repo, runs the FastAPI parser on all
Python files, and persists extracted endpoints to the database.
AI doc generation (chains.py) is Sprint 2 scope and is left as stubs.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from typing import Any

import redis
from celery import shared_task  # type: ignore[import-untyped]

from app.core.analytics import capture_event
from app.core.config import settings
from app.core.parser import FastAPIParser
from app.core.pipeline import run_pipeline


def _update_progress(r: redis.Redis, repo_id: str, status: str, progress: int) -> None:
    r.set(f"scan_status:{repo_id}", json.dumps({"status": status, "progress": progress}))


def _update_repo_scan_status(repo_id: str, scan_status: str) -> None:
    """Update repos.scan_status in the database (synchronous via psycopg2)."""
    import psycopg2

    # Build a sync DATABASE_URL for use in the Celery worker context
    sync_url = settings.DATABASE_URL.replace("+asyncpg", "")
    # psycopg2 expects postgresql:// not postgresql+psycopg2://
    sync_url = sync_url.replace("postgresql+psycopg2", "postgresql")

    try:
        conn = psycopg2.connect(sync_url)
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE repos SET scan_status = %s, updated_at = NOW() WHERE id = %s",
                (scan_status, int(repo_id)),
            )
        conn.commit()
        conn.close()
    except Exception as exc:  # noqa: BLE001
        # Log but don't crash the task — Redis progress is the source of truth for UI
        import structlog

        log = structlog.get_logger()
        log.warning("db_scan_status_update_failed", repo_id=repo_id, error=str(exc))


def _persist_endpoints(repo_id: str, routes: list[Any]) -> int:
    """Persist parsed routes as Endpoint rows in the database."""
    import psycopg2

    sync_url = settings.DATABASE_URL.replace("+asyncpg", "").replace(
        "postgresql+psycopg2", "postgresql"
    )

    saved = 0
    try:
        conn = psycopg2.connect(sync_url)
        with conn.cursor() as cur:
            # Remove stale endpoints for this repo before re-inserting
            cur.execute("DELETE FROM endpoints WHERE repo_id = %s", (int(repo_id),))
            for route in routes:
                cur.execute(
                    """
                    INSERT INTO endpoints
                        (repo_id, method, path, handler_function, file_path,
                         line_number, params_json, response_schema_json, status,
                         created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'pending', NOW(), NOW())
                    """,
                    (
                        int(repo_id),
                        route.method,
                        route.path,
                        route.handler_name,
                        route.file_path,
                        route.line_number,
                        json.dumps(
                            {
                                "path_parameters": route.path_parameters,
                                "query_parameters": route.query_parameters,
                                "request_model": route.request_model,
                                "docstring": route.docstring,
                            }
                        ),
                        json.dumps(route.response_model) if route.response_model else None,
                    ),
                )
                saved += 1
        conn.commit()
        conn.close()
    except Exception as exc:  # noqa: BLE001
        import structlog

        log = structlog.get_logger()
        log.error("endpoint_persist_failed", repo_id=repo_id, error=str(exc))

    return saved

def _run_ai_pipeline_for_repo(repo_id: str, routes: list[Any], tmpdir: str) -> None:
    """Run AI pipeline for each endpoint and update the DB records."""
    import psycopg2
    import structlog
    
    log = structlog.get_logger()
    sync_url = settings.DATABASE_URL.replace("+asyncpg", "").replace("postgresql+psycopg2", "postgresql")
    
    for route in routes:
        try:
            # Read source file for context
            source_code = ""
            source_file = os.path.join(tmpdir, route.file_path)
            if os.path.exists(source_file):
                with open(source_file, encoding="utf-8") as f:
                    source_code = f.read()
            
            result = run_pipeline(route, source_code)
            
            # Update endpoint in DB
            conn = psycopg2.connect(sync_url)
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE endpoints
                    SET generated_doc_json = %s,
                        quality_score = %s,
                        quality_dimensions = %s,
                        attempts = %s,
                        needs_human_review = %s,
                        source_code_snippet = %s,
                        status = %s,
                        updated_at = NOW()
                    WHERE repo_id = %s AND path = %s AND method = %s
                    """,
                    (
                        json.dumps(result.generated_doc.model_dump()) if result.generated_doc else None,
                        result.quality_score,
                        json.dumps(result.quality_dimensions.model_dump()) if result.quality_dimensions else None,
                        result.attempts,
                        result.needs_human_review,
                        source_code[:5000],  # store first 5000 chars
                        "needs_review" if result.needs_human_review else "pending_review",
                        int(repo_id),
                        route.path,
                        route.method,
                    ),
                )
            conn.commit()
            conn.close()
            
            log.info(
                "pipeline_endpoint_processed",
                repo_id=repo_id,
                path=route.path,
                method=route.method,
                verdict=result.final_verdict,
                quality_score=result.quality_score,
            )
        
        except Exception as exc:  # noqa: BLE001
            log.error(
                "pipeline_endpoint_failed",
                repo_id=repo_id,
                path=route.path,
                method=route.method,
                error=str(exc),
            )


@shared_task  # type: ignore[untyped-decorator]
def scan_repo_task(repo_id: str, user_id: str = "anonymous") -> dict[str, Any]:
    """
    Clone the repository URL from the database, run the FastAPI AST parser
    on every Python file, and persist the discovered endpoints.

    Progress steps:
        10  — cloning repo
        30  — walking Python files
        60  — AST parsing complete
        80  — persisting endpoints to DB
        100 — completed
    """
    import structlog
    import time

    log = structlog.get_logger()
    r = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

    start_time = time.time()

    try:
        _update_progress(r, repo_id, "scanning", 10)
        _update_repo_scan_status(repo_id, "scanning")

        # ── Step 1: Fetch repo URL from DB ────────────────────────────────
        import psycopg2

        sync_url = settings.DATABASE_URL.replace("+asyncpg", "").replace(
            "postgresql+psycopg2", "postgresql"
        )
        conn = psycopg2.connect(sync_url)
        with conn.cursor() as cur:
            cur.execute("SELECT url FROM repos WHERE id = %s", (int(repo_id),))
            row = cur.fetchone()
        conn.close()

        if not row:
            log.error("scan_repo_not_found", repo_id=repo_id)
            _update_progress(r, repo_id, "failed", 0)
            _update_repo_scan_status(repo_id, "failed")
            return {"status": "failed", "repo_id": repo_id, "error": "repo not found"}

        repo_url: str = row[0]
        log.info("scan_started", repo_id=repo_id, url=repo_url)

        # ── Step 2: Clone repository into a temp directory ────────────────
        tmpdir = tempfile.mkdtemp(prefix="docforge_scan_")
        try:
            result = subprocess.run(
                ["git", "clone", "--depth", "1", repo_url, tmpdir],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode != 0:
                raise RuntimeError(f"git clone failed: {result.stderr}")

            _update_progress(r, repo_id, "parsing_ast", 30)

            # ── Step 3: Walk and parse all Python files ───────────────────
            parser = FastAPIParser()
            all_routes = []

            for dirpath, _, filenames in os.walk(tmpdir):
                # Skip hidden dirs and common non-source dirs
                dirpath_parts = dirpath.replace(tmpdir, "").split(os.sep)
                if any(p.startswith(".") or p in ("node_modules", "__pycache__", ".venv", "venv", "env", "tests") for p in dirpath_parts):
                    continue

                for filename in filenames:
                    if not filename.endswith(".py"):
                        continue
                    full_path = os.path.join(dirpath, filename)
                    relative_path = os.path.relpath(full_path, tmpdir)
                    routes = parser.parse_file(full_path)
                    # Rewrite file_path to be repo-relative
                    for route in routes:
                        route.file_path = relative_path
                    all_routes.extend(routes)

            log.info("scan_parsing_complete", repo_id=repo_id, endpoints_found=len(all_routes))
            _update_progress(r, repo_id, "enriching_context", 60)

            # ── Step 4: Persist endpoints to DB ──────────────────────────
            _update_progress(r, repo_id, "saving_endpoints", 80)
            saved_count = _persist_endpoints(repo_id, all_routes)

            _update_progress(r, repo_id, "running_ai_pipeline", 85)
            _run_ai_pipeline_for_repo(repo_id, all_routes, tmpdir)

            _update_repo_scan_status(repo_id, "completed")
            _update_progress(r, repo_id, "completed", 100)

        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    except Exception as exc:  # noqa: BLE001
        log.error("scan_task_failed", repo_id=repo_id, error=str(exc))
        _update_progress(r, repo_id, "failed", 0)
        _update_repo_scan_status(repo_id, "failed")
        saved_count = 0

    duration_ms = int((time.time() - start_time) * 1000)

    capture_event(
        user_id,
        "repo_scan_completed",
        {
            "repo_id": repo_id,
            "endpoints_found": saved_count,
            "duration_ms": duration_ms,
        },
    )

    return {"status": "completed", "repo_id": repo_id, "endpoints_saved": saved_count}
