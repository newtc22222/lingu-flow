# 🧠 LinguFlow

LinguFlow is a modern, high-performance, keyboard-driven flashcard web app and certification exam simulator utilizing a Spaced Repetition System (SRS) based on the SuperMemo-2 (SM-2) algorithm and automated mock test simulations for TOEIC, IELTS, HSK, and JLPT.

---

## 📚 Technical Wiki & Documentation

Detailed architecture, database models, API specs, and algorithms are documented in the **[LinguFlow Technical Wiki](docs/wiki/Home.md)**:

- 🏠 **[Wiki Home Page](docs/wiki/Home.md)** — Project overview, technology stack, and architecture sitemap.
- 🏗️ **[Architecture & Database Schema](docs/wiki/Architecture-and-Database-Schema.md)** — ER diagram, 7 PostgreSQL models, Alembic migrations.
- 📡 **[API Documentation](docs/wiki/API-Documentation.md)** — OpenAPI endpoints, Pydantic schemas, and auth contracts.
- 🧠 **[Spaced Repetition (SM-2)](docs/wiki/Spaced-Repetition-SM2.md)** — Mathematical formulation, score mapping (1-4 -> 0-5), and Python implementation.
- 🚢 **[Deployment & DevOps Guide](docs/wiki/Deployment-Guide.md)** — Deployment guides for Vercel, Railway, Cloudflare R2, and Docker Compose.

---

## ✨ Features

- **Certification Exam Simulator**: Timed mock exams with question banks, countdown timer, keyboard shortcuts (`A`/`B`/`C`/`D`), and detailed answer explanations.
- **Keyboard-Driven Flashcards**: Press `Spacebar` to flip cards, and `1`, `2`, `3`, `4` to grade retention score.
- **Spaced Repetition System (SRS)**: Robust SM-2 algorithm to schedule cards optimally.
- **In-Place Guest Account Migration**: Guest users can convert to permanent accounts at any time without losing any deck or card data.
- **33 Built-in Practice Questions**: Pre-seeded exams for TOEIC Part 5, IELTS Academic Reading, HSK Level 2, and JLPT N5.
- **Real-Time Updates**: Server-Sent Events (SSE) stream for real-time progress events.
- **Presigned Cloudflare R2 Uploads**: Secure media file storage using S3 presigned PUT/GET URLs.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.12, FastAPI, Async SQLAlchemy 2.0, Alembic, Pydantic v2, `asyncpg`
- **Frontend**: Vue.js 3 (Composition API), Vite, TypeScript, Pinia, Arcade Pixel CSS Design System
- **Database**: PostgreSQL 16
- **Storage**: Cloudflare R2 (S3 API)

---

## 🚀 Quickstart (Docker)

Run the full stack with Docker Compose:

```bash
docker-compose up --build
```

- Frontend UI: `http://localhost:8080`
- FastAPI Backend: `http://localhost:8000`
- Interactive OpenAPI Docs: `http://localhost:8000/docs`
- PostgreSQL: `localhost:5432`

---

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
