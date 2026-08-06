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


async def _deck_with_cards(client: AsyncClient, headers: dict, count: int):
    deck_id = (
        await client.post(
            "/api/decks", json={"name": "Deck", "description": ""}, headers=headers
        )
    ).json()["id"]

    card_ids = []
    for i in range(count):
        res = await client.post(
            "/api/cards",
            json={"front": f"front {i}", "back": f"back {i}", "deckId": deck_id},
            headers=headers,
        )
        card_ids.append(res.json()["id"])
    return deck_id, card_ids


@pytest.mark.asyncio
async def test_get_deck_cards_returns_creation_order(client: AsyncClient):
    """New cards are appended, so they come back in the order they were added."""
    headers = await _register(client, "deckcards")
    deck_id, card_ids = await _deck_with_cards(client, headers, 3)

    res = await client.get(f"/api/decks/{deck_id}/cards", headers=headers)
    assert res.status_code == 200

    cards = res.json()
    assert [c["id"] for c in cards] == card_ids
    assert [c["position"] for c in cards] == [0, 1, 2]


@pytest.mark.asyncio
async def test_reorder_deck_cards(client: AsyncClient):
    """A full reorder rewrites position and changes the returned order."""
    headers = await _register(client, "deckreorder")
    deck_id, card_ids = await _deck_with_cards(client, headers, 3)

    reversed_ids = list(reversed(card_ids))
    res = await client.patch(
        f"/api/decks/{deck_id}/cards/reorder",
        json={"cardIds": reversed_ids},
        headers=headers,
    )
    assert res.status_code == 200
    assert [c["id"] for c in res.json()] == reversed_ids

    # And the new order is persisted, not just reflected in the response.
    after = await client.get(f"/api/decks/{deck_id}/cards", headers=headers)
    assert [c["id"] for c in after.json()] == reversed_ids


@pytest.mark.asyncio
async def test_reorder_rejects_partial_id_list(client: AsyncClient):
    """A partial list would strand the omitted cards, so it's a 400."""
    headers = await _register(client, "deckpartial")
    deck_id, card_ids = await _deck_with_cards(client, headers, 3)

    res = await client.patch(
        f"/api/decks/{deck_id}/cards/reorder",
        json={"cardIds": card_ids[:2]},
        headers=headers,
    )
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_reorder_rejects_foreign_card_id(client: AsyncClient):
    """Ids from another deck must not be accepted into this deck's ordering."""
    headers = await _register(client, "deckforeign")
    deck_id, card_ids = await _deck_with_cards(client, headers, 2)
    _, other_ids = await _deck_with_cards(client, headers, 1)

    res = await client.patch(
        f"/api/decks/{deck_id}/cards/reorder",
        json={"cardIds": [card_ids[0], other_ids[0]]},
        headers=headers,
    )
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_card_image_url_and_notes_round_trip(client: AsyncClient):
    """The new optional card fields persist through create and update."""
    headers = await _register(client, "cardfields")
    deck_id = (
        await client.post(
            "/api/decks", json={"name": "D", "description": ""}, headers=headers
        )
    ).json()["id"]

    created = (
        await client.post(
            "/api/cards",
            json={
                "front": "chat",
                "back": "cat",
                "deckId": deck_id,
                "imageUrl": "https://example.com/cat.png",
                "notes": "masculine noun",
            },
            headers=headers,
        )
    ).json()
    assert created["imageUrl"] == "https://example.com/cat.png"
    assert created["notes"] == "masculine noun"

    updated = (
        await client.put(
            f"/api/cards/{created['id']}",
            json={
                "front": "chat",
                "back": "cat",
                "deckId": deck_id,
                "imageUrl": None,
                "notes": "updated note",
            },
            headers=headers,
        )
    ).json()
    assert updated["imageUrl"] is None
    assert updated["notes"] == "updated note"
