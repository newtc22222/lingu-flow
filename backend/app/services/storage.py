import aioboto3
from app.config import get_settings

settings = get_settings()


def get_r2_session():
    return aioboto3.Session(
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
    )


async def generate_presigned_upload_url(object_key: str, content_type: str, expires_in: int = 3600) -> str:
    """
    Generate a presigned S3/R2 PUT URL for uploading media files.
    """
    session = get_r2_session()
    endpoint_url = settings.R2_ENDPOINT_URL or (
        f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com" if settings.R2_ACCOUNT_ID else None
    )
    async with session.client("s3", endpoint_url=endpoint_url, region_name="auto") as client:
        return await client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": settings.R2_BUCKET_NAME,
                "Key": object_key,
                "ContentType": content_type,
            },
            ExpiresIn=expires_in,
        )


async def generate_presigned_download_url(object_key: str, expires_in: int = 3600) -> str:
    """
    Generate a presigned S3/R2 GET URL for retrieving private media files.
    """
    session = get_r2_session()
    endpoint_url = settings.R2_ENDPOINT_URL or (
        f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com" if settings.R2_ACCOUNT_ID else None
    )
    async with session.client("s3", endpoint_url=endpoint_url, region_name="auto") as client:
        return await client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": settings.R2_BUCKET_NAME,
                "Key": object_key,
            },
            ExpiresIn=expires_in,
        )
