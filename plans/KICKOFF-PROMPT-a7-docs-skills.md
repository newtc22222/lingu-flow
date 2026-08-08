# Kickoff prompt — Horizon A docs & agent skills (A7 / #50)

> **How to use:** Copy everything below the horizontal rule into a **fresh** agent session as the first message.

---

Implement **Horizon A package A7** for LinguFlow: make agent docs and skills match repository reality so future sessions do not skip tests, invent a Mongo API, or target a dead Express deploy path.

**Issue:** https://github.com/newtc22222/lingu-flow/issues/50  
**Artifact findings:** F-10, F-11  
**Plan:** `plans/05-reliability-and-ops.md` (docs section) · `plans/09-implementation-backlog.md` (A7)

**Prerequisite:** Horizon A security stack (#44–#46) is done or in review. Do **not** re-implement JWT/exam visibility/SSE in this issue.

---

## Mission

Agents (and humans) reading the repo first should learn:

1. **Primary production** is Vercel (frontend) + Railway (API + Postgres) + Cloudflare R2 — not Express-on-Vercel.
2. **Local full stack** is `docker compose` (secondary / dev).
3. Backend has a **real pytest suite**; frontend gates are `vue-tsc` + ESLint + stylelint + Prettier (no vitest yet unless already added).
4. Phase 1.5/1.6 largely aligned FE/BE contracts; silent `?? fallback` remains the residual risk, not “treat Mongo shapes as the only spec.”
5. Exam authz / answer-key rules documented in `CLAUDE.md` (may already exist from security PR) stay accurate.

---

## Scope

### In scope (docs / skills / env examples only)

| File / area | Work |
|-------------|------|
| `CLAUDE.md` | Remove or mark resolved obsolete Express / `api/index.ts` / broken Vercel path warnings; declare **primary vs local** deploy; keep security/authz notes if already present; accurate test commands and rough test counts |
| `.claude/skills/project-conventions/SKILL.md` | Delete “no test suite / no lint” claim; describe pytest + frontend lint gates; soften mid-migration “frontend is Mongo API spec” language |
| Root `.env.example` | If still Node/Mongo-era (`MONGO_URI`), fix or delete and point to `backend/.env.example` |
| `DEPLOYMENT.md` | Only touch if it contradicts primary topology; prefer align CLAUDE to DEPLOYMENT if DEPLOYMENT is already correct |
| `RELEASE.md` | Optional: refresh test counts if you touch it |
| `plans/README.md` | Optional: note A7 closed when done |

### Out of scope

- Application code changes (backend/frontend logic)
- F-04 transactions, F-06 seed entrypoint, F-08 Postgres harness
- Horizon B performance work
- Creating new product features

---

## Concrete checklist

### 1. Audit current claims

Grep and read:

```text
api/index.ts
MONGO_URI
No test suite
empty scaffolding
backend/src
Express
vercel.json
docker-compose
```

in `CLAUDE.md`, `.claude/skills/**`, root `.env.example`, `AGENTS.md`.

### 2. CLAUDE.md

- **Stale docs section:** rewrite so it does not warn about a missing Express path if `api/index.ts` is gone and `DEPLOYMENT.md` already describes Railway+Vercel+R2.
- **Deploy:** one short block:

```markdown
## Deployment topology

- **Primary production:** Vercel (Vue SPA) + Railway (FastAPI + Postgres) + Cloudflare R2 — see DEPLOYMENT.md and frontend/vercel.json.
- **Local / demo full stack:** docker-compose.yml (postgres, backend, frontend).
```

- **Tests:** point at `cd backend && ./venv/Scripts/python.exe -m pytest` (or project’s real command); note frontend has no unit suite yet unless that changed.
- **Do not** remove the question-bank or exam authz invariants sections if present.

### 3. project-conventions skill

Replace the “Project state” / “no pytest / no lint” paragraph with current truth:

- pytest under `backend/tests/`
- ESLint (+ custom token rule), stylelint, Prettier under `frontend/`
- Frontend layout is feature-based (`features/`), not “mid empty migration”
- API contract: backend schemas are source of truth; still verify FE call sites for silent fallbacks

### 4. Root `.env.example`

Either:

- Update to point to backend vars, or  
- Replace body with a short pointer to `backend/.env.example`

Do not leave `MONGO_URI` as if it were live.

### 5. Light consistency

If `README.md` still claims SSE “real-time progress” as a product feature and events are gone, either soften the README bullet or leave a one-line note that SSE was removed — only if you can do it in the same PR without scope creep. Prefer CLAUDE accuracy first.

---

## Definition of done

- [ ] A new agent reading only `CLAUDE.md` + project-conventions would **not** skip pytest/lint because docs said they are missing
- [ ] Primary (Vercel+Railway+R2) vs local (compose) is unambiguous
- [ ] No remaining “implement Express on Vercel via `api/index.ts`” as current guidance
- [ ] Root env example is not Mongo-era
- [ ] `gh issue close 50` is justified (or leave open only if a deliberate residual remains — list it)

**No pytest required** unless you accidentally touch code. If only markdown: done when the files above are accurate.

---

## Ground rules

- Docs-only PR preferred: `docs: fix stale agent guidance and deploy topology (F-10, F-11)`
- Conventional Commits; **never** AI co-author trailers
- Do not commit unless asked
- If security PR is not merged yet, base this branch on that branch or on `main` after merge — avoid conflicting CLAUDE.md rewrites; re-read CLAUDE before editing

## Suggested branch

```text
docs/horizon-a-agent-skills-a7
```

Closes #50.
