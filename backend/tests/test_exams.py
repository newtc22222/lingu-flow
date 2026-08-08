import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_exam_template_crud(client: AsyncClient):
    """Test custom ExamTemplate creation, listing, metadata fetch, and deletion."""
    # 1. Register & login
    reg_res = await client.post(
        "/api/auth/register",
        json={"username": "creator", "email": "creator@test.com", "password": "Password123!"},
    )
    token = reg_res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create template
    t_payload = {
        "name": "TOEIC Grammar Sprint",
        "examType": "toeic",
        "description": "20 rapid-fire grammar questions",
        "durationMinutes": 15,
        "passingScore": 70,
        "level": "Intermediate",
        "isPublic": False,
        "tags": ["toeic", "grammar"],
    }
    create_res = await client.post("/api/exams/templates", json=t_payload, headers=headers)
    assert create_res.status_code == 201
    t_data = create_res.json()
    t_id = t_data["id"]

    assert t_data["name"] == "TOEIC Grammar Sprint"
    assert t_data["examType"] == "toeic"
    assert t_data["_id"] == t_id

    # 3. Get all templates
    list_res = await client.get("/api/exams/templates", headers=headers)
    assert list_res.status_code == 200
    templates = list_res.json()
    assert any(t["id"] == t_id for t in templates)

    # 4. Get template metadata by ID
    get_res = await client.get(f"/api/exams/templates/{t_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "TOEIC Grammar Sprint"

    # 5. Delete template
    del_res = await client.delete(f"/api/exams/templates/{t_id}", headers=headers)
    assert del_res.status_code == 200


@pytest.mark.asyncio
async def test_exam_question_management(client: AsyncClient):
    """Test adding questions to an exam template and fetching question list."""
    reg_res = await client.post(
        "/api/auth/register",
        json={"username": "q_admin", "email": "q_admin@test.com", "password": "Password123!"},
    )
    token = reg_res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create template
    t_res = await client.post(
        "/api/exams/templates",
        json={"name": "HSK 2 Grammar", "examType": "hsk", "durationMinutes": 20},
        headers=headers,
    )
    t_id = t_res.json()["id"]

    # Add question
    q_payload = {
        "examType": "hsk",
        "part": "reading",
        "questionText": "这本 书 _____ 很好看。",
        "type": "multiple-choice",
        "options": ["A. 吧", "B. 呢", "C. 真", "D. 的"],
        "correctAnswer": "C",
        "explanation": "真 (zhēn) means really/truly.",
        "difficulty": "easy",
    }
    q_res = await client.post(
        f"/api/exams/templates/{t_id}/questions", json=q_payload, headers=headers
    )
    assert q_res.status_code == 201
    q_data = q_res.json()
    assert q_data["correctAnswer"] == "C"
    # A question is no longer owned by one template, so it carries bank
    # taxonomy instead of an examTemplateId.
    assert q_data["examType"] == "hsk"
    assert q_data["part"] == "reading"
    assert "examTemplateId" not in q_data

    # Get questions for template (as the owner — a private template is not
    # readable anonymously; see test_exam_visibility.py)
    q_list_res = await client.get(
        f"/api/exams/templates/{t_id}/questions", headers=headers
    )
    assert q_list_res.status_code == 200
    questions = q_list_res.json()
    assert len(questions) == 1
    assert questions[0]["questionText"] == "这本 书 _____ 很好看。"
    # Position comes from the composition, not from the question.
    assert questions[0]["orderIndex"] == 0


@pytest.mark.asyncio
async def test_full_exam_session_flow(client: AsyncClient):
    """Test starting session, recording answers, finishing session, and fetching details map."""
    reg_res = await client.post(
        "/api/auth/register",
        json={"username": "student_test", "email": "student_test@test.com", "password": "Password123!"},
    )
    token = reg_res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create template & question
    t_res = await client.post(
        "/api/exams/templates",
        json={"name": "IELTS Academic Reading Set", "examType": "ielts", "durationMinutes": 30},
        headers=headers,
    )
    t_id = t_res.json()["id"]

    q_res = await client.post(
        f"/api/exams/templates/{t_id}/questions",
        json={
            "examType": "ielts",
            "questionText": "What is the primary conclusion of the passage?",
            "passage": "Sample academic passage about renewable energy...",
            "options": ["A. Option 1", "B. Option 2", "C. Option 3", "D. Option 4"],
            "correctAnswer": "B",
        },
        headers=headers,
    )
    q_id = q_res.json()["id"]

    # 2. Start session
    start_res = await client.post(
        "/api/exams/sessions",
        json={"examTemplateId": t_id},
        headers=headers,
    )
    assert start_res.status_code == 201
    session_data = start_res.json()
    s_id = session_data["id"]
    assert session_data["status"] == "in-progress"

    # 3. Submit answer (correct = B)
    ans_res = await client.put(
        f"/api/exams/sessions/{s_id}/answer",
        json={"questionId": q_id, "userAnswer": "B", "timeTakenSeconds": 14},
        headers=headers,
    )
    assert ans_res.status_code == 200
    assert ans_res.json()["isCorrect"] is True

    # 4. Finish session
    finish_res = await client.put(f"/api/exams/sessions/{s_id}/finish", headers=headers)
    assert finish_res.status_code == 200
    finished_data = finish_res.json()
    assert finished_data["status"] == "completed"
    assert finished_data["score"] == 100.0
    assert finished_data["correctCount"] == 1

    # 5. Fetch session details map for results review page
    details_res = await client.get(f"/api/exams/sessions/{s_id}/details", headers=headers)
    assert details_res.status_code == 200
    details = details_res.json()

    assert details["session"]["id"] == s_id
    assert details["template"]["id"] == t_id
    assert len(details["questions"]) == 1
    assert q_id in details["userAnswers"]
    assert details["userAnswers"][q_id]["userAnswer"] == "B"
    assert details["userAnswers"][q_id]["isCorrect"] is True
