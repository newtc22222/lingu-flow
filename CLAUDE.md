# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LinguFlow is a keyboard-driven flashcard app with Spaced Repetition (SM-2 algorithm) and a certification exam simulator (TOEIC, IELTS, HSK, JLPT). Frontend: Vue 3 + Vite + TailwindCSS v4. Backend: Python/FastAPI + PostgreSQL.

## Backend status

The backend was rewritten from Node.js/Express/MongoDB to Python/FastAPI/PostgreSQL (commit `a9fec74`). That migration is **done** — `backend/app/{models,schemas,services,routers}/` are fully populated and `main.py` registers auth, cards, dashboard, decks, exams, events, media, and health routers.

The API is the source of truth for request/response shapes; the Pydantic schemas in `backend/app/schemas/` use camelCase aliases to match the frontend. Note that `ExamTemplateResponse`/`QuestionResponse`/`ExamSessionResponse` still emit a computed `_id` alongside `id` — a Mongo-era holdover. **Prefer `id` in new frontend code**; the `_id` reads were removed from the frontend during Phase 1.5.

When adding an endpoint a component already calls, check the call site for the shape it expects, and mind the field names: several frontend/backend mismatches (`duration` vs `durationMinutes`, `timeLimit` vs `timeLimitMinutes`, a flat vs. nested session-details response) went unnoticed for a long time because they failed silently into fallback values rather than erroring.

**Questions are a shared bank, not exam property** (Phase 1.6). `Question` has no `exam_template_id`; placement lives in the `exam_template_questions` join table, so one question can appear in many exams and deleting an exam removes only its links. Three invariants exist to stop a shared, mutable bank corrupting finished sessions — don't work around them:

- **Session results resolve from `AnswerRecord`, not the template.** `create_session` pre-creates one record per question and freezes their order in `AnswerRecord.order_index`. Reading the template's *current* composition instead would let attach/detach/reorder/re-seed retroactively rewrite somebody's finished exam.
- **Deleting a question is a soft delete** (`Question.archived_at`). `AnswerRecord.question_id` cascades, so a hard delete erases the answer history of every past session that used it. Bank listings filter archived rows; session/results resolution deliberately does not.
- **An answered question's `options`/`correct_answer` are frozen** (409). Changing them would leave every stored `is_correct` disagreeing with the displayed key.

Built-in exams are keyed on `exam_templates.seed_key` with a `seed_version`; bumping the version updates the template row **in place** so its id survives for past sessions. Never match seed content by `name`.

Tests: `backend/tests/` runs under pytest (`cd backend && ./venv/Scripts/python.exe -m pytest`), currently 46 tests against SQLite in-memory via the `client`/`db_session` fixtures in `conftest.py`. **There is still no frontend test suite** (no vitest/jest) — `npm run build` (which runs `vue-tsc`) plus the two lint scripts are the only frontend gates.

Migrations are Alembic under `backend/alembic/versions/` (`0001_initial_schema`, `0002_card_position_image_notes`).

**Stale docs — do not trust without cross-checking code:**

- `DEPLOYMENT.md` and `api/index.ts` describe deploying `backend/src/app` (Express) via a Vercel serverless function — `backend/src` no longer exists (it's `backend/app`, FastAPI, not designed as a single Vercel function handler). This deployment path is broken until reworked for the Python backend.
- Root `.env.example` still lists `MONGO_URI` (Node-era). The real backend env vars are in `backend/.env.example` (`DATABASE_URL`, `JWT_SECRET`, etc.).
- `README.md` and `docker-compose.yml` reflect the current (Python/Postgres) reality and are trustworthy.

## Commands

### Docker (full stack)

```bash
docker-compose up --build
```

Frontend → `http://localhost:8080`, Backend → `http://localhost:8000`, OpenAPI docs → `http://localhost:8000/docs`, Postgres → `localhost:5432`.

### Backend (Python 3.12, from `backend/`)

```bash
python -m venv venv
.\venv\Scripts\Activate.ps1        # Windows
pip install -r requirements.txt
python -m uvicorn app.main:app --port 8000 --reload
```

Or from repo root: `npm run dev:backend` (assumes a `backend/venv` already exists on Windows).

Database migrations (Alembic, config at `backend/alembic.ini`, no migrations committed yet):

```bash
cd backend
alembic revision --autogenerate -m "message"
alembic upgrade head
```

### Frontend (from `frontend/`, or `npm run dev:frontend` / `npm run build:frontend` from repo root)

```bash
npm install
npm run dev       # Vite dev server; proxies /api -> http://localhost:8000 (see vite.config.ts)
npm run build      # runs `vue-tsc -b` (typecheck) then `vite build`
npm run preview
```

There is no root-level install/build step beyond the `dev:*`/`build:frontend` scripts in the root `package.json` — frontend and backend dependencies are managed independently in their own directories (no npm workspaces despite what `DEPLOYMENT.md` implies).

## Architecture

### Backend (`backend/app/`)

- `main.py` — FastAPI app factory, CORS, router registration, lifespan (opens/disposes the async SQLAlchemy engine).
- `config.py` — Pydantic Settings (`Settings`), loaded from `backend/.env` via `get_settings()` (lru-cached). `JWT_SECRET` falls back to a dev default outside `ENVIRONMENT=production`, where it's required.
- `database.py` — Async SQLAlchemy engine/session (`asyncpg` driver), `Base` declarative class, `get_db()` FastAPI dependency yielding an `AsyncSession` with commit/rollback handling.
- `routers/`, `models/`, `schemas/`, `services/`, `core/` — empty scaffolding; new features should add modules here following FastAPI's router → service → model layering (router handles HTTP, service holds business logic, model is the SQLAlchemy table, schema is the Pydantic I/O shape).
- New routers must be included in `main.py` (`app.include_router(...)`) and generally prefixed `/api/...` to match the frontend and the Vite proxy.

### Frontend (`frontend/src/`)

- **Routing**: `vue-router` (`src/router/index.ts`). `App.vue` is a `RouterView` shell holding the nav bar and language switcher. Every route is lazy-loaded; a `beforeEach` guard redirects to `/auth` unless the route sets `meta.public`. Routes that own their full-bleed layout set `meta.fullBleed` to opt out of the centered `.arcade-app` column. Auth state lives in `features/auth/store/authStore.ts` (a reactive token, so the guard re-evaluates per navigation) — don't read `localStorage` directly for auth.
- **i18n**: `vue-i18n` (`src/i18n/index.ts`, locales in `src/locales/{vi,en}.json`, VI default). All user-facing copy must go through `t()`, including prop defaults. See `.context/ui-guidelines.md` for how this interacts with the `font-pixel` diacritic limitation.
- `utils/api.ts` (`apiFetch`) wraps `fetch`, attaching `Authorization: Bearer <token>` from `localStorage` and clearing the token + redirecting to `/auth` on `401`. Use it (or a Pinia store action that wraps it, e.g. `features/exam/store/examStore.ts`) for all authenticated calls instead of raw `fetch`.
- All Vue components use `<script setup lang="ts">` (Composition API) exclusively — follow this convention for new components.
- **State**: Pinia (`createPinia()` in `main.ts`) is available for state shared across components/views (see `features/exam/store/examStore.ts`). Local/single-view state still just uses `ref`/`computed` directly in the component.
- **Path alias**: `@` → `frontend/src` (configured in both `vite.config.ts` and `tsconfig.app.json`) — prefer `@/utils/api` style imports in new code under `features/`.
- Styling is Tailwind v4, but **not** a dark slate/emerald theme — it's a retro-arcade pixel design system. Design tokens (8 brand colors: `ink`, `cabinet`, `cabinet-light`, `amber`, `red`, `green`, `phosphor`, `muted`, plus derived shades) live as CSS custom properties in `frontend/src/styles/tokens.css` and are re-exposed as Tailwind utilities via a `@theme` block (e.g. `bg-ink`, `text-phosphor`, `bg-amber`). Never hardcode hex values in components — use the token utilities/classes. Fonts: `font-pixel` (Press Start 2P, headers/labels only) and `font-body`/`font-label` (IBM Plex Sans/Mono); **`font-pixel` has no Vietnamese diacritic glyphs**, so any Vietnamese-language string must use `font-body`/`font-label` instead.
- `vite.config.ts` proxies `/api/*` to `localhost:8000` in dev, so frontend code should always call relative `/api/...` paths, never an absolute backend URL.

**Frontend layout (restructure completed in Phase 1.5):** the flat `frontend/src/components/` folder is gone. Everything lives in `frontend/src/features/<domain>/{<Name>View.vue, components/, store/, types.ts}` — `auth`, `dashboard`, `exam`, `flashcards`, `library` — with cross-feature primitives in `frontend/src/shared/components/` (`AppButton`, `ManageListShell`, `PixelFrame`, `MarkdownRenderer`). Don't reintroduce a top-level `components/` folder; promote a component to `shared/` rather than importing across feature boundaries.

Note that `.stylelintrc.json` exempts specific files by path and those globs **do not follow renames** — check them whenever you move a component.

### Deployment

`docker-compose.yml` is the current known-good multi-container setup (Postgres + FastAPI + Nginx-served Vue build) and should be treated as the reference for how the three services fit together. The Vercel path (`vercel.json`, `api/index.ts`) predates the Python migration and needs rework before it can be relied on.

## UI Development

Before touching any frontend/UI code, read these in order:

1. `frontend/src/styles/tokens.css` — the full token set (colors, spacing, font-size, tracking, border-width, `--focus-ring-width`).
2. `frontend/COMPONENTS.md` — component inventory (`AppButton`, `ManageListShell`, `PixelFrame`, `MarkdownRenderer`, etc.) — check here before creating any new component.
3. `.context/ui-guidelines.md` — MUST/SHOULD/AVOID rules for UI code.

ESLint + stylelint (`frontend/eslint.config.js`, `frontend/.stylelintrc.json`) mechanically enforce the `[MUST]` token/component rules from `ui-guidelines.md` — violations fail CI, they don't just silently deviate from the guidance above.

## Commit Rules

When creating commits, follow these rules:

1. Write clear, concise commit messages using Conventional Commits:
   - `feat:` New feature
   - `fix:` Bug fix
   - `refactor:` Code restructuring without behavior changes
   - `docs:` Documentation changes
   - `test:` Test changes
   - `chore:` Maintenance tasks
   - `perf:` Performance improvements
   - `build:` Build system or dependency changes
   - `ci:` CI/CD changes

2. Keep commits focused on a single logical change.

3. Do not include unrelated modifications in the same commit.

4. Before committing:
   - Review the diff.
   - Remove debug code, temporary files, and commented-out code.
   - Ensure tests (if applicable) pass.

5. **Never add Claude, Anthropic, or any AI assistant as a contributor.**
   - Do not add `Co-authored-by:` trailers.
   - Do not add `Generated-by:` or similar attribution.
   - Do not modify AUTHORS, CONTRIBUTORS, or credits to include AI.
   - The commit author should always be the configured Git user.

6. Do not rewrite Git history unless explicitly instructed.

7. If the changes are too large for a single commit, propose splitting them into multiple logical commits.
