# 06 — Performance & Scale

**Findings covered:** F-07, F-14 (Redis/AI keys), capacity from 02  
**Horizon:** B for F-07; scale blocks for later phases  
**Effort:** 0.5–1 day dashboard; Redis only if triggered

---

## Performance philosophy

LinguFlow near-term traffic is **~5–20 QPS peak** at 10k DAU. Optimize for:

1. **Correctness first** (Horizons A).
2. **Per-user data growth** (power users with thousands of cards) — this bites before global QPS.
3. **AI cost and latency** (Phase 2) — different bottleneck class.

Avoid premature: Redis, read replicas, sharding, microservices.

---

## F-07 — Dashboard full-dataset load

### Current behavior

`get_progress` loads:

- All cards for user
- All decks for user  
- All completed sessions

…then aggregates XP, readiness, world maps in Python.

### Target queries

| Metric | Approach |
|--------|----------|
| Card counts / XP | `COUNT` / `SUM` SQL with filters on `user_id` |
| Due cards | `COUNT(*) WHERE srs_next_review <= now()` |
| Per-deck progress | `GROUP BY deck_id` with `COUNT` and average repetitions or % mature |
| Exam readiness | Aggregate from `exam_sessions` scores (`AVG`, last N) |
| Worlds UI | Only deck id, name, progress percent — not full card entities |

### Index checklist

Confirm present or add:

- `cards(user_id, srs_next_review)`
- `cards(user_id, deck_id)`
- `exam_sessions(user_id, status, finished_at)`
- `decks(user_id)`

### Acceptance

- [ ] No full `select(Card)` for dashboard progress.
- [ ] Manual test with 5k cards: p95 < 300 ms on local Postgres.
- [ ] Response shape unchanged for frontend (or FE updated in same PR).

---

## Read path inventory & caching

| Path | Hot? | Strategy now | Later |
|------|------|--------------|-------|
| Dashboard | Per login | SQL aggregates | Cache 30–60s per user if needed |
| Question bank list | Medium | Pagination + indexes | Redis cache public bank pages |
| Exam template public list | Medium | DB | CDN/cache short TTL |
| Session answer PUT | Hot during exam | DB only | No cache |
| SM-2 review POST | Hot | DB only | No cache |
| Media GET | Hot | R2 + browser cache | Cloudflare CDN |

### When to introduce Redis (F-14)

`REDIS_URL` exists but nothing uses it. **Do not** implement a cache “to use the setting.”

**Introduce Redis when any of:**

- Postgres CPU > 60% sustained from identical read queries
- Public bank list p95 > 200 ms after indexes
- Multi-instance rate limiting needed
- Phase 2 job queue chosen as Redis-backed

Until then: either remove `REDIS_URL` from Settings or mark `# reserved for Phase 2+` in config + `.env.example`.

Same for `GEMINI_API_KEY` / `OPENAI_API_KEY` — reserved for Phase 2 AI client (#8).

---

## Database scaling path

```
1. Vertical (Railway plan bump)           ← stay here through 100k DAU likely
2. Connection pooling (PgBouncer)         ← if connection errors / many workers
3. Read replica for analytics/dashboard   ← Phase 3 analytics heavy reads
4. Partition answer_records by time       ← if sessions explode
5. Shard by user_id                       ← only multi-million users
```

**Never shard before** aggregates + indexes + replica.

### SQL vs NoSQL

Keep **Postgres** as system of record. Reasons:

- Relational integrity for bank/session invariants
- Alembic migrations already invested
- Scale not yet limited by model flexibility

Optional later: OpenSearch for full-text bank search if `ILIKE` fails.

---

## Async / queues (scale building block)

Introduce a queue when:

| Workload | Why queue |
|----------|-----------|
| LLM question generation | 5–60s, retries, cost control |
| Bulk card import | Spiky CPU |
| PDF report | CPU + storage |
| Fanout notifications | Phase 3 reminders |

**Minimal design for Phase 2:**

```
API ─► job_queue (Postgres table or Redis) ─► worker ─► writes results
         │
         └─ client polls GET /jobs/{id} or SSE ticket (if revived carefully)
```

Prefer **Postgres job table** first (one less moving part) if QPS low; Redis if multi-worker high throughput.

---

## Frontend performance notes

- Full-bleed consoles already isolate scroll — good.
- Exam session should not refetch full bank; keep store scoped (already).
- Consider route-level code splitting (lazy routes already).
- Images: lazy-load; constrain card image sizes on upload later.
- Avoid N+1 API patterns in library views (batch where possible).

---

## Capacity milestones

| Milestone | Expected scale | Engineering focus |
|-----------|----------------|-------------------|
| v0.x now | < 1k DAU | Security + integrity |
| v1.0 | 10k DAU | Dashboard SQL, rate limits, observability |
| v1.x AI | 10–50k DAU | Queue, spend caps, caching bank |
| v2.0 social | 100k DAU | Replica, CDN media, gamification writes |

---

## Acceptance for Horizon B perf slice

- [ ] F-07 fixed with tests for aggregate correctness
- [ ] Config documents unused Redis/AI keys as reserved
- [ ] This plan’s scaling triggers linked from CLAUDE.md briefly

---

## Next

→ [07-frontend-quality.md](./07-frontend-quality.md)
