import uuid
import json
from datetime import datetime, timezone

from fastapi import APIRouter, UploadFile, File, HTTPException
import redis

from app.workers.tasks import summarize_book
from app.schemas.jobs import JobCreateResponse
from app.core.config import settings

router = APIRouter()
redis_client = redis.from_url(settings.redis_url)


@router.post("/summarize", response_model=JobCreateResponse)
async def create_summary(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(400, "Apenas arquivos PDF são aceitos")

    pdf_bytes = await file.read()
    job_id = str(uuid.uuid4())
    job_data = {
        "status": "PENDING",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    redis_client.setex(f"job:{job_id}", settings.job_ttl_seconds, json.dumps(job_data))
    summarize_book.delay(job_id, pdf_bytes.hex())
    return JobCreateResponse(job_id=job_id, status="PENDING")
