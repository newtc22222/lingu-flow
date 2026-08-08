# 09 — Implementation Backlog

Ordered work packages with effort, dependencies, and acceptance criteria. Each package should become one PR (or a small PR stack).

---

## Legend

| Field | Meaning |
|-------|---------|
| **Pri** | P0 (now) → P4 (later) |
| **Effort** | Eng-days (1 person) |
| **Deps** | Must complete first |
| **Artifact** | Finding IDs |

---

## GitHub issues

| ID | Issue |
|----|------:|
| A1 | [#44](https://github.com/newtc22222/lingu-flow/issues/44) |
| A2 | [#45](https://github.com/newtc22222/lingu-flow/issues/45) |
| A3 | [#46](https://github.com/newtc22222/lingu-flow/issues/46) |
| A4 | [#47](https://github.com/newtc22222/lingu-flow/issues/47) |
| A5 | [#48](https://github.com/newtc22222/lingu-flow/issues/48) |
| A6 | [#49](https://github.com/newtc22222/lingu-flow/issues/49) |
| A7 | [#50](https://github.com/newtc22222/lingu-flow/issues/50) |
| B1 | [#51](https://github.com/newtc22222/lingu-flow/issues/51) |
| B2 | [#52](https://github.com/newtc22222/lingu-flow/issues/52) |
| B3 | [#53](https://github.com/newtc22222/lingu-flow/issues/53) |
| B4 | [#54](https://github.com/newtc22222/lingu-flow/issues/54) |
| B5 | [#55](https://github.com/newtc22222/lingu-flow/issues/55) |
| B6 | [#56](https://github.com/newtc22222/lingu-flow/issues/56) |
| B7 | [#57](https://github.com/newtc22222/lingu-flow/issues/57) |
| B8 | [#58](https://github.com/newtc22222/lingu-flow/issues/58) |
| B9 | [#59](https://github.com/newtc22222/lingu-flow/issues/59) |

---

## Horizon A — Secure & correct

### A1. Fix production JWT environment guard · [#44](https://github.com/newtc22222/lingu-flow/issues/44)

| | |
|--|--|
| **Pri** | P0 |
| **Effort** | 0.1 d |
| **Artifact** | F-01 |
| **Files** | `backend/app/config.py`, `backend/tests/test_config.py` |

**Work**

- Read `ENVIRONMENT` from `info.data` in `JWT_SECRET` validator.
- Add temp-`.env` test proving production + weak secret fails.

**Accept**

- [ ] Test fails on old code, passes on new.
- [ ] Dev default secret still works in development.

---

### A2. Exam visibility + session answer-key policy

| | |
|--|--|
| **Pri** | P0 |
| **Effort** | 0.5 d |
| **Deps** | A1 optional |
| **Artifact** | F-02, F-03 |

**Work**

- Add `_readable_template_or_404`.
- Apply to template GET, questions GET, create_session template resolve.
- Session details: owner-only; keys only when `status == completed`; use `build_question_response`.
- Pytest coverage per matrix in plan 03.

**Accept**

- [ ] All 8 security matrix cases green.
- [ ] ExamResults still shows explanations after finish.

---

### A3. Remove unused SSE endpoint

| | |
|--|--|
| **Pri** | P0 |
| **Effort** | 0.1 d |
| **Artifact** | F-09 |

**Work**

- Remove `routers/events.py` registration, tests, docs mentions.
- Or gate behind explicit feature flag if product insists on keeping — default is delete.

**Accept**

- [ ] No `/api/events` in OpenAPI.
- [ ] No JWT query-string auth path remains.

---

### A4. Postgres integration test harness

| | |
|--|--|
| **Pri** | P1 |
| **Effort** | 1 d |
| **Artifact** | F-08 |
| **Deps** | — |

**Work**

- `@pytest.mark.postgres` + CI service / compose recipe.
- Run Alembic upgrade on empty DB.
- 3–5 cascade/transaction tests.

**Accept**

- [ ] Documented command for local Postgres tests.
- [ ] CI job (or documented manual) runs on PR.

---

### A5. Single transaction owner (strip service commits)

| | |
|--|--|
| **Pri** | P1 |
| **Effort** | 1–2 d |
| **Deps** | A4 |
| **Artifact** | F-04 |

**Work**

- Services `flush` only; `get_db` sole commit for HTTP.
- Fix `create_session` atomic snapshot.
- Grep/lint gate against service `commit()`.
- Postgres crash-injection test for orphan session.

**Accept**

- [ ] Full pytest green.
- [ ] Zero orphan sessions under simulated mid-create failure.
- [ ] CLAUDE.md transaction convention added.

---

### A6. Seed ownership (entrypoint + advisory lock)

| | |
|--|--|
| **Pri** | P1 |
| **Effort** | 0.5 d |
| **Artifact** | F-06 |

**Work**

- Move seed to entrypoint after migrate.
- Advisory lock inside seeder.
- Fail deploy on seed error in production.
- Remove lifespan seed (or no-op).

**Accept**

- [ ] Dual concurrent seed safe.
- [ ] API boot does not write seed.

---

### A7. Docs & agent skill accuracy

| | |
|--|--|
| **Pri** | P1 |
| **Effort** | 0.2 d |
| **Artifact** | F-10, F-11 |
| **Can parallel** | A1–A3 |

**Work**

- Refresh CLAUDE.md stale sections.
- Fix project-conventions skill test/lint claims.
- Declare primary deploy topology.
- Fix root `.env.example` if Mongo-era.

**Accept**

- [ ] New agent reading CLAUDE.md would not skip pytest/lint.
- [ ] Primary vs local deploy is unambiguous.

---

## Horizon B — Fast & operable

### B1. Dashboard SQL aggregates

| | |
|--|--|
| **Pri** | P2 |
| **Effort** | 0.5–1 d |
| **Artifact** | F-07 |

**Accept**

- [ ] No full card ORM load.
- [ ] FE contract preserved.
- [ ] Test with fixture of many cards.

---

### B2. Streak UTC consistency

| | |
|--|--|
| **Pri** | P2 |
| **Effort** | 0.2 d |
| **Artifact** | F-13 |
| **Deps** | B1 optional same PR |

**Accept**

- [ ] UTC day boundaries tested.

---

### B3. Exam server-side time enforcement

| | |
|--|--|
| **Pri** | P2 |
| **Effort** | 0.5 d |
| **Artifact** | F-05 |
| **Deps** | Product choice (soft enforce recommended) |

**Accept**

- [ ] Finish/answer respect wall clock + grace.
- [ ] Double finish idempotent.
- [ ] FE handles expiry error.

---

### B4. Compose healthchecks + ready endpoint

| | |
|--|--|
| **Pri** | P2 |
| **Effort** | 0.3 d |
| **Artifact** | F-11 |

**Accept**

- [ ] Cold `docker compose up` does not race-fail migrate.
- [ ] `/api/health/ready` checks DB.

---

### B5. Auth rate limiting

| | |
|--|--|
| **Pri** | P2 |
| **Effort** | 0.5 d |

**Accept**

- [ ] Login/register/guest limited per IP.
- [ ] 429 with clear body.

---

### B6. Frontend data-access convention + selective refactors

| | |
|--|--|
| **Pri** | P3 |
| **Effort** | 0.5 d docs + opportunistic refactors |
| **Artifact** | F-12 |

**Accept**

- [ ] Documented rule.
- [ ] At least dashboard extracted to clean module when next touched.

---

### B7. Config hygiene (reserved settings)

| | |
|--|--|
| **Pri** | P3 |
| **Effort** | 0.1 d |
| **Artifact** | F-14 |

**Accept**

- [ ] REDIS/AI keys commented as reserved or removed until used.

---

### B8. Observability baseline

| | |
|--|--|
| **Pri** | P3 |
| **Effort** | 0.5–1 d |

**Accept**

- [ ] Structured request logging.
- [ ] Optional Sentry hook.
- [ ] Error rate visible on host dashboard.

---

### B9. Frontend test bootstrap

| | |
|--|--|
| **Pri** | P3 |
| **Effort** | 1 d |

**Accept**

- [ ] Vitest runs in CI for pure units + one store test.

---

## Horizon C — Product (existing issues)

| Package | Issues | Deps |
|---------|--------|------|
| C1 AI client | #8 | A1–A6, B5 recommended |
| C2 Explainer | #10 | C1 |
| C3 Generator | #9 | C1, A5 |
| C4 Hints | #11 | C1, A2 |
| C5 Analytics | #13 | B1 |
| C6 Adaptive exam | #14 | A5, bank invariants |
| C7+ | #12, #15–#20 | per plan 08 |

---

## Suggested PR stack (first two weeks)

```
PR1  A1 + A2 + A3 + tests          security
PR2  A7                            docs/skills
PR3  A4                            postgres harness
PR4  A5                            transactions
PR5  A6                            seed ownership
PR6  B1 + B2                       dashboard + streak
PR7  B3 + B4 + B5                  exam time + compose + rate limit
```

---

## Definition of done (program)

Horizon A is **done** when:

1. Artifact critical findings F-01–F-04 closed with tests.
2. F-06 and F-09 closed.
3. F-08 harness exists and protects F-04.
4. Docs no longer lie about tests/deploy.

Horizon B is **done** when:

1. Dashboard scales with card volume.
2. Deploy story + healthchecks clear.
3. Basic abuse controls and observability exist.

Only then schedule Phase 2 AI as the main feature track.

---

## Appendix — Artifact source

- **URL:** https://claude.ai/code/artifact/3c990b70-7e97-42a2-9d3b-5c9e80751ff9  
- **Local scratch copy (session):**  
  `AppData/Local/Temp/claude/.../scratchpad/linguflow-architecture-review.html`  
- **Session:** `f3b02765-ab2f-49db-85b8-e5ef8843cd02`  
- **Branch at review:** `feat/flashcards-lobby @ d5a5e87` (findings still valid on `main` @ plan creation)
