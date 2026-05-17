import json

from fastapi import APIRouter, HTTPException
import redis

from app.schemas.jobs import JobStatusResponse
from app.services.storage_service import get_presigned_url
from app.core.config import settings

router = APIRouter()
redis_client = redis.from_url(settings.redis_url)


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    raw = redis_client.get(f"job:{job_id}")
    if not raw:
        raise HTTPException(404, "Job não encontrado")

    data = json.loads(raw)
    download_url = None
    if data.get("status") == "DONE" and data.get("object_key"):
        download_url = get_presigned_url(data["object_key"])

    return JobStatusResponse(
        job_id=job_id,
        download_url=download_url,
        **data,
    )
