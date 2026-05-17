from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "book_summarizer",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    timezone="America/Sao_Paulo",
)
