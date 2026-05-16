from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from typing import Any, AsyncGenerator, cast
from app.core.analytics import capture_event
from sse_starlette.sse import EventSourceResponse
import json
import asyncio
from redis.asyncio import Redis
from app.core.config import settings

router = APIRouter(prefix="/api/repos", tags=["repos"])

REPOS_DB: dict[str, dict[str, Any]] = {}

async def get_redis() -> Redis:
    return Redis.from_url(settings.REDIS_URL, decode_responses=True)

@router.post("")
async def create_repo(repo_data: dict[str, Any]) -> dict[str, Any]:
    repo_id = str(len(REPOS_DB) + 1)
    REPOS_DB[repo_id] = repo_data
    
    # Instrumentation
    capture_event(
        "anonymous", # TODO: Get from auth context
        "repo_connected",
        {
            "repo_name": repo_data.get("name"),
            "language": repo_data.get("language"),
            "framework": repo_data.get("framework")
        }
    )
    
    return {"id": repo_id, **repo_data}

@router.get("")
async def list_repos() -> list[dict[str, Any]]:
    return list(REPOS_DB.values())

@router.post("/{id}/scan")
async def scan_repo(id: str, background_tasks: BackgroundTasks) -> dict[str, str]:
    if id not in REPOS_DB:
        raise HTTPException(status_code=404, detail="Repo not found")
        
    redis = await get_redis()
    await redis.set(f"scan_status:{id}", json.dumps({"status": "pending", "progress": 0}))
    
    # Instrumentation
    capture_event(
        "anonymous", # TODO: Get from auth context
        "repo_scan_triggered",
        {"repo_id": id, "trigger_type": "manual"}
    )
    
    from app.core.celery_tasks import scan_repo_task
    scan_repo_task.delay(id)
    
    return {"status": "scan initiated"}

@router.get("/{id}/scan-progress")
async def get_scan_progress(id: str) -> dict[str, Any]:
    redis = await get_redis()
    status = await redis.get(f"scan_status:{id}")
    if not status:
        return {"status": "not_started"}
    return cast(dict[str, Any], json.loads(status))

@router.get("/{id}/scan-stream")
async def scan_stream(id: str, request: Request) -> EventSourceResponse:
    if id not in REPOS_DB:
        raise HTTPException(status_code=404, detail="Repo not found")

    async def event_generator() -> AsyncGenerator[dict[str, Any], None]:
        redis = await get_redis()
        last_status = None
        while True:
            # Check if client disconnected
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
