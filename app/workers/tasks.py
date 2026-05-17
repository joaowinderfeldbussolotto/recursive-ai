import json
from datetime import datetime, timezone

from app.workers.celery_app import celery_app
from app.services.pdf_service import extract_text
from app.services.summarizer import summarize
from app.services.storage_service import upload_markdown, ensure_bucket
from app.core.config import settings
import redis

redis_client = redis.from_url(settings.redis_url)


def _update_job(job_id: str, data: dict):
    key = f"job:{job_id}"
    current = json.loads(redis_client.get(key) or "{}")
    current.update(data)
    redis_client.setex(key, settings.job_ttl_seconds, json.dumps(current))


@celery_app.task(bind=True, max_retries=2, default_retry_delay=60)
def summarize_book(self, job_id: str, pdf_bytes_hex: str):
    try:
        _update_job(job_id, {"status": "PROCESSING"})
        pdf_bytes = bytes.fromhex(pdf_bytes_hex)
        book_text = extract_text(pdf_bytes)
        ensure_bucket()
        markdown, chapters = summarize(book_text)
        object_key = upload_markdown(job_id, markdown)
        _update_job(job_id, {
            "status": "DONE",
            "object_key": object_key,
            "chapters_processed": chapters,
            "completed_at": datetime.now(timezone.utc).isoformat(),
        })
    except Exception as exc:
        _update_job(job_id, {
            "status": "FAILED",
            "error": str(exc),
            "completed_at": datetime.now(timezone.utc).isoformat(),
        })
        raise self.retry(exc=exc)
