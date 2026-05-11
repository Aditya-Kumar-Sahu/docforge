import asyncio
import os
import json
from celery import Celery # type: ignore
from app.core.config import settings
from app.core.database import async_session_factory
from app.models.models import Repository, Endpoint
from app.core.parser import FastAPIParser
from app.core.chains import process_endpoint_pipeline
from sqlalchemy.future import select
from typing import Any, List
import structlog

logger = structlog.get_logger()

celery_app = Celery(
    "worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

async def _update_scan_status(repo_id: int, status: str):
    async with async_session_factory() as session:
        query = select(Repository).where(Repository.id == repo_id)
        result = await session.execute(query)
        repo = result.scalars().first()
        if repo:
            repo.scan_status = status
            if status == "completed":
                from datetime import datetime
                repo.last_scan_at = datetime.now()
            await session.commit()

async def _save_endpoints(repo_id: int, routes: list[dict[str, Any]]) -> List[int]:
    endpoint_ids = []
    async with async_session_factory() as session:
        for route in routes:
            new_endpoint = Endpoint(
                repo_id=repo_id,
                path=route["path"],
                method=route["method"],
                status="pending",
                summary=route["handler_name"],
                raw_ast_data=route
            )
            session.add(new_endpoint)
            await session.flush()
            endpoint_ids.append(new_endpoint.id)
        await session.commit()
    return endpoint_ids

@celery_app.task(name="process_endpoint_ai") # type: ignore
def process_endpoint_ai(endpoint_id: int):
    """
    Background task to run AI documentation pipeline for a single endpoint.
    """
    async def _run():
        async with async_session_factory() as session:
            query = select(Endpoint).where(Endpoint.id == endpoint_id)
            result = await session.execute(query)
            endpoint = result.scalars().first()
            if not endpoint:
                return

            endpoint.status = "processing"
            await session.commit()

            try:
                # Run the AI pipeline
                res = await process_endpoint_pipeline(endpoint.raw_ast_data)
                
                if res["status"] == "success":
                    endpoint.summary = res["documentation"].get("title", endpoint.summary)
                    endpoint.description = res["documentation"].get("description", "")
                    endpoint.doc_data = res["documentation"]
                    endpoint.quality_score = res["gate"].get("mean_score", 0.0)
                    endpoint.status = "approved" if res["gate"].get("verdict") == "approve" else "needs_review"
                else:
                    endpoint.status = "failed"
                
                await session.commit()
                logger.info("ai_process_complete", endpoint_id=endpoint_id, status=endpoint.status)
            except Exception as e:
                logger.error("ai_process_failed", endpoint_id=endpoint_id, error=str(e))
                endpoint.status = "failed"
                await session.commit()

    asyncio.run(_run())

@celery_app.task(name="scan_repo") # type: ignore
def scan_repo(repo_id: int, local_path: str = None) -> dict[str, Any]:
    logger.info("scan_repo_started", repo_id=repo_id)
    
    try:
        if not local_path:
            local_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        parser = FastAPIParser()
        all_routes = []
        
        for root, _, files in os.walk(local_path):
            if any(ignore in root for ignore in [".venv", "__pycache__", ".git"]):
                continue
                
            for file in files:
                if file.endswith(".py"):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, local_path)
                    try:
                        with open(full_path, "r", encoding="utf-8") as f:
                            content = f.read()
                            routes = parser.parse_file(rel_path, content)
                            all_routes.extend(routes)
                    except Exception as e:
                        logger.error("file_scan_failed", file_path=full_path, error=str(e))

        # Save endpoints and get IDs
        endpoint_ids = asyncio.run(_save_endpoints(repo_id, all_routes))
        
        # Trigger AI processing for each endpoint
        for eid in endpoint_ids:
            process_endpoint_ai.delay(eid)

        asyncio.run(_update_scan_status(repo_id, "completed"))
        
        logger.info("scan_repo_completed", repo_id=repo_id, routes_found=len(all_routes))
        return {"status": "completed", "repo_id": repo_id, "routes_found": len(all_routes)}
        
    except Exception as e:
        logger.error("scan_repo_failed", repo_id=repo_id, error=str(e))
        asyncio.run(_update_scan_status(repo_id, "failed"))
        return {"status": "failed", "repo_id": repo_id, "error": str(e)}
