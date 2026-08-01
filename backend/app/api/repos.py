from fastapi import APIRouter, HTTPException, Request, Depends
from typing import Any, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models import Repo
from app.core.analytics import capture_event
from app.core.celery_tasks import scan_repo_task
from sse_starlette.sse import EventSourceResponse
import json
import asyncio
from redis.asyncio import Redis
from app.core.config import settings
from app.models.schemas import RepoCreate, RepoResponse, ScanResponse, ScanProgressResponse

router = APIRouter(prefix="/api/repos", tags=["repos"])


async def get_redis() -> Redis:  # noqa: F821
    return Redis.from_url(settings.REDIS_URL, decode_responses=True)


def _get_user_id(request: Request) -> str:
    """Extract authenticated user_id from request state (set by CoreMiddleware)."""
    user_id: str | None = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user_id


@router.post("", response_model=RepoResponse)
async def create_repo(
    repo_in: RepoCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> RepoResponse:
    user_id = _get_user_id(request)

    # Extract name from URL
    repo_name = repo_in.url.rstrip("/").split("/")[-1]
    if repo_name.endswith(".git"):
        repo_name = repo_name[:-4]

    new_repo = Repo(
        url=repo_in.url,
        name=repo_name,
        user_id=int(user_id),
        github_repo_id=repo_name,  # Placeholder — will be resolved via GitHub API in Phase 2
        scan_status="pending",
    )
    db.add(new_repo)
    await db.commit()
    await db.refresh(new_repo)

    capture_event(
        user_id,
        "repo_connected",
        {
            "repo_id": new_repo.id,
            "repo_name": repo_name,
            "url": repo_in.url,
        },
    )

    return RepoResponse(id=str(new_repo.id), url=new_repo.url, name=new_repo.name)


@router.get("", response_model=list[RepoResponse])
async def list_repos(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> list[RepoResponse]:
    user_id = _get_user_id(request)
    result = await db.execute(
        select(Repo).where(Repo.user_id == int(user_id), Repo.deleted_at.is_(None))
    )
    repos = result.scalars().all()
    return [RepoResponse(id=str(repo.id), url=repo.url, name=repo.name) for repo in repos]


@router.post("/{id}/scan", response_model=ScanResponse)
async def scan_repo(
    id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ScanResponse:
    user_id = _get_user_id(request)
    repo = await db.get(Repo, int(id))
    if not repo:
        raise HTTPException(status_code=404, detail="Repo not found")
    if repo.user_id != int(user_id):
        raise HTTPException(status_code=403, detail="Access denied")

    redis = await get_redis()
    await redis.set(f"scan_status:{id}", json.dumps({"status": "pending", "progress": 0}))

    capture_event(
        user_id,
        "repo_scan_triggered",
        {"repo_id": id, "trigger_type": "manual"},
    )

    scan_repo_task.delay(id, user_id)

    return ScanResponse(status="scan initiated")


@router.get("/{id}/scan-progress", response_model=ScanProgressResponse)
async def get_scan_progress(id: str) -> ScanProgressResponse:
    redis = await get_redis()
    status_json = await redis.get(f"scan_status:{id}")
    if not status_json:
        return ScanProgressResponse(status="not_started", progress=0)

    status_data = json.loads(status_json)
    return ScanProgressResponse(**status_data)


@router.get("/{id}/scan-stream")
async def scan_stream(
    id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> EventSourceResponse:
    repo = await db.get(Repo, int(id))
    if not repo:
        raise HTTPException(status_code=404, detail="Repo not found")

    async def event_generator() -> AsyncGenerator[dict[str, Any], None]:
        redis = await get_redis()
        last_status = None
        while True:
            if await request.is_disconnected():
                break

            status_json = await redis.get(f"scan_status:{id}")
            if status_json:
                if status_json != last_status:
                    yield {"data": status_json}
                    last_status = status_json

                status_data = json.loads(status_json)
                if status_data.get("status") in ("completed", "failed"):
                    break

            await asyncio.sleep(1)

    return EventSourceResponse(event_generator())
