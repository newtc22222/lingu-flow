from datetime import datetime, timedelta, timezone
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.card import Card
from app.models.user import User
from app.services.sm2_service import calculate_sm2


def test_sm2_algorithm_math():
    """Test SuperMemo-2 pure calculation logic."""
    # First successful review (Good = 3 -> quality 4)
    res1 = calculate_sm2(interval=0, ease_factor=2.5, repetitions=0, score=3)
    assert res1["interval"] == 1
    assert res1["repetitions"] == 1
    assert res1["ease_factor"] == 2.5

    # Second successful review (Easy = 4 -> quality 5)
    res2 = calculate_sm2(interval=res1["interval"], ease_factor=res1["ease_factor"], repetitions=res1["repetitions"], score=4)
    assert res2["interval"] == 6
    assert res2["repetitions"] == 2
    assert res2["ease_factor"] == 2.6

    # Failed review (Blackout = 1 -> quality 0) resets repetitions & interval
    res3 = calculate_sm2(interval=res2["interval"], ease_factor=res2["ease_factor"], repetitions=res2["repetitions"], score=1)
    assert res3["interval"] == 1
    assert res3["repetitions"] == 0

    # Test ease factor minimum floor (1.3)
    res4 = calculate_sm2(interval=1, ease_factor=1.3, repetitions=0, score=1)
    assert res4["ease_factor"] == 1.3


@pytest.mark.asyncio
async def test_card_crud_operations(client: AsyncClient):
    """Test Card creation, retrieval, updating, and deletion via API."""
    # 1. Register & login to get token
    reg_payload = {
        "username": "carduser",
        "email": "carduser@linguflow.com",
        "password": "Password123!",
    }
    reg_res = await client.post("/api/auth/register", json=reg_payload)
    token = reg_res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create card
    create_payload = {
        "front": "Ephemeral",
        "back": "Lasting for a very short time.",
    }
    create_res = await client.post("/api/cards", json=create_payload, headers=headers)
    assert create_res.status_code == 201
    card_data = create_res.json()
    card_id = card_data["id"]

    assert card_data["front"] == "Ephemeral"
    assert "srsData" in card_data
    assert card_data["srsData"]["repetitions"] == 0

    # 3. Get all cards
    get_res = await client.get("/api/cards", headers=headers)
    assert get_res.status_code == 200
    cards_list = get_res.json()
    assert len(cards_list) == 1
    assert cards_list[0]["id"] == card_id

    # 4. Update card
    update_payload = {
        "front": "Ephemeral (adj.)",
        "back": "Transient, fleeting, lasting a short time.",
    }
    update_res = await client.put(f"/api/cards/{card_id}", json=update_payload, headers=headers)
    assert update_res.status_code == 200
    assert update_res.json()["front"] == "Ephemeral (adj.)"

    # 5. Delete card
    delete_res = await client.delete(f"/api/cards/{card_id}", headers=headers)
    assert delete_res.status_code == 200

    # 6. Verify empty list
    get_res2 = await client.get("/api/cards", headers=headers)
    assert len(get_res2.json()) == 0


@pytest.mark.asyncio
async def test_card_study_and_review(client: AsyncClient, db_session: AsyncSession):
    """Test fetching due study cards and submitting a SM-2 review."""
    # 1. Register user
    reg_res = await client.post(
        "/api/auth/register",
        json={"username": "studyuser", "email": "study@linguflow.com", "password": "Password123!"},
    )
    token = reg_res.json()["token"]
    user_id = reg_res.json()["user"]["id"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Insert a card due for review (srs_next_review in past)
    import uuid
    u_uuid = uuid.UUID(user_id)
    past_due = datetime.now(timezone.utc) - timedelta(hours=2)
    card = Card(
        user_id=u_uuid,
        front="Ubiquitous",
        back="Present, appearing, or found everywhere.",
        srs_next_review=past_due,
    )
    db_session.add(card)
    await db_session.commit()
    await db_session.refresh(card)

    # 3. GET /api/cards/study returns the due card
    study_res = await client.get("/api/cards/study", headers=headers)
    assert study_res.status_code == 200
    due_cards = study_res.json()
    assert len(due_cards) == 1
    assert due_cards[0]["id"] == str(card.id)

    # 4. Submit review score = 3 (Good)
    review_res = await client.post(
        f"/api/cards/review/{card.id}", json={"score": 3}, headers=headers
    )
    assert review_res.status_code == 200
    reviewed_card = review_res.json()
    assert reviewed_card["srsData"]["repetitions"] == 1
    assert reviewed_card["srsData"]["interval"] == 1

    # 5. GET /api/cards/study now returns empty list (no longer due today)
    study_res2 = await client.get("/api/cards/study", headers=headers)
    assert len(study_res2.json()) == 0


@pytest.mark.asyncio
async def test_card_ownership_authorization(client: AsyncClient):
    """Test that users cannot update or delete other users' cards."""
    # User 1
    res1 = await client.post("/api/auth/register", json={"username": "u1", "email": "u1@test.com", "password": "Password123!"})
    t1 = res1.json()["token"]

    # User 2
    res2 = await client.post("/api/auth/register", json={"username": "u2", "email": "u2@test.com", "password": "Password123!"})
    t2 = res2.json()["token"]

    # User 1 creates card
    card_res = await client.post(
        "/api/cards",
        json={"front": "Private Front", "back": "Private Back"},
        headers={"Authorization": f"Bearer {t1}"},
    )
    card_id = card_res.json()["id"]

    # User 2 attempts to update User 1's card -> 404 Not Found
    hack_res = await client.put(
        f"/api/cards/{card_id}",
        json={"front": "Hacked Front", "back": "Hacked Back"},
        headers={"Authorization": f"Bearer {t2}"},
    )
    assert hack_res.status_code == 404

    # User 2 attempts to delete User 1's card -> 404 Not Found
    del_res = await client.delete(
        f"/api/cards/{card_id}", headers={"Authorization": f"Bearer {t2}"}
    )
    assert del_res.status_code == 404
