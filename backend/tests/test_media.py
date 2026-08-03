from unittest.mock import AsyncMock, patch
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_presign_upload_endpoint(client: AsyncClient):
    """Test POST /api/media/presign-upload returns a valid upload_url and file_key."""
    mock_url = "https://linguflow-media.r2.cloudflarestorage.com/uploads/card_audio.mp3?mock_sig=123"
    
    with patch("app.routers.media.generate_presigned_upload_url", new=AsyncMock(return_value=mock_url)):
        payload = {
            "filename": "card_audio.mp3",
            "content_type": "audio/mpeg"
        }
        response = await client.post("/api/media/presign-upload", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["upload_url"] == mock_url
        assert data["file_key"] == "uploads/card_audio.mp3"


@pytest.mark.asyncio
async def test_presign_upload_missing_fields(client: AsyncClient):
    """Test POST /api/media/presign-upload returns 400 when missing required parameters."""
    response = await client.post("/api/media/presign-upload", json={"filename": ""})
    assert response.status_code == 422  # Pydantic validation error


@pytest.mark.asyncio
async def test_presign_download_endpoint(client: AsyncClient):
    """Test GET /api/media/presign-download/{file_key} returns a valid download_url."""
    mock_url = "https://linguflow-media.r2.cloudflarestorage.com/uploads/card_audio.mp3?mock_get_sig=456"
    
    with patch("app.routers.media.generate_presigned_download_url", new=AsyncMock(return_value=mock_url)):
        response = await client.get("/api/media/presign-download/uploads/card_audio.mp3")
        assert response.status_code == 200
        data = response.json()
        assert data["download_url"] == mock_url
