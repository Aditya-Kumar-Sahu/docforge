from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Any
from app.core.analytics import capture_event

router = APIRouter(prefix="/api/repos", tags=["repos"])

REPOS_DB: dict[str, dict[str, Any]] = {}
SCAN_STATUS: dict[str, dict[str, Any]] = {}

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
        
    SCAN_STATUS[id] = {"status": "pending", "progress": 0}
    
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
    if id not in SCAN_STATUS:
        return {"status": "not_started"}
    return SCAN_STATUS[id]
