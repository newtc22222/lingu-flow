"""
Authorization matrix for exam templates and exam sessions.

Two separate leaks are pinned down here:

* A private template used to be readable — and sittable — by anyone holding its
  UUID, because only the *list* endpoint filtered on visibility.
* Session details used to return the full answer key regardless of session
  status, so the key was one request away in the middle of a sitting.

Assertions run against the JSON the client actually receives (camelCase), not
the ORM objects, because the redaction happens at serialization time.
"""
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
    assert res.status_code == 201
    return {"Authorization": f"Bearer {res.json()['token']}"}


async def _private_template(client: AsyncClient, headers: dict) -> str:
    res = await client.post(
        "/api/exams/templates",
        json={
            "name": "Private Set",
            "examType": "custom",
            "durationMinutes": 20,
            "isPublic": False,
        },
        headers=headers,
    )
    assert res.status_code == 201
    return res.json()["id"]


async def _add_question(
    client: AsyncClient, headers: dict, template_id: str, text: str = "Q1"
) -> str:
    res = await client.post(
        f"/api/exams/templates/{template_id}/questions",
        json={
            "examType": "custom",
            "questionText": text,
            "options": ["A. one", "B. two", "C. three", "D. four"],
            "correctAnswer": "A",
            "explanation": "A is right because it is.",
        },
        headers=headers,
    )
    assert res.status_code == 201
    return res.json()["id"]


async def _start_session(client: AsyncClient, headers: dict, template_id: str) -> str:
    res = await client.post(
        "/api/exams/sessions",
        json={"examTemplateId": template_id},
        headers=headers,
    )
    assert res.status_code == 201
    return res.json()["id"]


# ─── F-02: template visibility ────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_anonymous_cannot_read_private_template(client: AsyncClient):
    """Case 2: no token, private template — 404, not the template metadata."""
    owner = await _register(client, "vis_owner_anon")
    template_id = await _private_template(client, owner)
    await _add_question(client, owner, template_id)

    assert (await client.get(f"/api/exams/templates/{template_id}")).status_code == 404
    assert (
        await client.get(f"/api/exams/templates/{template_id}/questions")
    ).status_code == 404


@pytest.mark.asyncio
async def test_other_user_cannot_read_private_template(client: AsyncClient):
    """Case 3: authenticated stranger gets 404 on both by-id reads."""
    owner = await _register(client, "vis_owner_b")
    intruder = await _register(client, "vis_intruder_b")
    template_id = await _private_template(client, owner)
    await _add_question(client, owner, template_id)

    res_meta = await client.get(
        f"/api/exams/templates/{template_id}", headers=intruder
    )
    res_questions = await client.get(
        f"/api/exams/templates/{template_id}/questions", headers=intruder
    )
    assert res_meta.status_code == 404
    assert res_questions.status_code == 404

    # 404 over 403: the response must not confirm the id exists.
    assert "not found" in res_meta.json()["detail"].lower()


@pytest.mark.asyncio
async def test_other_user_cannot_start_session_on_private_template(
    client: AsyncClient,
):
    """Case 4: a stranger cannot sit a private exam either."""
    owner = await _register(client, "vis_owner_sit")
    intruder = await _register(client, "vis_intruder_sit")
    template_id = await _private_template(client, owner)
    await _add_question(client, owner, template_id)

    res = await client.post(
        "/api/exams/sessions",
        json={"examTemplateId": template_id},
        headers=intruder,
    )
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_owner_still_reads_and_sits_own_private_template(client: AsyncClient):
    """No regression: the owner keeps full access to their own exam."""
    owner = await _register(client, "vis_owner_self")
    template_id = await _private_template(client, owner)
    question_id = await _add_question(client, owner, template_id)

    meta = await client.get(f"/api/exams/templates/{template_id}", headers=owner)
    assert meta.status_code == 200
    assert meta.json()["name"] == "Private Set"

    questions = await client.get(
        f"/api/exams/templates/{template_id}/questions", headers=owner
    )
    assert questions.status_code == 200
    # The author of a question still sees its key on the composition route.
    assert questions.json()[0]["correctAnswer"] == "A"

    session_id = await _start_session(client, owner, template_id)
    answered = await client.put(
        f"/api/exams/sessions/{session_id}/answer",
        json={"questionId": question_id, "userAnswer": "A"},
        headers=owner,
    )
    assert answered.status_code == 200
    assert (
        await client.put(f"/api/exams/sessions/{session_id}/finish", headers=owner)
    ).status_code == 200


@pytest.mark.asyncio
async def test_public_template_stays_readable_without_answer_keys(
    client: AsyncClient, db_session: AsyncSession
):
    """
    Case 8: built-in exams stay open to everyone, keys still withheld.

    This is the only remaining path by which a non-owner can read a composition
    at all, so it is where the redaction guarantee has to be pinned.
    """
    await seed_builtin_exams(db_session)
    stranger = await _register(client, "vis_stranger_public")

    listed = (await client.get("/api/exams/templates")).json()
    public = next(t for t in listed if t["isPublic"])

    for headers in ({}, stranger):
        meta = await client.get(f"/api/exams/templates/{public['id']}", headers=headers)
        assert meta.status_code == 200

        questions = await client.get(
            f"/api/exams/templates/{public['id']}/questions", headers=headers
        )
        assert questions.status_code == 200
        body = questions.json()
        assert body, "the built-in exam should have questions"
        assert all("correctAnswer" not in q for q in body)
        assert all("explanation" not in q for q in body)


# ─── F-03: session answer-key policy ──────────────────────────────────────────
@pytest.mark.asyncio
async def test_mid_exam_details_withholds_answer_keys(client: AsyncClient):
    """Case 5: the owner of an in-progress session must not get the key."""
    owner = await _register(client, "keys_midexam")
    template_id = await _private_template(client, owner)
    question_id = await _add_question(client, owner, template_id)

    session_id = await _start_session(client, owner, template_id)
    await client.put(
        f"/api/exams/sessions/{session_id}/answer",
        json={"questionId": question_id, "userAnswer": "A"},
        headers=owner,
    )
    res = await client.get(
        f"/api/exams/sessions/{session_id}/details", headers=owner
    )
    assert res.status_code == 200
    body = res.json()
    assert body["session"]["status"] == "in-progress"
    assert body["questions"], "the sitting should expose its questions"
    for question in body["questions"]:
        assert "correctAnswer" not in question
        assert "explanation" not in question
        # The question itself is still renderable — only the key is missing.
        assert len(question["options"]) == 4
    # isCorrect is also key-derived feedback — withhold it mid-exam.
    assert question_id in body["userAnswers"]
    assert "isCorrect" not in body["userAnswers"][question_id]


@pytest.mark.asyncio
async def test_completed_details_reveals_answer_keys_to_owner(client: AsyncClient):
    """Case 6: after finishing, the results page gets keys and explanations."""
    owner = await _register(client, "keys_completed")
    template_id = await _private_template(client, owner)
    question_id = await _add_question(client, owner, template_id)

    session_id = await _start_session(client, owner, template_id)
    await client.put(
        f"/api/exams/sessions/{session_id}/answer",
        json={"questionId": question_id, "userAnswer": "B"},
        headers=owner,
    )
    await client.put(f"/api/exams/sessions/{session_id}/finish", headers=owner)

    body = (
        await client.get(f"/api/exams/sessions/{session_id}/details", headers=owner)
    ).json()
    assert body["session"]["status"] == "completed"
    question = body["questions"][0]
    assert question["correctAnswer"] == "A"
    assert question["explanation"] == "A is right because it is."
    assert body["userAnswers"][question_id]["isCorrect"] is False


@pytest.mark.asyncio
async def test_completed_builtin_details_reveals_answer_keys(
    client: AsyncClient, db_session: AsyncSession
):
    """
    Case 6, built-in flavour: seeded questions are owned by nobody.

    Gating the key on question ownership instead of session status would leave
    the results page for every built-in exam permanently blank.
    """
    await seed_builtin_exams(db_session)
    student = await _register(client, "keys_builtin")

    listed = (await client.get("/api/exams/templates")).json()
    public = next(t for t in listed if t["isPublic"] and t["totalQuestions"] > 0)

    session_id = await _start_session(client, student, public["id"])
    await client.put(f"/api/exams/sessions/{session_id}/finish", headers=student)

    body = (
        await client.get(f"/api/exams/sessions/{session_id}/details", headers=student)
    ).json()
    assert body["questions"]
    assert all(q.get("correctAnswer") for q in body["questions"])


@pytest.mark.asyncio
async def test_other_user_cannot_read_session_details(client: AsyncClient):
    """Case 7: session details are owner-only, 404 for anyone else."""
    owner = await _register(client, "keys_owner")
    intruder = await _register(client, "keys_intruder")
    template_id = await _private_template(client, owner)
    await _add_question(client, owner, template_id)
    session_id = await _start_session(client, owner, template_id)

    assert (
        await client.get(
            f"/api/exams/sessions/{session_id}/details", headers=intruder
        )
    ).status_code == 404
    # Unauthenticated is rejected by the dependency, before any lookup.
    assert (
        await client.get(f"/api/exams/sessions/{session_id}/details")
    ).status_code in (401, 403)


# ─── F-09: the SSE endpoint is gone ───────────────────────────────────────────
@pytest.mark.asyncio
async def test_sse_endpoint_is_unmounted(client: AsyncClient):
    """No route may accept a bearer token in the query string."""
    assert (await client.get("/api/events")).status_code == 404
    assert (await client.get("/api/events?token=whatever")).status_code == 404

    schema = (await client.get("/openapi.json")).json()
    assert not [path for path in schema["paths"] if path.startswith("/api/events")]
