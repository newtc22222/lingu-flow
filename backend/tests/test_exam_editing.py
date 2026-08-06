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


async def _create_template(client: AsyncClient, headers: dict) -> str:
    res = await client.post(
        "/api/exams/templates",
        json={
            "name": "My Practice Set",
            "examType": "custom",
            "description": "draft",
            "durationMinutes": 30,
            "passingScore": 70,
            "level": "N5",
        },
        headers=headers,
    )
    assert res.status_code == 201
    return res.json()["id"]


async def _add_question(client: AsyncClient, headers: dict, template_id: str) -> str:
    res = await client.post(
        f"/api/exams/templates/{template_id}/questions",
        json={
            "examType": "custom",
            "questionText": "The meeting was _____ until Monday.",
            "options": ["A. postponed", "B. arrived", "C. sang", "D. ate"],
            "correctAnswer": "A",
            "explanation": "postpone = delay",
            "difficulty": "medium",
        },
        headers=headers,
    )
    assert res.status_code == 201
    return res.json()["id"]


@pytest.mark.asyncio
async def test_update_template(client: AsyncClient):
    """PUT replaces a custom template's metadata."""
    headers = await _register(client, "examedit")
    template_id = await _create_template(client, headers)

    res = await client.put(
        f"/api/exams/templates/{template_id}",
        json={
            "name": "Renamed Set",
            "examType": "toeic",
            "description": "final",
            "durationMinutes": 45,
            "passingScore": 80,
            "level": "N4",
        },
        headers=headers,
    )
    assert res.status_code == 200

    body = res.json()
    assert body["name"] == "Renamed Set"
    assert body["examType"] == "toeic"
    assert body["durationMinutes"] == 45
    assert body["passingScore"] == 80


@pytest.mark.asyncio
async def test_update_template_rejects_other_users_template(client: AsyncClient):
    """One user must not be able to edit another user's custom exam."""
    owner_headers = await _register(client, "examowner")
    template_id = await _create_template(client, owner_headers)

    intruder_headers = await _register(client, "examintruder")
    res = await client.put(
        f"/api/exams/templates/{template_id}",
        json={
            "name": "Hijacked",
            "examType": "custom",
            "durationMinutes": 10,
            "passingScore": 50,
        },
        headers=intruder_headers,
    )
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_update_question(client: AsyncClient):
    """PUT replaces a question's content in place."""
    headers = await _register(client, "qedit")
    template_id = await _create_template(client, headers)
    question_id = await _add_question(client, headers, template_id)

    res = await client.put(
        f"/api/exams/questions/{question_id}",
        json={
            "examType": "custom",
            "questionText": "She _____ to the store yesterday.",
            "options": ["A. go", "B. went", "C. gone", "D. going"],
            "correctAnswer": "B",
            "explanation": "simple past",
            "difficulty": "easy",
        },
        headers=headers,
    )
    assert res.status_code == 200

    body = res.json()
    assert body["questionText"] == "She _____ to the store yesterday."
    assert body["correctAnswer"] == "B"
    assert body["difficulty"] == "easy"


@pytest.mark.asyncio
async def test_delete_question_decrements_template_count(client: AsyncClient):
    """Removing a question keeps the template's totalQuestions in step."""
    headers = await _register(client, "qdelete")
    template_id = await _create_template(client, headers)
    first_id = await _add_question(client, headers, template_id)
    await _add_question(client, headers, template_id)

    before = (
        await client.get(f"/api/exams/templates/{template_id}", headers=headers)
    ).json()
    assert before["totalQuestions"] == 2

    res = await client.delete(f"/api/exams/questions/{first_id}", headers=headers)
    assert res.status_code == 200

    after = (
        await client.get(f"/api/exams/templates/{template_id}", headers=headers)
    ).json()
    assert after["totalQuestions"] == 1

    remaining = (
        await client.get(
            f"/api/exams/templates/{template_id}/questions", headers=headers
        )
    ).json()
    assert [q["id"] for q in remaining] == [q["id"] for q in remaining if q["id"] != first_id]
    assert len(remaining) == 1


@pytest.mark.asyncio
async def test_delete_question_rejects_other_user(client: AsyncClient):
    """Question deletion is scoped to the owner."""
    owner_headers = await _register(client, "qowner")
    template_id = await _create_template(client, owner_headers)
    question_id = await _add_question(client, owner_headers, template_id)

    intruder_headers = await _register(client, "qintruder")
    res = await client.delete(
        f"/api/exams/questions/{question_id}", headers=intruder_headers
    )
    assert res.status_code == 404
