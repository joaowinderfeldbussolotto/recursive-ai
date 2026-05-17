import boto3
from botocore.client import Config
from app.core.config import settings


def _client():
    return boto3.client(
        "s3",
        endpoint_url=f"http://{settings.minio_endpoint}",
        aws_access_key_id=settings.minio_access_key,
        aws_secret_access_key=settings.minio_secret_key,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )


def ensure_bucket():
    client = _client()
    existing = [b["Name"] for b in client.list_buckets()["Buckets"]]
    if settings.minio_bucket not in existing:
        client.create_bucket(Bucket=settings.minio_bucket)


def upload_markdown(job_id: str, content: str) -> str:
    key = f"{job_id}.md"
    _client().put_object(
        Bucket=settings.minio_bucket,
        Key=key,
        Body=content.encode("utf-8"),
        ContentType="text/markdown",
    )
    return key


def get_presigned_url(object_key: str) -> str:
    return _client().generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.minio_bucket, "Key": object_key},
        ExpiresIn=settings.presigned_url_expiry,
    )
