from typing import Any
from celery import shared_task # type: ignore
import time
from app.core.analytics import capture_event

@shared_task # type: ignore
def scan_repo_task(repo_id: str) -> dict[str, Any]:
    start_time = time.time()
    print(f"Starting scan for repo {repo_id}")
    time.sleep(2)
    print(f"Parsing AST for repo {repo_id}...")
    time.sleep(2)
    print(f"Generating docs using LLM for repo {repo_id}...")
    time.sleep(2)
    print(f"Scan complete for repo {repo_id}")
    
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
