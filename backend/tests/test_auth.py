import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)
from app.models import User, Deck, Card


def test_password_hashing():
    """Test password hashing and verification utilities."""
    password = "MySecurePassword123!"
    hashed = get_password_hash(password)

    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword", hashed) is False
    assert verify_password(password, "") is False


def test_jwt_token_operations():
    """Test JWT access token creation and decoding."""
    user_id = "123e4567-e89b-12d3-a456-426614174000"
    token = create_access_token(user_id)

    assert isinstance(token, str)
    payload = decode_access_token(token)
    assert payload is not None
    assert payload.get("userId") == user_id
    assert payload.get("sub") == user_id


@pytest.mark.asyncio
async def test_register_new_user(client: AsyncClient):
    """Test POST /api/auth/register creates a new user."""
    payload = {
        "username": "newstudent",
        "email": "newstudent@linguflow.com",
        "password": "Password123!",
    }
    response = await client.post("/api/auth/register", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert "token" in data
    assert data["user"]["username"] == "newstudent"
    assert data["user"]["email"] == "newstudent@linguflow.com"
    assert data["user"]["isGuest"] is False


@pytest.mark.asyncio
async def test_register_duplicate_user(client: AsyncClient):
    """Test POST /api/auth/register returns 409 Conflict for duplicate email/username."""
    payload = {
        "username": "duplicatestudent",
        "email": "duplicate@linguflow.com",
        "password": "Password123!",
    }
    res1 = await client.post("/api/auth/register", json=payload)
    assert res1.status_code == 201

    # Second attempt with same email
    res2 = await client.post("/api/auth/register", json=payload)
    assert res2.status_code == 409


@pytest.mark.asyncio
async def test_login_user(client: AsyncClient):
    """Test POST /api/auth/login authenticates registered user."""
    reg_payload = {
        "username": "loginuser",
        "email": "loginuser@linguflow.com",
        "password": "SecretPassword123",
    }
    await client.post("/api/auth/register", json=reg_payload)

    # Valid login
    login_res = await client.post(
        "/api/auth/login",
        json={"email": "loginuser@linguflow.com", "password": "SecretPassword123"},
    )
    assert login_res.status_code == 200
    assert "token" in login_res.json()

    # Invalid password login
    bad_res = await client.post(
        "/api/auth/login",
        json={"email": "loginuser@linguflow.com", "password": "WrongPassword"},
    )
    assert bad_res.status_code == 401


@pytest.mark.asyncio
async def test_guest_login_and_migration(client: AsyncClient, db_session: AsyncSession):
    """Test guest login, creating data as guest, and migrating to a registered account."""
    # 1. Create guest user
    guest_res = await client.post("/api/auth/guest")
    assert guest_res.status_code == 201
    guest_data = guest_res.json()
    guest_token = guest_data["token"]
    guest_id = guest_data["user"]["id"]
    assert guest_data["user"]["isGuest"] is True

    # 2. Add Deck & Card for guest user in database
    import uuid
    g_uuid = uuid.UUID(guest_id)
    deck = Deck(user_id=g_uuid, name="Guest Deck")
    db_session.add(deck)
    await db_session.commit()

    card = Card(user_id=g_uuid, deck_id=deck.id, front="Hello", back="World")
    db_session.add(card)
    await db_session.commit()

    # 3. Register converting guest account via guestToken
    reg_payload = {
        "username": "converted_guest",
        "email": "converted@linguflow.com",
        "password": "Password123!",
        "guestToken": guest_token,
    }
    reg_res = await client.post("/api/auth/register", json=reg_payload)
    assert reg_res.status_code == 201
    reg_data = reg_res.json()

    # The migrated user ID must match the original guest ID
    assert reg_data["user"]["id"] == guest_id
    assert reg_data["user"]["isGuest"] is False
    assert reg_data["user"]["username"] == "converted_guest"

    # Verify deck and card now belong to the converted user
    card_check = (await db_session.execute(select(Card).where(Card.id == card.id))).scalar_one()
    assert str(card_check.user_id) == guest_id


@pytest.mark.asyncio
async def test_forgot_password(client: AsyncClient):
    """Test POST /api/auth/forgot-password endpoint."""
    response = await client.post(
        "/api/auth/forgot-password", json={"email": "anyone@example.com"}
    )
    assert response.status_code == 200
    assert "message" in response.json()


@pytest.mark.asyncio
async def test_get_current_user_profile(client: AsyncClient):
    """Test GET /api/auth/me protected endpoint."""
    # Unauthenticated request
    unauth_res = await client.get("/api/auth/me")
    assert unauth_res.status_code == 401

    # Register user to get token
    reg_payload = {
        "username": "profileuser",
        "email": "profile@linguflow.com",
        "password": "Password123!",
    }
    reg_res = await client.post("/api/auth/register", json=reg_payload)
    token = reg_res.json()["token"]

    # Authenticated request
    auth_res = await client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert auth_res.status_code == 200
    assert auth_res.json()["username"] == "profileuser"
