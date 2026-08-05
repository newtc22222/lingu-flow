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
async def test_progress_requires_auth(client: AsyncClient):
    """The dashboard is per-user, so an anonymous request must be rejected."""
    res = await client.get("/api/dashboard/progress")
    assert res.status_code in (401, 403)


@pytest.mark.asyncio
async def test_progress_empty_account(client: AsyncClient):
    """A brand-new account reports zeroes and no worlds, not an error."""
    headers = await _register(client, "dashempty")

    res = await client.get("/api/dashboard/progress", headers=headers)
    assert res.status_code == 200

    body = res.json()
    assert body["totalXp"] == 0
    assert body["streakDays"] == 0
    assert body["examReadiness"] == 0
    assert body["worlds"] == []


@pytest.mark.asyncio
async def test_progress_builds_world_per_deck(client: AsyncClient):
    """Each non-empty deck becomes a world whose levels chunk its cards by 5."""
    headers = await _register(client, "dashworlds")

    deck_res = await client.post(
        "/api/decks", json={"name": "Kanji N5", "description": ""}, headers=headers
    )
    deck_id = deck_res.json()["id"]

    # 6 cards -> 2 levels (5 + 1)
    for i in range(6):
        await client.post(
            "/api/cards",
            json={"front": f"front {i}", "back": f"back {i}", "deckId": deck_id},
            headers=headers,
        )

    body = (await client.get("/api/dashboard/progress", headers=headers)).json()

    assert len(body["worlds"]) == 1
    world = body["worlds"][0]
    assert world["id"] == deck_id
    assert world["title"] == "Kanji N5"
    assert len(world["levels"]) == 2
    # Nothing reviewed yet: first level is current, the rest locked.
    assert [lv["status"] for lv in world["levels"]] == ["current", "locked"]
    assert world["progressPercent"] == 0
    assert world["subLabel"] == "0/6"


@pytest.mark.asyncio
async def test_progress_counts_reviews_as_xp_and_completion(client: AsyncClient):
    """Reviewing cards advances XP, deck progress, and the level path."""
    headers = await _register(client, "dashreview")

    deck_res = await client.post(
        "/api/decks", json={"name": "Verbs", "description": ""}, headers=headers
    )
    deck_id = deck_res.json()["id"]

    card_ids = []
    for i in range(2):
        res = await client.post(
            "/api/cards",
            json={"front": f"f{i}", "back": f"b{i}", "deckId": deck_id},
            headers=headers,
        )
        card_ids.append(res.json()["id"])

    # Review both cards, so the deck's single level is fully done.
    for card_id in card_ids:
        await client.post(
            f"/api/cards/review/{card_id}", json={"score": 4}, headers=headers
        )

    body = (await client.get("/api/dashboard/progress", headers=headers)).json()
    world = body["worlds"][0]

    assert body["totalXp"] == 20  # 2 repetitions * 10 XP
    assert body["streakDays"] == 1
    assert world["progressPercent"] == 100
    assert world["subLabel"] == "2/2"
    assert [lv["status"] for lv in world["levels"]] == ["done"]


@pytest.mark.asyncio
async def test_progress_skips_empty_decks(client: AsyncClient):
    """A deck with no cards has no levels to show, so it isn't a world."""
    headers = await _register(client, "dashskip")
    await client.post(
        "/api/decks", json={"name": "Empty", "description": ""}, headers=headers
    )

    body = (await client.get("/api/dashboard/progress", headers=headers)).json()
    assert body["worlds"] == []
