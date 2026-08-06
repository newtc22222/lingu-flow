import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.seed.exam_seed import seed_builtin_exams


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


def _payload(**overrides) -> dict:
    payload = {
        "examType": "toeic",
        "part": "part5",
        "questionText": "The report was submitted _____ schedule.",
        "options": ["A. on", "B. at", "C. in", "D. to"],
        "correctAnswer": "A",
        "explanation": "'On schedule' is a fixed phrase.",
        "difficulty": "easy",
        "tags": ["prepositions", "collocation"],
    }
    payload.update(overrides)
    return payload


async def _create(client: AsyncClient, headers: dict, **overrides) -> dict:
    res = await client.post("/api/questions", json=_payload(**overrides), headers=headers)
    assert res.status_code == 201, res.text
    return res.json()


@pytest.mark.asyncio
async def test_create_and_list(client: AsyncClient):
    headers = await _register(client, "bankcreate")
    created = await _create(client, headers)

    assert created["examType"] == "toeic"
    assert created["part"] == "part5"
    assert created["isOwned"] is True
    # A bank question belongs to no exam.
    assert "examTemplateId" not in created
    assert "orderIndex" not in created

    listed = (await client.get("/api/questions", headers=headers)).json()
    assert [q["id"] for q in listed] == [created["id"]]


@pytest.mark.asyncio
async def test_part_is_normalized(client: AsyncClient):
    """'Part 5', 'PART5' and 'part5' must not fragment the filter chips."""
    headers = await _register(client, "banknorm")
    created = await _create(client, headers, part="Part 5")
    assert created["part"] == "part5"


@pytest.mark.asyncio
async def test_options_are_prefix_normalized(client: AsyncClient):
    """Bare options get their positional letter, so they render consistently."""
    headers = await _register(client, "bankopts")
    created = await _create(
        client, headers, options=["on", "at", "in", "to"]
    )
    assert created["options"] == ["A. on", "B. at", "C. in", "D. to"]


@pytest.mark.asyncio
async def test_filters(client: AsyncClient):
    headers = await _register(client, "bankfilter")
    await _create(client, headers, part="part5", difficulty="easy", tags=["grammar"])
    await _create(
        client,
        headers,
        examType="ielts",
        part="reading",
        difficulty="hard",
        tags=["inference"],
    )

    by_type = (await client.get("/api/questions?examType=ielts", headers=headers)).json()
    assert len(by_type) == 1 and by_type[0]["examType"] == "ielts"

    by_part = (await client.get("/api/questions?part=part5", headers=headers)).json()
    assert len(by_part) == 1 and by_part[0]["part"] == "part5"

    by_difficulty = (
        await client.get("/api/questions?difficulty=hard", headers=headers)
    ).json()
    assert len(by_difficulty) == 1

    by_tag = (await client.get("/api/questions?tags=grammar", headers=headers)).json()
    assert len(by_tag) == 1 and "grammar" in by_tag[0]["tags"]

    by_search = (
        await client.get("/api/questions?search=submitted", headers=headers)
    ).json()
    assert len(by_search) == 2


@pytest.mark.asyncio
async def test_pagination(client: AsyncClient):
    headers = await _register(client, "bankpage")
    for i in range(5):
        await _create(client, headers, questionText=f"Question {i}")

    page = (await client.get("/api/questions?limit=2&offset=0", headers=headers)).json()
    assert len(page) == 2
    rest = (await client.get("/api/questions?limit=10&offset=4", headers=headers)).json()
    assert len(rest) == 1


@pytest.mark.asyncio
async def test_update(client: AsyncClient):
    headers = await _register(client, "bankupdate")
    created = await _create(client, headers)

    res = await client.put(
        f"/api/questions/{created['id']}",
        json=_payload(questionText="Reworded", difficulty="hard"),
        headers=headers,
    )
    assert res.status_code == 200
    assert res.json()["questionText"] == "Reworded"
    assert res.json()["difficulty"] == "hard"


@pytest.mark.asyncio
async def test_soft_delete_removes_from_listing(client: AsyncClient):
    headers = await _register(client, "bankdelete")
    created = await _create(client, headers)

    assert (
        await client.delete(f"/api/questions/{created['id']}", headers=headers)
    ).status_code == 200

    assert (await client.get("/api/questions", headers=headers)).json() == []
    # Archived, so no longer individually retrievable either.
    assert (
        await client.get(f"/api/questions/{created['id']}", headers=headers)
    ).status_code == 404


@pytest.mark.asyncio
async def test_tags_and_parts_facets(client: AsyncClient):
    headers = await _register(client, "bankfacets")
    await _create(client, headers, part="part5", tags=["grammar", "prepositions"])
    await _create(client, headers, part="part6", tags=["grammar", "text-cohesion"])

    tags = (await client.get("/api/questions/tags?examType=toeic", headers=headers)).json()
    assert tags == ["grammar", "prepositions", "text-cohesion"]

    parts = (await client.get("/api/questions/parts?examType=toeic", headers=headers)).json()
    assert parts == ["part5", "part6"]


@pytest.mark.asyncio
async def test_facet_routes_are_not_parsed_as_ids(client: AsyncClient):
    """
    Regression: /tags and /parts must be declared before /{question_id},
    otherwise FastAPI tries to parse "tags" as a UUID and returns 422.
    """
    headers = await _register(client, "bankrouting")
    for path in ("/api/questions/tags", "/api/questions/parts"):
        res = await client.get(path, headers=headers)
        assert res.status_code == 200, f"{path} -> {res.status_code}"
        assert isinstance(res.json(), list)


@pytest.mark.asyncio
async def test_non_owner_cannot_edit_or_delete(client: AsyncClient):
    owner = await _register(client, "bankowner")
    created = await _create(client, owner)

    intruder = await _register(client, "bankintruder")
    assert (
        await client.put(
            f"/api/questions/{created['id']}", json=_payload(), headers=intruder
        )
    ).status_code == 404
    assert (
        await client.delete(f"/api/questions/{created['id']}", headers=intruder)
    ).status_code == 404

    # And the UI is told so up front, rather than finding out via a 404.
    listed = (await client.get("/api/questions", headers=intruder)).json()
    assert listed[0]["isOwned"] is False


@pytest.mark.asyncio
async def test_seeded_questions_are_not_owned(
    client: AsyncClient, db_session: AsyncSession
):
    """Built-in content has user_id NULL, so nobody may edit it."""
    await seed_builtin_exams(db_session)
    headers = await _register(client, "bankseeded")

    listed = (await client.get("/api/questions?examType=toeic", headers=headers)).json()
    assert listed, "seeding should have produced TOEIC questions"
    assert all(q["isOwned"] is False for q in listed)

    res = await client.put(
        f"/api/questions/{listed[0]['id']}", json=_payload(), headers=headers
    )
    assert res.status_code == 404
