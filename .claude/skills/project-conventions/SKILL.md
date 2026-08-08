---
name: project-conventions
description: Background knowledge of LinguFlow's backend layering, API contract rules, and quality gates. Not user-invocable; Claude should apply it automatically whenever touching backend/app or a frontend component that calls /api/...
user-invocable: false
---

# LinguFlow Project Conventions

## Backend layering (`backend/app/`)

Follow router → service → model → schema strictly:

- **router** (`routers/`): HTTP only — path/method, request validation via schema, calls one service function, returns a schema. No SQLAlchemy queries here.
- **service** (`services/`): business logic, takes `AsyncSession` (via `get_db()` dependency), returns plain Python/ORM objects.
- **model** (`models/`): SQLAlchemy declarative table, inherits `Base` from `database.py`.
- **schema** (`schemas/`): Pydantic I/O shape, one module per resource, separate `*Create`/`*Read`/`*Update` classes where the shapes differ.

Every new router **must** be registered in `backend/app/main.py` via `app.include_router(...)`, generally prefixed `/api/...`.

## API contract

**Backend Pydantic schemas** (`backend/app/schemas/`) are the source of truth for request/response shapes (camelCase aliases for the frontend).

When adding or changing an endpoint a Vue component already calls:

- Still **read the call site** under `frontend/src/features/**` (and `utils/api.ts`). Silent `??` / wrong field-name fallbacks (`duration` vs `durationMinutes`, `timeLimit` vs `timeLimitMinutes`) can hide drift without throwing.
- Prefer `id` in new frontend code. Some exam-related schemas still emit a computed `_id` alongside `id` (Mongo-era holdover); do not reintroduce `_id` reads in new FE code.

Phase 1.5/1.6 largely aligned FE/BE contracts. The residual risk is silent fallbacks, not “treat Mongo shapes as the only spec.”

## Deploy & env

- **Primary production:** Vercel (Vue SPA) + Railway (FastAPI + Postgres) + Cloudflare R2 — see `DEPLOYMENT.md` and `frontend/vercel.json`.
- **Local / demo full stack:** `docker-compose.yml`.
- Root `.env.example` is compose-oriented. Full backend vars (R2, OAuth, etc.) live in `backend/.env.example`.

Trustworthy: `DEPLOYMENT.md`, `docker-compose.yml`, `backend/.env.example`, `CLAUDE.md` / `AGENTS.md`.

## Quality gates (do not skip)

- **Backend:** `cd backend && ./venv/Scripts/python.exe -m pytest` (~104 tests, SQLite in-memory via `client` / `db_session` in `conftest.py`). Run the relevant modules after any backend change.
- **Frontend:** ESLint (`npm run lint:js`, includes custom token palette rule), stylelint (`npm run lint:style`), Prettier (`format` / `format:check`), and `vue-tsc` via `npm run build`. **No vitest/jest yet** — those gates are the FE verification path.

## Frontend layout

Phase 1.5 restructure is **done**. UI lives under `frontend/src/features/<domain>/` with cross-feature primitives in `frontend/src/shared/components/`. Do not reintroduce a top-level `frontend/src/components/` folder. See the `vue-guide` skill for design-system conventions.
