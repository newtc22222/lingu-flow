---
name: implement-endpoint
description: Implements a FastAPI backend endpoint that matches the existing Vue frontend's expected request/response shape. Use when adding any /api/... route to backend/app (auth, decks, cards, exams) during the Node->Python migration, since the frontend was never updated and is the de facto API spec.
---

# Implement Endpoint

LinguFlow's backend was rewritten from Node/Express/MongoDB to FastAPI/PostgreSQL as bare scaffolding (see `CLAUDE.md`). The Vue frontend was **not** touched by that rewrite — it still calls the old API contract. Until the backend catches up, every frontend call site is the spec for the endpoint it calls.

## Workflow

1. **Find every call site for the endpoint.** Grep `frontend/src/` (including `frontend/src/features/**`, `frontend/src/utils/api.ts`) for the route path (e.g. `/api/decks`). Note every HTTP method used against it.
2. **Extract the exact contract from each call site:**
   - Request: body shape, query params, headers (most calls go through `apiFetch` in `frontend/src/utils/api.ts`, which adds `Authorization: Bearer <token>`).
   - Response: every field the frontend reads off the response (e.g. `data._id` vs `data.id`, nested objects, arrays). Search the component for `response.json()` / destructuring to be exhaustive — don't assume, read the actual usage.
   - Status codes the frontend branches on (e.g. `401` triggers logout in `apiFetch`).
3. **Decide the `_id` vs `id` question per endpoint.** Some components still expect Mongo-style `_id`. Default to Postgres-native `id` in the SQLAlchemy model/schema and either update the frontend call site to match, or alias in the Pydantic response schema (`Field(..., alias="_id")` / `serialization_alias`) if the frontend is out of scope for this change. Don't silently leave a mismatch. If you do touch the frontend call site, follow the `vue-guide` skill's conventions (feature-folder layout, Pinia for shared state, the arcade token/theme system).
4. **Implement following the existing layering** (see `backend/app/{routers,services,models,schemas}/` and the `project-conventions` skill):
   - `models/<name>.py` — SQLAlchemy table (only if it doesn't exist yet).
   - `schemas/<name>.py` — Pydantic request/response models matching step 2/3 exactly.
   - `services/<name>.py` — business logic, takes an `AsyncSession` via `get_db()`.
   - `routers/<name>.py` — HTTP layer only, prefixed `/api/...`, delegates to the service.
5. **Register the router in `backend/app/main.py`** via `app.include_router(...)`. This is easy to forget — a hook exists to catch it, but verify manually too.
6. **If a model changed**, generate an Alembic migration: `cd backend && alembic revision --autogenerate -m "<message>"`.
7. **Verify against the frontend**, not just OpenAPI docs: start both (`docker-compose up --build` or the two `npm run dev:*` scripts) and exercise the actual UI flow that hits the new endpoint, or at minimum re-read the component's usage of the response and confirm every field it accesses is present.

## Notes

- No test suite exists yet — don't assume pytest/vitest fixtures are available; verification is manual (step 7) or the `api-contract-reviewer` subagent.
- Auth endpoints (`/api/auth/*`) involve `python-jose` (JWT) and `google-auth` (Google OAuth) — check `backend/.env.example` for required secrets, and never hardcode `JWT_SECRET`.
