from celery import Celery # type: ignore
from app.core.config import settings
from typing import Any

celery_app = Celery(
    "worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.task_routes = {
    "app.worker.test_task": "main-queue",
}

@celery_app.task # type: ignore
def test_task(name: str) -> str:
    return f"Hello {name}!"
