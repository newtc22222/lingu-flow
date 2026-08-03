# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LinguFlow is a keyboard-driven flashcard app with Spaced Repetition (SM-2 algorithm) and a certification exam simulator (TOEIC, IELTS, HSK, JLPT). Frontend: Vue 3 + Vite + TailwindCSS v4. Backend: Python/FastAPI + PostgreSQL.

## Critical context: mid-migration backend

The backend was fully rewritten from Node.js/Express/MongoDB to Python/FastAPI/PostgreSQL (see commit `a9fec74`). This rewrite is **only scaffolding** — `backend/app/{models,schemas,services,core}/` are empty packages, and `backend/app/main.py` registers only `GET /api/health` (`backend/app/routers/health.py`). No auth, decks, cards, or exams endpoints exist in the Python backend yet.

The Vue frontend, however, is fully built against the **old** Node.js API contract and was not touched by the rewrite. Its components call REST endpoints that don't exist server-side yet:

- `features/auth/AuthView.vue` (formerly `Login.vue` / `Signup.vue`) → `/api/auth/{login,register,guest,google}`
- `features/library/DeckManagementView.vue` (formerly `DeckManagement.vue`) → `/api/decks[/:id]`
- `features/library/CardManagementView.vue` (formerly `CardManagement.vue`) / `features/dashboard/DashboardView.vue` (formerly `StudyDashboard.vue`) → `/api/cards[/:id]`, `/api/cards/study`, `/api/cards/review/:id`
- `components/ExamHub.vue` / `features/exam/ExamView.vue` (formerly `ExamRoom.vue`) / `components/ExamResults.vue` / `components/ExamCreator.vue` / `features/exam/store/examStore.ts` → `/api/exams/templates[/:id[/questions]]`, `/api/exams/sessions[/:id[/answer|finish|details]]`

When implementing backend features, treat these call sites as the de facto API spec unless told otherwise, and check the actual component/store for the exact request/response shape each one expects (many still reference Mongo-style `_id` fields — decide per-endpoint whether to keep that shape or migrate the frontend to `id`). See the "Frontend restructure" note below for where these files actually live now.

**Stale docs — do not trust without cross-checking code:**

- `DEPLOYMENT.md` and `api/index.ts` describe deploying `backend/src/app` (Express) via a Vercel serverless function — `backend/src` no longer exists (it's `backend/app`, FastAPI, not designed as a single Vercel function handler). This deployment path is broken until reworked for the Python backend.
- Root `.env.example` still lists `MONGO_URI` (Node-era). The real backend env vars are in `backend/.env.example` (`DATABASE_URL`, `JWT_SECRET`, etc.).
- `README.md` and `docker-compose.yml` reflect the current (Python/Postgres) reality and are trustworthy.

No test suite exists yet for either frontend or backend (no pytest/vitest/jest configured).

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

- No router library — `App.vue` holds a single `currentView` ref (a string union type `AppView`) and conditionally renders the top-level view components. Auth state (`isAuthenticated`) is derived from presence of a `token` in `localStorage`.
- `utils/api.ts` (`apiFetch`) wraps `fetch`, attaching `Authorization: Bearer <token>` from `localStorage` and clearing the token + reloading on `401`. Use it (or a Pinia store action that wraps it, e.g. `features/exam/store/examStore.ts`) for all authenticated calls instead of raw `fetch`.
- All Vue components use `<script setup lang="ts">` (Composition API) exclusively — follow this convention for new components.
- **State**: Pinia (`createPinia()` in `main.ts`) is available for state shared across components/views (see `features/exam/store/examStore.ts`). Local/single-view state still just uses `ref`/`computed` directly in the component.
- **Path alias**: `@` → `frontend/src` (configured in both `vite.config.ts` and `tsconfig.app.json`) — prefer `@/utils/api` style imports in new code under `features/`.
- Styling is Tailwind v4, but **not** a dark slate/emerald theme — it's a retro-arcade pixel design system. Design tokens (8 brand colors: `ink`, `cabinet`, `cabinet-light`, `amber`, `red`, `green`, `phosphor`, `muted`, plus derived shades) live as CSS custom properties in `frontend/src/styles/tokens.css` and are re-exposed as Tailwind utilities via a `@theme` block (e.g. `bg-ink`, `text-phosphor`, `bg-amber`). Never hardcode hex values in components — use the token utilities/classes. Fonts: `font-pixel` (Press Start 2P, headers/labels only) and `font-body`/`font-label` (IBM Plex Sans/Mono); **`font-pixel` has no Vietnamese diacritic glyphs**, so any Vietnamese-language string must use `font-body`/`font-label` instead.
- `vite.config.ts` proxies `/api/*` to `localhost:8000` in dev, so frontend code should always call relative `/api/...` paths, never an absolute backend URL.

**Frontend restructure (undocumented until now — verify against code, not this list, before relying on it):** the flat `frontend/src/components/` layout is being migrated to a feature-folder layout, `frontend/src/features/<domain>/{<Name>View.vue, components/, store/}`, with cross-feature reusable primitives in `frontend/src/shared/components/` (e.g. `PixelFrame.vue`). Migrated so far: `features/auth`, `features/dashboard`, `features/exam` (incl. `store/examStore.ts`), `features/flashcards`, `features/library`. Still living in the legacy `components/` folder and **not yet migrated**: `ExamHub.vue`, `ExamResults.vue`, `ExamCreator.vue`, `MarkdownRenderer.vue` (actively used by `features/library/CardManagementView.vue` and `features/flashcards/components/FlashCard.vue` — do not delete). `components/StudyDashboard.vue` and `components/HelloWorld.vue` are orphaned (no longer imported anywhere, superseded by `features/dashboard/DashboardView.vue`) — don't treat grep hits on them as live call sites, and feel free to flag for deletion if asked to clean up.

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
