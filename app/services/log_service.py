import glob
import json
import os

from app.schemas.jobs import (
    CodeBlockEntry,
    IterationEntry,
    JobLogsResponse,
    LogMetadata,
    RLMCallEntry,
)

LOG_BASE_DIR = "./logs"


def read_job_logs(job_id: str) -> JobLogsResponse:
    log_dir = os.path.join(LOG_BASE_DIR, job_id)

    if not os.path.isdir(log_dir):
        return JobLogsResponse(job_id=job_id, status="empty")

    jsonl_files = sorted(glob.glob(os.path.join(log_dir, "*.jsonl")))

    if not jsonl_files:
        return JobLogsResponse(job_id=job_id, status="pending")

    metadata = None
    iterations: list[IterationEntry] = []
    parse_errors = 0

    for filepath in jsonl_files:
        with open(filepath, "r", encoding="utf-8") as fh:
            for raw_line in fh:
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    parse_errors += 1
                    continue

                entry_type = entry.get("type")

                if entry_type == "metadata" and metadata is None:
                    metadata = LogMetadata(
                        root_model=entry.get("root_model"),
                        max_depth=entry.get("max_depth"),
                        max_iterations=entry.get("max_iterations"),
                        backend=entry.get("backend"),
                        environment_type=entry.get("environment_type"),
                        timestamp=entry.get("timestamp"),
                    )

                elif entry_type == "iteration":
                    code_blocks = []
                    for cb in entry.get("code_blocks", []):
                        result = cb.get("result", {})
                        rlm_calls = [
                            RLMCallEntry(
                                root_model=c.get("root_model", ""),
                                prompt=c.get("prompt", ""),
                                response=c.get("response", ""),
                                execution_time=c.get("execution_time", 0.0),
                            )
                            for c in result.get("rlm_calls", [])
                        ]
                        code_blocks.append(CodeBlockEntry(
                            code=cb.get("code", ""),
                            stdout=result.get("stdout"),
                            stderr=result.get("stderr"),
                            execution_time=result.get("execution_time"),
                            rlm_calls=rlm_calls,
                        ))

                    iterations.append(IterationEntry(
                        iteration=entry.get("iteration", 0),
                        timestamp=entry.get("timestamp", ""),
                        prompt=entry.get("prompt", []),
                        response=entry.get("response", ""),
                        code_blocks=code_blocks,
                        iteration_time=entry.get("iteration_time"),
                        final_answer=entry.get("final_answer"),
                    ))

    iterations.sort(key=lambda x: x.iteration)

    return JobLogsResponse(
        job_id=job_id,
        status="ok",
        metadata=metadata,
        iterations=iterations,
        total_iterations=len(iterations),
        parse_errors=parse_errors,
    )
