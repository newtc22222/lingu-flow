# 03 — Security Hardening (Deep Dive)

**Findings covered:** F-01, F-02, F-03, F-05 (integrity angle), F-09  
**Horizon:** A (P0)  
**Effort:** ~0.5–1 day for P0; F-05 product decision may extend

---

## Threat model (pragmatic)

| Threat | Impact | Likelihood today | Mitigations |
|--------|--------|------------------|-------------|
| Forge JWT with known secret | Full account takeover | High if F-01 path used | Fix guard; rotate secrets; never commit secrets |
| Enumerate private exam UUID | Content theft, spoilers | Medium (UUIDs hard but shareable/leaked) | Visibility predicate on all reads |
| Read answer key mid-exam | Cheating / spoilers | High via API | Gate details on `completed` + ownership |
| JWT in URL (SSE) | Log/history leak | Low (endpoint unused) | Remove or ticket-based auth |
| Client-only exam timer | Inflated scores / practice abuse | High for “cert simulator” pitch | Server deadline or product honesty |
| Auth brute force | Account takeover | Medium | Rate limit (Horizon B) |

Not in scope here: XSS in markdown, R2 bucket policy audit, OAuth CSRF deep review (schedule separately if shipping enterprise).

---

## F-01 — Production JWT guard must always fire

### Problem

```python
# config.py validator (conceptual)
env = os.getenv("ENVIRONMENT", "development")  # ignores .env-loaded field
```

Pydantic loads `ENVIRONMENT=production` from `backend/.env`, but the validator still thinks “development” and accepts the hardcoded fallback secret that appears in repo + docker-compose.

### Fix design

1. In `JWT_SECRET` validator, use `info.data.get("ENVIRONMENT")` (field order already declares `ENVIRONMENT` first).
2. Keep process-env override semantics: if both set, Pydantic Settings merge rules already apply — do not reintroduce `os.getenv` for this check.
3. Tests:
   - **Existing:** `os.environ["ENVIRONMENT"]="production"` + empty/default secret → raises (keep).
   - **New:** temporary `.env` file with `ENVIRONMENT=production` and no `JWT_SECRET` / default secret → `Settings()` raises (covers F-01).
   - **New:** production + strong random secret → accepts.

### Ops follow-up

- Rotate production `JWT_SECRET` if any environment ever ran with the committed default.
- Ensure Railway dashboard shows real secret (not compose default).
- Optional: fail boot if secret length < 32 bytes in production.

### Acceptance

- [ ] Probe: Settings from `.env` production without strong secret fails boot.
- [ ] Documented deploy path still boots with real secret.
- [ ] No regression for local dev default secret when `ENVIRONMENT=development`.

---

## F-02 — Template visibility predicate

### Problem

| Endpoint | Auth | Visibility |
|----------|------|------------|
| `GET /api/exams/templates` | optional | Correct: public OR owned |
| `GET /api/exams/templates/{id}` | **none** | **None** |
| `GET /api/exams/templates/{id}/questions` | optional | **None** (only key redact) |

### Design

Introduce one helper next to `_owned_template_or_404`:

```text
_readable_template_or_404(db, template_id, user | None) -> ExamTemplate
  allow if template.is_public OR (user and template.user_id == user.id)
  else 404  # prefer 404 over 403 to avoid existence oracle
```

Apply to:

- `GET /templates/{id}`
- `GET /templates/{id}/questions`
- Any other by-id read that currently uses unfiltered `get_template_by_id`

**Composition mutations** already require ownership — verify no path mutates public built-ins (artifact noted historical hole; composition should already check).

### Acceptance

- [ ] Anon cannot read private template name/questions (404).
- [ ] Other user cannot read private template (404).
- [ ] Owner and public still 200.
- [ ] Answer key still withheld for non-owners on question list.

---

## F-03 — Session details answer-key policy

### Problem compound

1. `create_session` uses unfiltered template lookup → any user can start private exams (via F-02).
2. `GET .../sessions/{id}/details` returns full `QuestionResponse` including `correctAnswer` regardless of `status` and weak ownership story.

### Design

**A. create_session**

- Resolve template via `_readable_template_or_404`.
- Optionally: only allow session creation on public OR owned (same predicate).

**B. get_session_details**

- Require authenticated owner of the session (`session.user_id == current_user.id`) — return 404 otherwise.
- Map questions through `build_question_response` (or equivalent).
- **Answer key rule:**
  - Include `correctAnswer` / explanations **only if** `session.status == "completed"` (and caller is owner).
  - While `in-progress` / `abandoned`, return public-shaped questions (stem, options, media) without key.

**C. Schema**

- Prefer explicit DTO split if needed: `SessionQuestionLive` vs `SessionQuestionReview` to make the invariant type-level, not only runtime.

### Acceptance

- [ ] Probe: mid-exam details has **no** `correctAnswer`.
- [ ] Probe: post-finish details **has** key for owner.
- [ ] Probe: other user 404 on details.
- [ ] Probe: cannot create session on private non-owned exam.
- [ ] ExamResults UI still shows explanations after finish.

---

## F-05 — Exam timing (product + security)

### Current

- Client: `deadlineAt = Date.now() + minutes`.
- Server: stores `started_at`, `time_limit_minutes`; never enforces.
- `finish_session` can be called twice (overwrites `finished_at`); answers after finish correctly 400.

### Options

| Option | Pros | Cons |
|--------|------|------|
| **A. Honor system** (document as practice) | Zero work | Undercuts “proctor booth” marketing |
| **B. Soft enforce** — reject `finish` if now > started + limit + grace | Simple, good enough | Clock skew; offline tabs |
| **C. Hard enforce** — reject late `record_answer`; auto-finish job | Stronger | Needs background tick or lazy check on each write |
| **D. Signed server deadline** cookie/token | Tamper-resistant | More complexity |

**Recommendation:** **B + lazy C on answer/finish** for Horizon B:

```text
on record_answer / finish_session:
  if now > started_at + time_limit + 30s grace:
    auto-transition to completed (score what is answered) OR 400 with code EXAM_EXPIRED
  if status already completed: finish is idempotent no-op (return current score)
```

Product copy: “Server enforces time limit; refreshing does not extend the exam.”

### Acceptance

- [ ] Second finish is idempotent.
- [ ] Answer after wall-clock expiry rejected or auto-finished per chosen rule.
- [ ] FE shows consistent “time up” state from server error.

---

## F-09 — SSE endpoint

### Current

- Query-string JWT → logs/history risk.
- No token revalidation / user existence check.
- No frontend consumer.

### Decision

**Horizon A: delete** `/api/events` (router + tests + docs mentions) unless a committed design needs it within 30 days.

**If reintroduced later:**

1. Auth via short-lived SSE ticket (`POST /api/events/ticket` → 60s one-time token) **or** cookie session.
2. Publish real events (card reviewed, exam finished) via in-process bus first; Redis pub/sub only multi-instance.
3. Never put long-lived access JWT in query string.

---

## Additional security backlog (Horizon B)

| Item | Notes |
|------|-------|
| Rate limit login / register / guest | SlowAPI or reverse-proxy limits |
| Refresh tokens / shorter access TTL | 7-day access JWT is long; consider rotate |
| Security headers | CSP on Vercel; HSTS |
| Markdown XSS audit | `MarkdownRenderer` sanitize policy |
| R2 CORS / public ACL review | Presign only |
| Dependency audit | `npm audit` / `pip-audit` in CI |

---

## Implementation sequence

```
1. F-01 config + tests                          (minutes)
2. Visibility helper + wire F-02 routes         (1–2 h)
3. create_session + details F-03                (2–3 h)
4. Integration tests (pytest) for all probes    (2 h)
5. Delete F-09 SSE                              (30 m)
6. (Optional same PR) finish idempotency        (1 h)
```

Single security PR preferred so probes and fixes land together.

---

## Test matrix (must land with code)

| # | Case | Expected |
|---|------|----------|
| 1 | Production Settings from temp `.env` + weak secret | ValueError / boot fail |
| 2 | Anon GET private template | 404 |
| 3 | User B GET user A private template/questions | 404 |
| 4 | User B POST session on A’s private template | 404 |
| 5 | Owner mid-exam GET details | 200, no correctAnswer |
| 6 | Owner completed GET details | 200, with correctAnswer |
| 7 | User B GET A’s session details | 404 |
| 8 | Double finish | 200 idempotent or 409 once policy chosen |

---

## Next

→ [04-data-integrity-transactions.md](./04-data-integrity-transactions.md) — make session snapshot atomic and tests real.
