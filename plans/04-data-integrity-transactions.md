# 04 — Data Integrity & Transaction Boundaries (Deep Dive)

**Findings covered:** F-04, F-08  
**Horizon:** A (P1) — **after** security P0, **before** large feature work  
**Effort:** 2–3 days total (harness day + refactor day)

---

## Why this is structural

Question-bank invariants are documented and mostly enforced in happy paths:

- Answer records are the composition snapshot.
- Soft-delete preserves history.
- Answered options freeze.

Those rules assume **one atomic write** for “create session + N answer rows.” Today that is **two commits** in `create_session`, and similar dual ownership exists across services.

`guest_service.purge_guest_user` already states the correct rule: **“does not commit — caller owns the transaction boundary.”** Promote that to a project-wide convention.

---

## F-04 — Single commit owner

### Current pattern

```text
Request
  └─ get_db() yields session
       ├─ service method A → commit()
       ├─ service method B → commit()
       └─ get_db finally → commit() again
```

Problems:

1. Partial failure leaves inconsistent rows (orphan sessions, half-updated decks).
2. Nested commits make rollback at router level useless.
3. Tests override `get_db` without commit wrapper → **false confidence**.

### Target pattern

```text
Request
  └─ get_db() yields session
       ├─ service methods only flush() / add() / delete()
       ├─ need PK early? → await db.flush()
       └─ get_db on success → commit(); on error → rollback()
```

Jobs (guest cleanup) and CLI scripts own their own `session.commit()` explicitly at the top level — not buried in service helpers used by HTTP.

### Migration plan (mechanical but careful)

1. **Inventory** all `await db.commit()` / `await session.commit()` under `backend/app/services/` and `seed/`.
2. **Replace** HTTP-path commits with `flush()` where identity is needed; delete commits otherwise.
3. **Keep** commits in:
   - `get_db()`
   - `jobs/*` entrypoints
   - seed script when run **outside** request lifecycle (entrypoint one-shot)
4. **Review** multi-step methods:
   - `create_session` — one logical unit
   - `auth_service` guest upgrade — must stay atomic
   - `attach/reorder` composition — one unit
   - card reorder — one unit
5. **Explicit nested units:** if a true savepoint is needed, use `session.begin_nested()` and document why.

### create_session specific fix

```text
Before:
  insert ExamSession; commit
  insert N AnswerRecords; commit

After:
  insert ExamSession; flush  # get session.id
  insert N AnswerRecords
  return  # get_db commits once
```

On failure, no session row is visible to other requests.

### Risk & rollback

- Risk: code paths that assumed intermediate commit visibility mid-request (unlikely in this codebase).
- Rollback strategy: PR is pure backend; if issue found, revert PR (no migration).

### Acceptance

- [ ] Zero `commit()` in service methods invoked from routers (lint or grep gate).
- [ ] Crash injection / simulated error between session insert and answer inserts leaves **zero** orphan sessions (Postgres test).
- [ ] Existing pytest suite green after conftest still valid.
- [ ] Guest upgrade and composition mutations still pass.

---

## F-08 — Test harness that can see the truth

### Gaps today

| Gap | Effect |
|-----|--------|
| SQLite in-memory | FKs off by default; cascades not enforced |
| `postgresql.UUID` / JSON dialects | Subtle type differences |
| `get_db` override bare yield | Never tests real commit/rollback |
| No Postgres CI job | Cascades only fail in prod |

### Target testing pyramid

```
┌─────────────────────────────────────┐
│  Optional: FE contract smoke (node) │  existing verify-library-contracts
├─────────────────────────────────────┤
│  Postgres integration (slow job)    │  NEW — cascades, transactions, seed
├─────────────────────────────────────┤
│  SQLite unit/API tests (fast)       │  KEEP — majority of 70+ tests
└─────────────────────────────────────┘
```

### Postgres job options

| Option | Pros | Cons |
|--------|------|------|
| **testcontainers** | Isolated, CI-friendly | Docker required |
| **compose service `postgres` + `DATABASE_URL`** | Simple locally | Shared state if not careful |
| **GitHub Actions Postgres service** | Native CI | Local parity needs docs |

**Recommendation:** GitHub Actions service container + local `docker compose run` recipe; mark tests with `@pytest.mark.postgres`.

### Tests that must run on Postgres

1. Hard-delete question blocked / soft-delete keeps `AnswerRecord` resolvable.
2. Delete template removes links not questions.
3. `create_session` atomicity under forced error (use savepoint or monkeypatch after flush).
4. User delete cascades decks/cards; template SET NULL behavior per model.
5. Unique `seed_key` constraint.
6. Guest cleanup cascade paths that SQLite silently skips.

### conftest changes

**SQLite suite (default):**

- Keep fast path.
- Optionally enable `PRAGMA foreign_keys=ON` for partial improvement (still not full Postgres parity).

**Postgres suite:**

- Real `get_db` commit wrapper **or** explicit commit in fixtures that mirror production.
- Run Alembic `upgrade head` against empty DB, not only `create_all`.

### Acceptance

- [ ] `pytest -m "not postgres"` remains default fast path.
- [ ] `pytest -m postgres` documented; runs in CI on main/PR.
- [ ] At least one test fails on current main if run against multi-commit create_session with crash injection (proves harness value), then passes after F-04.

---

## Implementation order (critical)

```
Day 1: F-08 harness + 2–3 cascade tests green on Postgres
Day 2: F-04 strip commits + create_session atomicity
Day 3: Expand postgres tests; add ruff/grep CI check for service commits
```

**Do not** refactor transactions before the harness exists — you cannot see regressions.

---

## Convention snippet (add to CLAUDE.md after fix)

```markdown
## Transaction ownership

- `get_db()` is the sole commit point for HTTP requests.
- Services may `flush()` to obtain IDs; they must not `commit()` or `rollback()`.
- Background jobs open their own session and commit once at the end of the unit of work.
- Prefer one service call per mutation endpoint; multi-step workflows stay in one service method.
```

---

## Related integrity work (non-blocking)

| Item | Note |
|------|------|
| Tag filter in Python | OK until ~5k questions; plan JSONB later |
| `total_questions` sync helper | Keep COUNT-based sync after composition |
| Soft-delete filters | Bank lists only; session resolution includes archived |

---

## Next

→ [05-reliability-and-ops.md](./05-reliability-and-ops.md) for seed races, deploy topology, observability.
