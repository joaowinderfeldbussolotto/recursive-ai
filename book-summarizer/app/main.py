from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1 import summarize, jobs


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="Book Summarizer API",
    description="Geração de resumos de livros técnicos via Recursive LM",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(summarize.router, prefix="/api/v1", tags=["summarize"])
app.include_router(jobs.router, prefix="/api/v1", tags=["jobs"])
