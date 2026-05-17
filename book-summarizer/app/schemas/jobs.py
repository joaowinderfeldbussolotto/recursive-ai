from pydantic import BaseModel
from typing import Optional


class JobCreateResponse(BaseModel):
    job_id: str
    status: str  # "PENDING"


class JobStatusResponse(BaseModel):
    job_id: str
    status: str  # PENDING | PROCESSING | DONE | FAILED
    download_url: Optional[str] = None
    chapters_processed: Optional[int] = None
    created_at: str
    completed_at: Optional[str] = None
    error: Optional[str] = None
