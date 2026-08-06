"""
Regressions guarding the integrity of finished exam sessions.

A shared, mutable question bank makes it possible to change an exam — or a
question — after somebody has already sat it. These tests pin down that doing
so cannot rewrite what their finished session was.
"""
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


async def _template(client: AsyncClient, headers: dict) -> str:
    res = await client.post(
        "/api/exams/templates",
        json={
            "name": "History Test",
            "examType": "custom",
            "durationMinutes": 20,
            "passingScore": 60,
        },
        headers=headers,
    )
    return res.json()["id"]


async def _add_question(
    client: AsyncClient, headers: dict, template_id: str, text: str
) -> str:
    res = await client.post(
        f"/api/exams/templates/{template_id}/questions",
        json={
            "examType": "custom",
            "questionText": text,
            "options": ["A. one", "B. two", "C. three", "D. four"],
            "correctAnswer": "A",
        },
        headers=headers,
    )
    assert res.status_code == 201
    return res.json()["id"]


async def _sit_exam(client: AsyncClient, headers: dict, template_id: str) -> str:
    """Start, answer every question correctly, and finish. Returns session id."""
    session_id = (
        await client.post(
            "/api/exams/sessions",
            json={"examTemplateId": template_id},
            headers=headers,
        )
    ).json()["id"]

    questions = (
        await client.get(
            f"/api/exams/templates/{template_id}/questions", headers=headers
        )
    ).json()
    for q in questions:
        await client.put(
            f"/api/exams/sessions/{session_id}/answer",
            json={"questionId": q["id"], "userAnswer": "A"},
            headers=headers,
        )

    await client.put(f"/api/exams/sessions/{session_id}/finish", headers=headers)
    return session_id


@pytest.mark.asyncio
async def test_editing_exam_does_not_rewrite_finished_session(client: AsyncClient):
    """Attach, detach and reorder after the fact; the session must not move."""
    headers = await _register(client, "histedit")
    template_id = await _template(client, headers)
    first = await _add_question(client, headers, template_id, "Q1")
    second = await _add_question(client, headers, template_id, "Q2")

    session_id = await _sit_exam(client, headers, template_id)

    before = (
        await client.get(f"/api/exams/sessions/{session_id}/details", headers=headers)
    ).json()
    assert [q["questionText"] for q in before["questions"]] == ["Q1", "Q2"]

    # Now mutate the exam in every way the composition endpoints allow.
    third = await _add_question(client, headers, template_id, "Q3")
    await client.delete(
        f"/api/exams/templates/{template_id}/questions/{first}", headers=headers
    )
    await client.put(
        f"/api/exams/templates/{template_id}/questions/reorder",
        json={"questionIds": [third, second]},
        headers=headers,
    )

    after = (
        await client.get(f"/api/exams/sessions/{session_id}/details", headers=headers)
    ).json()
    assert [q["questionText"] for q in after["questions"]] == ["Q1", "Q2"]
    assert after["session"]["correctCount"] == before["session"]["correctCount"]
    assert after["session"]["score"] == before["session"]["score"]


@pytest.mark.asyncio
async def test_deleted_question_still_renders_in_past_results(client: AsyncClient):
    """Deleting a bank question archives it; it must not vanish from history."""
    headers = await _register(client, "histdelete")
    template_id = await _template(client, headers)
    question_id = await _add_question(client, headers, template_id, "Doomed question")

    session_id = await _sit_exam(client, headers, template_id)

    res = await client.delete(f"/api/exams/questions/{question_id}", headers=headers)
    assert res.status_code == 200

    details = (
        await client.get(f"/api/exams/sessions/{session_id}/details", headers=headers)
    ).json()
    assert [q["questionText"] for q in details["questions"]] == ["Doomed question"]
    assert question_id in details["userAnswers"]

    # It is gone from the exam itself, though.
    remaining = (
        await client.get(
            f"/api/exams/templates/{template_id}/questions", headers=headers
        )
    ).json()
    assert remaining == []


@pytest.mark.asyncio
async def test_hard_delete_of_answered_question_is_refused(client: AsyncClient):
    headers = await _register(client, "histhard")
    template_id = await _template(client, headers)
    question_id = await _add_question(client, headers, template_id, "Answered")
    await _sit_exam(client, headers, template_id)

    res = await client.delete(
        f"/api/exams/questions/{question_id}?hard=true", headers=headers
    )
    assert res.status_code == 409


@pytest.mark.asyncio
async def test_answering_a_question_outside_the_session_is_rejected(
    client: AsyncClient,
):
    """
    Regression for a scoring exploit.

    `record_answer` used to create an answer record on demand for any question
    id, while `finish_session` summed all records over `total_count` — so a
    client could answer questions that were never in the exam and push
    correctCount past totalCount.
    """
    headers = await _register(client, "histexploit")
    template_id = await _template(client, headers)
    await _add_question(client, headers, template_id, "In the exam")

    other_template = (
        await client.post(
            "/api/exams/templates",
            json={"name": "Other", "examType": "custom", "durationMinutes": 10},
            headers=headers,
        )
    ).json()["id"]
    outsider = await _add_question(client, headers, other_template, "Not in the exam")

    session_id = (
        await client.post(
            "/api/exams/sessions",
            json={"examTemplateId": template_id},
            headers=headers,
        )
    ).json()["id"]

    res = await client.put(
        f"/api/exams/sessions/{session_id}/answer",
        json={"questionId": outsider, "userAnswer": "A"},
        headers=headers,
    )
    assert res.status_code == 404

    finished = (
        await client.put(f"/api/exams/sessions/{session_id}/finish", headers=headers)
    ).json()
    assert finished["correctCount"] <= finished["totalCount"]


@pytest.mark.asyncio
async def test_answer_key_is_frozen_once_answered(client: AsyncClient):
    """
    Changing options/correctAnswer after an answer exists would desync every
    stored is_correct from the displayed key, so past results would start lying.
    """
    headers = await _register(client, "histfrozen")
    template_id = await _template(client, headers)
    question_id = await _add_question(client, headers, template_id, "Frozen")
    await _sit_exam(client, headers, template_id)

    payload = {
        "examType": "custom",
        "questionText": "Frozen",
        "options": ["A. one", "B. two", "C. three", "D. four"],
        "correctAnswer": "A",
    }

    # Wording, explanation and tags stay editable.
    editable = await client.put(
        f"/api/exams/questions/{question_id}",
        json={**payload, "questionText": "Reworded", "explanation": "why"},
        headers=headers,
    )
    assert editable.status_code == 200

    # The answer key does not.
    rejected = await client.put(
        f"/api/exams/questions/{question_id}",
        json={**payload, "questionText": "Reworded", "correctAnswer": "C"},
        headers=headers,
    )
    assert rejected.status_code == 409
