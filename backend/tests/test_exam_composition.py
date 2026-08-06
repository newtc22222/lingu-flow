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


async def _template(client: AsyncClient, headers: dict, name: str = "Composed") -> str:
    res = await client.post(
        "/api/exams/templates",
        json={"name": name, "examType": "custom", "durationMinutes": 20},
        headers=headers,
    )
    return res.json()["id"]


async def _question(
    client: AsyncClient, headers: dict, template_id: str, text: str
) -> str:
    res = await client.post(
        f"/api/exams/templates/{template_id}/questions",
        json={
            "examType": "toeic",
            "part": "part5",
            "questionText": text,
            "options": ["A. one", "B. two", "C. three", "D. four"],
            "correctAnswer": "A",
        },
        headers=headers,
    )
    assert res.status_code == 201
    return res.json()["id"]


async def _composition(client: AsyncClient, headers: dict, template_id: str):
    res = await client.get(
        f"/api/exams/templates/{template_id}/questions", headers=headers
    )
    return res.json()


@pytest.mark.asyncio
async def test_attach_appends_in_order(client: AsyncClient):
    headers = await _register(client, "compattach")
    source = await _template(client, headers, "Source")
    q1 = await _question(client, headers, source, "Q1")
    q2 = await _question(client, headers, source, "Q2")

    target = await _template(client, headers, "Target")
    res = await client.post(
        f"/api/exams/templates/{target}/questions/attach",
        json={"questionIds": [q2, q1]},
        headers=headers,
    )
    assert res.status_code == 200
    assert [q["questionText"] for q in res.json()] == ["Q2", "Q1"]
    assert [q["orderIndex"] for q in res.json()] == [0, 1]


@pytest.mark.asyncio
async def test_attach_is_idempotent(client: AsyncClient):
    """Re-selecting an already-attached question in a multi-select must be a no-op."""
    headers = await _register(client, "compdupe")
    template_id = await _template(client, headers)
    q1 = await _question(client, headers, template_id, "Q1")

    res = await client.post(
        f"/api/exams/templates/{template_id}/questions/attach",
        json={"questionIds": [q1]},
        headers=headers,
    )
    assert res.status_code == 200
    assert len(res.json()) == 1

    template = (
        await client.get(f"/api/exams/templates/{template_id}", headers=headers)
    ).json()
    assert template["totalQuestions"] == 1


@pytest.mark.asyncio
async def test_attach_unknown_question_is_404(client: AsyncClient):
    headers = await _register(client, "compunknown")
    template_id = await _template(client, headers)
    res = await client.post(
        f"/api/exams/templates/{template_id}/questions/attach",
        json={"questionIds": ["00000000-0000-0000-0000-000000000000"]},
        headers=headers,
    )
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_reorder_rewrites_order(client: AsyncClient):
    headers = await _register(client, "comporder")
    template_id = await _template(client, headers)
    q1 = await _question(client, headers, template_id, "Q1")
    q2 = await _question(client, headers, template_id, "Q2")
    q3 = await _question(client, headers, template_id, "Q3")

    res = await client.put(
        f"/api/exams/templates/{template_id}/questions/reorder",
        json={"questionIds": [q3, q1, q2]},
        headers=headers,
    )
    assert res.status_code == 200
    assert [q["questionText"] for q in res.json()] == ["Q3", "Q1", "Q2"]

    assert [q["questionText"] for q in await _composition(client, headers, template_id)] == [
        "Q3",
        "Q1",
        "Q2",
    ]


@pytest.mark.asyncio
async def test_reorder_rejects_partial_list(client: AsyncClient):
    """A partial list would leave the omitted questions at stale indices."""
    headers = await _register(client, "comppartial")
    template_id = await _template(client, headers)
    q1 = await _question(client, headers, template_id, "Q1")
    await _question(client, headers, template_id, "Q2")

    res = await client.put(
        f"/api/exams/templates/{template_id}/questions/reorder",
        json={"questionIds": [q1]},
        headers=headers,
    )
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_detach_leaves_the_question_alive(client: AsyncClient):
    """Detaching removes the link only — the question stays reusable."""
    headers = await _register(client, "compdetach")
    template_id = await _template(client, headers)
    q1 = await _question(client, headers, template_id, "Survivor")

    res = await client.delete(
        f"/api/exams/templates/{template_id}/questions/{q1}", headers=headers
    )
    assert res.status_code == 200
    assert await _composition(client, headers, template_id) == []

    # Still attachable elsewhere, which is only true if the row still exists.
    other = await _template(client, headers, "Other")
    reattached = await client.post(
        f"/api/exams/templates/{other}/questions/attach",
        json={"questionIds": [q1]},
        headers=headers,
    )
    assert reattached.status_code == 200
    assert [q["questionText"] for q in reattached.json()] == ["Survivor"]


@pytest.mark.asyncio
async def test_deleting_a_template_does_not_delete_its_questions(client: AsyncClient):
    """The core #29 guarantee: templates own placements, not questions."""
    headers = await _register(client, "comptemplatedel")
    template_id = await _template(client, headers)
    q1 = await _question(client, headers, template_id, "Outlives its exam")

    assert (
        await client.delete(f"/api/exams/templates/{template_id}", headers=headers)
    ).status_code == 200

    survivor = await _template(client, headers, "New home")
    res = await client.post(
        f"/api/exams/templates/{survivor}/questions/attach",
        json={"questionIds": [q1]},
        headers=headers,
    )
    assert res.status_code == 200
    assert [q["questionText"] for q in res.json()] == ["Outlives its exam"]


@pytest.mark.asyncio
async def test_composition_requires_ownership(client: AsyncClient):
    owner_headers = await _register(client, "compowner")
    template_id = await _template(client, owner_headers)
    q1 = await _question(client, owner_headers, template_id, "Q1")

    intruder = await _register(client, "compintruder")
    assert (
        await client.post(
            f"/api/exams/templates/{template_id}/questions/attach",
            json={"questionIds": [q1]},
            headers=intruder,
        )
    ).status_code == 404
    assert (
        await client.put(
            f"/api/exams/templates/{template_id}/questions/reorder",
            json={"questionIds": [q1]},
            headers=intruder,
        )
    ).status_code == 404
    assert (
        await client.delete(
            f"/api/exams/templates/{template_id}/questions/{q1}", headers=intruder
        )
    ).status_code == 404


@pytest.mark.asyncio
async def test_cannot_compose_a_builtin_public_exam(
    client: AsyncClient, db_session: AsyncSession
):
    """Built-in exams are owned by the seeder; edits would be clobbered."""
    await seed_builtin_exams(db_session)

    headers = await _register(client, "compbuiltin")
    templates = (await client.get("/api/exams/templates", headers=headers)).json()
    public = [t for t in templates if t["isPublic"]]
    assert public, "seeding should have produced public templates"

    scratch = await _template(client, headers, "Scratch")
    q1 = await _question(client, headers, scratch, "Q1")

    res = await client.post(
        f"/api/exams/templates/{public[0]['id']}/questions/attach",
        json={"questionIds": [q1]},
        headers=headers,
    )
    assert res.status_code == 404
