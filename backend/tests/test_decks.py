import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_deck_crud_operations(client: AsyncClient):
    """Test Deck creation, retrieval, updating, and deletion via API."""
    # 1. Register & login to get token
    reg_payload = {
        "username": "deckuser",
        "email": "deckuser@linguflow.com",
        "password": "Password123!",
    }
    reg_res = await client.post("/api/auth/register", json=reg_payload)
    token = reg_res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create deck
    create_payload = {
        "name": "IELTS Academic Vocabulary",
        "description": "Band 8+ words and phrases",
    }
    create_res = await client.post("/api/decks", json=create_payload, headers=headers)
    assert create_res.status_code == 201
    deck_data = create_res.json()
    deck_id = deck_data["id"]

    assert deck_data["name"] == "IELTS Academic Vocabulary"
    assert deck_data["description"] == "Band 8+ words and phrases"
    assert deck_data["cardCount"] == 0

    # 3. Get all decks
    get_res = await client.get("/api/decks", headers=headers)
    assert get_res.status_code == 200
    decks_list = get_res.json()
    assert len(decks_list) == 1
    assert decks_list[0]["id"] == deck_id

    # 4. Update deck
    update_payload = {
        "name": "IELTS Band 8+ Vocabulary",
        "description": "Updated essential collocations and idioms",
    }
    update_res = await client.put(f"/api/decks/{deck_id}", json=update_payload, headers=headers)
    assert update_res.status_code == 200
    assert update_res.json()["name"] == "IELTS Band 8+ Vocabulary"

    # 5. Delete deck
    delete_res = await client.delete(f"/api/decks/{deck_id}", headers=headers)
    assert delete_res.status_code == 200

    # 6. Verify empty list
    get_res2 = await client.get("/api/decks", headers=headers)
    assert len(get_res2.json()) == 0


@pytest.mark.asyncio
async def test_deck_card_count_aggregation(client: AsyncClient):
    """Test that GET /api/decks correctly aggregates cardCount for attached cards."""
    # 1. Register user
    reg_res = await client.post(
        "/api/auth/register",
        json={"username": "countuser", "email": "count@linguflow.com", "password": "Password123!"},
    )
    token = reg_res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create a deck
    deck_res = await client.post(
        "/api/decks",
        json={"name": "HSK 2 Vocabulary"},
        headers=headers,
    )
    deck_id = deck_res.json()["id"]

    # 3. Add 2 cards attached to this deck
    await client.post(
        "/api/cards",
        json={"front": "苹果", "back": "Apple", "deckId": deck_id},
        headers=headers,
    )
    await client.post(
        "/api/cards",
        json={"front": "牛奶", "back": "Milk", "deckId": deck_id},
        headers=headers,
    )

    # 4. GET /api/decks returns deck with cardCount == 2
    get_res = await client.get("/api/decks", headers=headers)
    assert get_res.status_code == 200
    decks = get_res.json()
    assert len(decks) == 1
    assert decks[0]["id"] == deck_id
    assert decks[0]["cardCount"] == 2


@pytest.mark.asyncio
async def test_deck_ownership_authorization(client: AsyncClient):
    """Test that users cannot update or delete another user's deck."""
    # User 1
    res1 = await client.post("/api/auth/register", json={"username": "d_u1", "email": "d_u1@test.com", "password": "Password123!"})
    t1 = res1.json()["token"]

    # User 2
    res2 = await client.post("/api/auth/register", json={"username": "d_u2", "email": "d_u2@test.com", "password": "Password123!"})
    t2 = res2.json()["token"]

    # User 1 creates deck
    deck_res = await client.post(
        "/api/decks",
        json={"name": "User 1 Deck"},
        headers={"Authorization": f"Bearer {t1}"},
    )
    deck_id = deck_res.json()["id"]

    # User 2 attempts to update User 1's deck -> 404 Not Found
    hack_res = await client.put(
        f"/api/decks/{deck_id}",
        json={"name": "Hacked Deck"},
        headers={"Authorization": f"Bearer {t2}"},
    )
    assert hack_res.status_code == 404

    # User 2 attempts to delete User 1's deck -> 404 Not Found
    del_res = await client.delete(
        f"/api/decks/{deck_id}", headers={"Authorization": f"Bearer {t2}"}
    )
    assert del_res.status_code == 404
