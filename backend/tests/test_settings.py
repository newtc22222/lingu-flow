"""Tests for the GET/PUT /api/settings endpoints."""
import pytest
from httpx import AsyncClient


async def _register(client: AsyncClient, name: str) -> dict:
    res = await client.post(
        "/api/auth/register",
        json={
            "username": name,
            "email": f"{name}@linguflow.com",
            "password": "Password123!",
        },
    )
    return {"Authorization": f"Bearer {res.json()['token']}"}


@pytest.mark.asyncio
async def test_get_settings_returns_defaults(client: AsyncClient):
    """GET /api/settings returns defaults when no row exists."""
    headers = await _register(client, "settings_default")
    res = await client.get("/api/settings", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["locale"] == "vi"
    assert data["crtEnabled"] is True
    assert data["dailyXpGoal"] == 50
    assert data["audioSfxEnabled"] is False
    assert data["notificationsEnabled"] is False


@pytest.mark.asyncio
async def test_put_settings_creates_and_returns(client: AsyncClient):
    """PUT /api/settings upserts a settings row and returns persisted values."""
    headers = await _register(client, "settings_put")
    payload = {"locale": "en", "crtEnabled": False, "dailyXpGoal": 100}
    res = await client.put("/api/settings", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["locale"] == "en"
    assert data["crtEnabled"] is False
    assert data["dailyXpGoal"] == 100
    # Feature-flagged fields stay at defaults.
    assert data["audioSfxEnabled"] is False
    assert data["notificationsEnabled"] is False


@pytest.mark.asyncio
async def test_put_settings_partial_update(client: AsyncClient):
    """PUT /api/settings with partial payload only updates sent fields."""
    headers = await _register(client, "settings_partial")
    # Seed initial settings.
    await client.put(
        "/api/settings",
        json={"locale": "en", "crtEnabled": False, "dailyXpGoal": 100},
        headers=headers,
    )

    # Partial update — only change dailyXpGoal.
    res = await client.put(
        "/api/settings",
        json={"dailyXpGoal": 75},
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["locale"] == "en"  # unchanged
    assert data["crtEnabled"] is False  # unchanged
    assert data["dailyXpGoal"] == 75  # updated


@pytest.mark.asyncio
async def test_get_settings_after_put(client: AsyncClient):
    """GET /api/settings returns previously saved values after a PUT."""
    headers = await _register(client, "settings_getafter")
    await client.put(
        "/api/settings",
        json={"locale": "en", "dailyXpGoal": 200},
        headers=headers,
    )

    res = await client.get("/api/settings", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["locale"] == "en"
    assert data["dailyXpGoal"] == 200


@pytest.mark.asyncio
async def test_settings_requires_auth(client: AsyncClient):
    """Settings endpoints reject unauthenticated requests."""
    get_res = await client.get("/api/settings")
    assert get_res.status_code in (401, 403)

    put_res = await client.put("/api/settings", json={"locale": "en"})
    assert put_res.status_code in (401, 403)
