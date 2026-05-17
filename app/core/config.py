from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Mistral
    mistral_api_key: str
    mistral_model: str = "mistral/mistral-small-latest"
    mistral_rpm: int = 4

    # Redis
    redis_url: str = "redis://redis:6379/0"
    job_ttl_seconds: int = 86400  # 24h

    # MinIO
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "summaries"
    minio_secure: bool = False
    presigned_url_expiry: int = 3600  # 1h em segundos

    class Config:
        env_file = ".env"


settings = Settings()
