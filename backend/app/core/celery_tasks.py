from typing import Any
from celery import shared_task # type: ignore
import time
import json
import redis
from app.core.config import settings
from app.core.analytics import capture_event

@shared_task # type: ignore
def scan_repo_task(repo_id: str) -> dict[str, Any]:
    r = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
    
    def update_progress(status: str, progress: int) -> None:
        r.set(f"scan_status:{repo_id}", json.dumps({"status": status, "progress": progress}))

    start_time = time.time()
    
    update_progress("scanning", 10)
    time.sleep(1)
    
    update_progress("parsing_ast", 30)
    time.sleep(2)
    
    update_progress("enriching_context", 60)
    time.sleep(2)
    
    update_progress("generating_docs", 80)
    time.sleep(2)
    
    update_progress("completed", 100)
    
    duration_ms = int((time.time() - start_time) * 1000)
    
    # Instrumentation
    capture_event(
        "anonymous", # TODO: Pass user_id to task
        "repo_scan_completed",
        {
            "repo_id": repo_id,
            "endpoints_found": 12, # Mock data for now
            "duration_ms": duration_ms
        }
    )
    
    return {"status": "completed", "repo_id": repo_id}
