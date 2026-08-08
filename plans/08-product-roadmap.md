# 08 — Product Roadmap (Phases 2–5) with System-Design Gates

Open GitHub issues already track product work. This document **does not replace** those issues; it sequences them against foundation work and adds capacity/abuse constraints so AI and social features do not re-break integrity.

---

## Gate: Foundation first

| Gate | Required before |
|------|-----------------|
| Horizon A security (F-01–F-03) | Any public launch push; any AI that reads private exams |
| Horizon A integrity (F-04, F-08) | Any multi-step AI write (generate + attach questions) |
| Horizon A ops (F-06) | Replicas > 1 or multi-worker |
| Horizon B rate limits | Guest + AI endpoints public |
| Spend budget + job queue design | Phase 2 AI ship |

**Do not** start Phase 2 implementation until F-01–F-04 and F-06 are closed (or consciously waived with written risk).

---

## Phase 2 — AI features (issues #8–#11)

| Issue | Title | System-design notes |
|-------|-------|---------------------|
| #8 | Provider-agnostic AI client | Single interface; timeout; no secrets in FE; map to `GEMINI_API_KEY` / `OPENAI_API_KEY` |
| #9 | AI question generator | **Async job**; write to bank as draft; human confirm before attach; rate limit per user/day |
| #10 | Grammar & vocab explainer | Cache explanations by `(question_id, locale)` to control cost; never leak keys in prompts |
| #11 | Smart hints in ExamRoom | Hints must **not** include correct answer; log hint usage for analytics later |

### High-level AI architecture

```
Vue ──POST /api/ai/...──► FastAPI
                            │
                            ├─ validate auth + quota
                            ├─ enqueue job (Postgres/Redis)
                            └─ 202 { jobId }

Worker ──provider client──► OpenAI/Gemini/…
   │
   └─ store result ──► client polls or future SSE ticket
```

### Non-functional for Phase 2

| NFR | Target |
|-----|--------|
| Cost cap | Soft daily $ limit per env; hard per-user request cap |
| Latency | Async for generation; stream for explain if UX needs |
| Safety | Prompt injection: treat user content as data; no tool exfil |
| Privacy | Do not send other users’ private cards to model |

### Capacity sketch (10k DAU, 5% use AI daily, 3 calls)

```
AI calls/day ≈ 10_000 × 0.05 × 3 = 1_500
Avg QPS ≈ 0.02  (bursty evenings)
```

Bottleneck is **provider rate limits and $**, not CPU — design quotas first.

---

## Phase 3 — Adaptive learning & analytics (#12–#16)

| Issue | Title | Design notes |
|-------|-------|--------------|
| #12 | AI flashcards from text | Same job pipeline as #9; bulk card insert transaction (F-04 pattern) |
| #13 | User analytics engine | **Read models** / nightly aggregates; do not scan raw cards on dashboard (extends F-07) |
| #14 | Adaptive exam mode | Select from bank by tags/difficulty; freeze selection in AnswerRecords at start |
| #15 | Personalized study plan | Derived from SRS + weak tags; store plan snapshots |
| #16 | PDF progress reports | Worker + R2 storage; time-limited download URL |

### Analytics store

Prefer:

1. Postgres materialized views / summary tables first.
2. Warehouse only if exporting multi-tenant BI later.

Adaptive exams must respect bank invariants (snapshot order, no live template rewrite).

---

## Phase 4 — Social & gamification (#17–#18)

| Issue | Title | Design notes |
|-------|-------|--------------|
| #17 | Community exam & deck library | Visibility model expands (public/unlisted/private); clone-on-fork; license/report abuse |
| #18 | Achievements, badges, leaderboard | Write-heavy streaks; leaderboard = periodic recompute or Redis sorted set |

**AuthZ complexity jumps here** — complete F-02 style visibility framework before community publish.

Leaderboards: accept short lag (eventual); never block study writes on rank updates.

---

## Phase 5 — Listening / writing (#19–#20)

| Issue | Title | Design notes |
|-------|-------|--------------|
| #19 | Listening simulator (TTS) | Audio assets on R2; player UI; parts with image+audio; bandwidth/CDN |
| #20 | AI writing grader | Long-running jobs; rubric storage; human appeal path optional |

Media pipeline:

```
Upload/TTS ─► R2 ─► presigned GET ─► ExamView player
```

Listening sessions still freeze question order in `AnswerRecord`.

---

## Cross-cutting product decisions to lock early

1. **Exam honesty level** — practice honor system vs server-enforced timer (F-05).
2. **Timezone for streaks** — UTC vs user setting (F-13).
3. **Guest retention** — already 7 days; AI access for guests? (recommend: registered only).
4. **Content moderation** — required before community (#17).
5. **Primary deploy** — Vercel+Railway (F-11).

---

## Suggested calendar (indicative)

```
Week 1–2   Horizon A security + integrity + ops
Week 3     Horizon B dashboard + docs + rate limits
Week 4–6   Phase 2 #8 + #10 (explain) then #9/#11
Month 3    Phase 3 analytics foundation (#13) + adaptive (#14)
Month 4+   Phase 4/5 as demand warrants
```

Adjust freely; **do not** parallelize Phase 2 with F-04 rewrite on the same branch without coordination.

---

## Tracking

```bash
gh issue list --state open --label phase-2
gh issue list --state open --label phase-3
# trust labels over titles when they disagree
```

Create new issues only for **foundation findings** (F-01–F-14) if you want GitHub tracking — product features already exist.

---

## Next

→ [09-implementation-backlog.md](./09-implementation-backlog.md) for executable tickets.
