from celery import Celery  # type: ignore
from app.core.config import settings

celery_app = Celery(
    "worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.core.celery_tasks"]
)

celery_app.conf.task_routes = {"app.core.celery_tasks.scan_repo_task": "main-queue"}
