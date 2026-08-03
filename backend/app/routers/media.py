from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.storage import generate_presigned_upload_url, generate_presigned_download_url

router = APIRouter(prefix="/api/media", tags=["Media"])


class PresignUploadRequest(BaseModel):
    filename: str
    content_type: str


@router.post("/presign-upload")
async def get_upload_url(req: PresignUploadRequest):
    """
    Returns a presigned PUT URL for uploading media files directly to Cloudflare R2.
    """
    if not req.filename or not req.content_type:
        raise HTTPException(status_code=400, detail="filename and content_type are required")

    object_key = f"uploads/{req.filename}"
    try:
        url = await generate_presigned_upload_url(object_key, req.content_type)
        return {"upload_url": url, "file_key": object_key}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate presigned upload URL: {str(e)}")


@router.get("/presign-download/{file_key:path}")
async def get_download_url(file_key: str):
    """
    Returns a presigned GET URL for accessing private media files in Cloudflare R2.
    """
    try:
        url = await generate_presigned_download_url(file_key)
        return {"download_url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate presigned download URL: {str(e)}")
