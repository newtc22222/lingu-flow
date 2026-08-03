---
name: project-conventions
description: Background knowledge of LinguFlow's backend layering and mid-migration API contract rules. Not user-invocable; Claude should apply it automatically whenever touching backend/app or a frontend component that calls /api/...
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

## The frontend is the API spec (until stated otherwise)

The Vue frontend (`frontend/src/`) was built against the old Node.js/Express/MongoDB API and was not touched by the Python rewrite (commit `a9fec74`). When implementing any backend endpoint, treat the frontend's actual `fetch`/`apiFetch` call sites as the ground truth for request/response shape — not assumptions, not the old Node code. Check per-endpoint whether the frontend's Mongo-style `_id` should be kept (schema alias) or migrated to `id` (also update the frontend).

The frontend itself is also mid-migration: it's moving from a flat `frontend/src/components/` folder to `frontend/src/features/<domain>/` (see the `vue-guide` skill for the full layout and current design-system conventions). When grepping for a call site, check `features/**` first — some `components/*.vue` files are dead code left behind by that move, not live call sites.

## Known-stale references — never trust without cross-checking code

- `DEPLOYMENT.md` / `api/index.ts` — describe deploying `backend/src` (Express) on Vercel; `backend/src` no longer exists.
- Root `.env.example` — still lists `MONGO_URI`; real backend vars are in `backend/.env.example`.

`README.md`, `docker-compose.yml`, and `AGENTS.md` (a thin pointer to `CLAUDE.md`) are current and trustworthy.

## Project state

No test suite (no pytest/vitest configured) and no lint/format tooling (no ESLint/Prettier/Ruff) exist yet — don't assume `npm test` or a linter will catch mistakes; verify manually or via the `api-contract-reviewer` subagent.
