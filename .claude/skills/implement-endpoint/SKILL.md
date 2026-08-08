---
name: implement-endpoint
description: Implements a FastAPI backend endpoint that matches the existing Vue frontend's expected request/response shape. Use when adding or changing any /api/... route under backend/app (auth, decks, cards, exams, etc.).
---

# Implement Endpoint

LinguFlow's backend is Python/FastAPI/PostgreSQL (`backend/app/`). Backend Pydantic schemas are the source of truth for shapes; when a Vue call site already exists, still verify it so silent `??` fallbacks do not hide field-name drift.

## Workflow

1. **Find every call site for the endpoint.** Grep `frontend/src/` (especially `frontend/src/features/**`, `frontend/src/utils/api.ts`) for the route path (e.g. `/api/decks`). Note every HTTP method used against it.
2. **Extract the exact contract from each call site:**
   - Request: body shape, query params, headers (most calls go through `apiFetch` in `frontend/src/utils/api.ts`, which adds `Authorization: Bearer <token>`).
   - Response: every field the frontend reads off the response. Search the component for `response.json()` / destructuring to be exhaustive — don't assume, read the actual usage.
   - Status codes the frontend branches on (e.g. `401` triggers logout in `apiFetch`).
3. **Prefer `id` over Mongo-era `_id`.** Some exam schemas still emit a computed `_id` alongside `id`. Default to Postgres-native `id` in the SQLAlchemy model/schema; only keep an `_id` alias if an existing call site still depends on it (and plan to remove that FE read). If you do touch the frontend call site, follow the `vue-guide` skill's conventions (feature-folder layout, Pinia for shared state, the arcade token/theme system).
4. **Implement following the existing layering** (see `backend/app/{routers,services,models,schemas}/` and the `project-conventions` skill):
   - `models/<name>.py` — SQLAlchemy table (only if it doesn't exist yet).
   - `schemas/<name>.py` — Pydantic request/response models matching step 2/3.
   - `services/<name>.py` — business logic, takes an `AsyncSession` via `get_db()`.
   - `routers/<name>.py` — HTTP layer only, prefixed `/api/...`, delegates to the service.
5. **Register the router in `backend/app/main.py`** via `app.include_router(...)`. This is easy to forget — verify manually.
6. **If a model changed**, generate an Alembic migration: `cd backend && alembic revision --autogenerate -m "<message>"`.
7. **Verify:**
   - Run the relevant pytest modules: `cd backend && ./venv/Scripts/python.exe -m pytest tests/<related>.py -v` (fixtures in `tests/conftest.py`).
   - If the frontend was touched: `npm run build` and the lint scripts under `frontend/`.
   - Optionally exercise the UI flow, or re-read the component's usage of the response and confirm every accessed field is present.

## Notes

- A real pytest suite lives under `backend/tests/` (~104 tests). Do not skip it because older docs claimed there was none.
- Auth endpoints (`/api/auth/*`) involve JWT and optional Google OAuth — check `backend/.env.example` for required secrets, and never hardcode `JWT_SECRET`.
- Production deploy is Vercel (SPA) + Railway (API/Postgres) + R2 — not Express-on-Vercel. See `DEPLOYMENT.md`.
