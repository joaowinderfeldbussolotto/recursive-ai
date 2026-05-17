from pydantic import BaseModel
from typing import Optional, List


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


class RLMCallEntry(BaseModel):
    root_model: str
    prompt: str
    response: str
    execution_time: float


class CodeBlockEntry(BaseModel):
    code: str
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    execution_time: Optional[float] = None
    rlm_calls: List[RLMCallEntry] = []


class IterationEntry(BaseModel):
    iteration: int
    timestamp: str
    prompt: List[dict]
    response: str
    code_blocks: List[CodeBlockEntry] = []
    iteration_time: Optional[float] = None
    final_answer: Optional[str] = None


class LogMetadata(BaseModel):
    root_model: Optional[str] = None
    max_depth: Optional[int] = None
    max_iterations: Optional[int] = None
    backend: Optional[str] = None
    environment_type: Optional[str] = None
    timestamp: Optional[str] = None


class JobLogsResponse(BaseModel):
    job_id: str
    status: str  # "ok" | "pending" | "empty"
    metadata: Optional[LogMetadata] = None
    iterations: List[IterationEntry] = []
    total_iterations: int = 0
    parse_errors: int = 0
