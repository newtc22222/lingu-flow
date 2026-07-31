# LinguFlow

LinguFlow is a minimalist, keyboard-driven flashcard web app and certification exam simulator utilizing a Spaced Repetition System (SRS) based on the SuperMemo-2 (SM-2) algorithm and automated mock test simulations (TOEIC, IELTS, HSK, JLPT).

## Features

- **Certification Exam Simulator**: Timed mock exams with question banks, countdown timer, keyboard shortcuts (`A`/`B`/`C`/`D`), and detailed answer explanations.
- **Keyboard-Driven Flashcards**: Press `Spacebar` to flip cards, and `1`, `2`, `3`, `4` to grade yourself.
- **Markdown Support**: Full Markdown support for flashcards and reading passages.
- **Spaced Repetition System (SRS)**: Robust SM-2 algorithm to schedule cards optimally.
- **Real-Time Updates**: Server-Sent Events (SSE) for instant progression notifications.
- **Docker-Ready**: Containerized deployment with PostgreSQL and FastAPI.

## Tech Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy 2.0 (Async), Alembic, Pydantic v2
- **Frontend**: Vue.js 3 (Composition API), Vite, TailwindCSS v4
- **Database**: PostgreSQL (via `asyncpg`)

## Quickstart (Docker)

Run the full stack with Docker Compose:

```bash
docker-compose up --build
```

- Frontend UI: `http://localhost:8080`
- FastAPI Backend: `http://localhost:8000`
- API Interactive OpenAPI Docs: `http://localhost:8000/docs`
- PostgreSQL: `localhost:5432`

### Local Development (Without Docker)

**1. Backend (Python):**
```bash
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --port 8000 --reload
```

**2. Frontend (Vue 3):**
```bash
cd frontend
npm install
npm run dev
```
*(Vite automatically proxies `/api` to `http://localhost:8000`).*
