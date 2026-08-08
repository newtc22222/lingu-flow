# 05 — Reliability, Deployment & Operations

**Findings covered:** F-06, F-09 (ops angle), F-10, F-11, parts of F-14  
**Horizon:** A/B  
**Effort:** ~1 day ops fixes + ongoing observability

---

## Deployment topologies (F-11)

### Reality today

| Topology | Role | Status |
|----------|------|--------|
| **Vercel SPA + Railway API + Railway Postgres + R2** | Production | Documented in `DEPLOYMENT.md`; `frontend/vercel.json` points at Railway |
| **docker-compose** (postgres, backend, frontend) | Local / demo full stack | Works; no healthcheck on depends_on; no Redis |

### Decision (record in CLAUDE.md + DEPLOYMENT.md)

```text
PRIMARY PRODUCTION: Vercel (frontend) + Railway (API + Postgres) + Cloudflare R2
SECONDARY LOCAL:    docker compose up --build
```

Compose is **not** the production reference for networking (no Vercel rewrite, different CORS). It **is** the reference for service list and env shape for local parity.

### Compose hardening

1. Add `healthcheck` on `postgres` (`pg_isready`).
2. Backend `depends_on: postgres: condition: service_healthy`.
3. Align backend env with `.env.example` (no weak secret when simulating production).
4. Optional: `profiles: ["full"]` if later adding redis/worker.

### entrypoint.sh

Current pattern `alembic upgrade head && uvicorn ...` is correct for Railway. Ensure:

- Retries or wait-for-db if compose race remains.
- Seed **not** in multi-worker lifespan (see F-06).

---

## F-06 — Built-in exam seeding ownership

### Problem

`lifespan` runs `seed_builtin_exams` in **every** worker/replica. On `seed_version` bump:

- Concurrent delete links / archive / re-link races
- Unique `seed_key` collisions or duplicate composition rows
- Exceptions swallowed → app serves half-seeded state

Hidden on single-process dev and single Railway replica; fails on scale-out.

### Options

| Approach | Pros | Cons |
|----------|------|------|
| **A. Run seed once in entrypoint after migrate** | Clear ownership, simple | Requires deploy command change |
| **B. Postgres advisory lock in seeder** | Safe even if called multiple times | Still runs on every boot (wasted work) |
| **C. Alembic data migration** | Versioned with schema | Harder for content-heavy TOEIC seeds |

**Recommendation:** **A + B belt-and-suspenders**

1. Move seed call to `entrypoint.sh` after `alembic upgrade head` (one process at container start).
2. Keep seeder idempotent + take `pg_advisory_lock(SEED_LOCK_ID)` for the duration of a version bump.
3. Remove seed from FastAPI lifespan (or leave a no-op log “seed is entrypoint-owned”).
4. **Do not swallow** seed failures in production — exit non-zero so Railway marks deploy failed.

### Acceptance

- [ ] Two concurrent seed invocations cannot double composition (advisory lock test).
- [ ] API process boot does not mutate seed data.
- [ ] Failed seed fails deploy in production.

---

## Observability plan

### Minimum viable (Horizon B)

| Pillar | Near-term choice | What to capture |
|--------|------------------|-----------------|
| **Metrics** | Railway metrics + simple `/api/health` extended | uptime, optional DB ping |
| **Logs** | Structured JSON logs (stdlib or structlog) | request_id, user_id hash, path, status, latency_ms |
| **Errors** | Sentry (optional free tier) | unhandled exceptions, auth failures rate |
| **Frontend** | Vercel Speed Insights (already) + error boundary logging | route, build id |

### Health endpoints

| Endpoint | Meaning |
|----------|---------|
| `GET /api/health` | Process up |
| `GET /api/health/ready` | DB `SELECT 1` succeeds (for orchestrators) |

Do not require auth on health.

### Alerts (when traffic exists)

- 5xx rate > 2% for 5 minutes
- p95 latency > 1s for non-AI routes
- Deploy seed failure
- Disk / connection pool saturation on Postgres

---

## Jobs & async work

### Today

- Guest cleanup: manual/cron one-shot module.
- No queue.

### Guidance

| Work | Mechanism |
|------|-----------|
| Guest purge | Railway cron → `python -m app.jobs.cleanup_guests` daily |
| Seed | Entrypoint only |
| AI generation (Phase 2) | Job table or Redis queue + worker service |
| PDF reports (Phase 3) | Same worker path |
| Email reset | Sync OK until volume; then queue |

Do not add Celery/RQ until Phase 2 needs retries/timeouts for LLM calls.

---

## F-09 ops note

Deleting unused SSE reduces:

- Open connection memory per client
- Proxy timeout complexity
- JWT logging risk

If product needs “live progress,” design event types first, then transport.

---

## Documentation fixes (F-10)

Update in one docs PR:

1. **CLAUDE.md**
   - Remove obsolete Express/Vercel `api/index.ts` warning (or mark resolved).
   - Note primary deploy topology.
   - Transaction ownership convention (after F-04).
   - Accurate test commands and counts.
2. **`.claude/skills/project-conventions/SKILL.md`**
   - Delete “no test suite / no lint” claim.
   - Point to pytest, ESLint, stylelint, Prettier.
   - Soften “frontend is Mongo-era API spec” — Phase 1.5/1.6 largely aligned; remaining risk is silent `??` fallbacks.
3. **RELEASE.md** — optional refresh of test counts.
4. **Root `.env.example`** — if still `MONGO_URI`, replace or delete; point to `backend/.env.example`.

---

## Disaster recovery (lightweight)

| Item | Target |
|------|--------|
| RPO | 24h (Railway automatic backups if enabled; verify) |
| RTO | 4h (redeploy + restore) |
| Backup test | Restore to staging once per quarter |
| Secret rotation | JWT_SECRET rotation runbook (invalidate sessions) |

---

## Multi-instance readiness checklist

Before scaling Railway replicas > 1:

- [ ] F-06 seed not in lifespan
- [ ] F-04 single commit owner (no cross-request assumptions)
- [ ] Sticky sessions **not** required (JWT stateless OK)
- [ ] No local disk dependency (use R2)
- [ ] SSE deleted or moved to shared pub/sub
- [ ] Rate limits at edge or shared store

---

## Next

→ [06-performance-and-scale.md](./06-performance-and-scale.md) for dashboard SQL, cache triggers, future scale blocks.
