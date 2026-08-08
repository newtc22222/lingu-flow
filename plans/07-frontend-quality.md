# 07 — Frontend Quality & Consistency

**Findings covered:** F-12, F-13, F-10 (skill accuracy), FE test gap from CLAUDE.md  
**Horizon:** B  
**Effort:** 1–2 days conventions + streak; longer for test bootstrap

---

## Context

Frontend restructure (Phase 1.5) and console redesigns (library, question bank, exam booth, flashcards lobby) left the **product UI strong** and the **data-access story inconsistent**. There is still **no vitest/jest suite**; gates are `vue-tsc`, ESLint, stylelint, Prettier, production build.

---

## F-12 — One data-access convention

### Current triad

| Pattern | Used by | Shape |
|---------|---------|-------|
| Pinia store actions | exam, question-bank, auth | Shared state + API |
| Feature `api.ts` module | library | Thin functions, local view state |
| Inline `apiFetch` in views | dashboard, flashcards, profile | Fast but scatters contracts |

### Decision (recommended)

```text
1. apiFetch is the only HTTP primitive (except public auth pre-token).
2. If state is shared across routes/components → Pinia store in features/<x>/store/
3. If state is single-view → composable or feature api.ts called from the view
4. Never raw fetch with hand-rolled Authorization (except AuthView before token exists)
```

### Migration

- **Do not** big-bang rewrite all views.
- **Enforce for new code** via vue-guide skill + PR checklist.
- When touching dashboard/flashcards/profile substantially, extract `features/<x>/api.ts` or store.

### Acceptance

- [ ] Convention written in `CLAUDE.md` / vue-guide skill.
- [ ] New feature PRs follow the rule.
- [ ] Optional: ESLint comment/docs only (no custom rule required).

---

## F-13 — Streak date consistency

### Problem

Dashboard streak compares UTC `card.updated_at.date()` with `date.today()` (server local). For UTC+7 learners, early-morning study can land on “yesterday” UTC and break streaks.

### Fix

1. Compute “today” as `datetime.now(timezone.utc).date()` everywhere for streak.
2. Optionally later: store `user.timezone` in settings and compute local days — **product decision**.
3. Unit-test with fixed freezegun/clock around midnight UTC.

### Acceptance

- [ ] All streak math uses UTC (or documented user TZ).
- [ ] Test covers boundary around UTC midnight.

---

## UX / design system (keep winning)

Already strong — **do not regress**:

- Tokens only (`tokens.css` + stylelint)
- `AppButton`, `PixelFrame`, `ModalShell`, `KeyboardGridList`
- `font-pixel` never for Vietnamese body copy
- Full-bleed consoles for library/bank; align remaining document layouts only if product asks

### Open FE polish (from recent plans, not artifact)

| Item | Note |
|------|------|
| Fold QuestionBank header into `ConsoleHeader` | Optional consistency |
| Hotkeys modal focus trap | ModalShell should own this |
| Exam client timer vs server | Coordinated with F-05 |

---

## Frontend testing bootstrap (recommended path)

No need for 100% coverage. Prioritize risk:

### Phase FE-T1 (half day)

- Add Vitest + Vue Test Utils (or minimal Vitest for pure TS).
- Test pure helpers: `utils/options.ts`, streak pure function (extract from service if duplicated), SM-2 mapping if any FE side.

### Phase FE-T2 (1 day)

- Store tests: `examStore` finish error handling, timer cleanup on unmount.
- `apiFetch` 401 redirect behavior (jsdom mock).

### Phase FE-T3 (later)

- Playwright smoke: login guest → create deck → review one card → start public exam → finish.
- Run on CI nightly or pre-release.

### Contract

Keep/expand `frontend/scripts/verify-library-contracts.mjs` style checks for critical JSON shapes if valuable.

---

## i18n hygiene

- Every new string in **both** `en.json` and `vi.json`.
- Prop defaults via `t()` where user-visible.
- Spot-check pixel font on Vietnamese screens after large UI PRs.

---

## Error handling UX

Today many failures fail soft into empty UI or 0% scores (historical contract bugs). Convention:

```text
if (!res.ok) → surface toast/banner with t('errors.generic') + log status
never set phase='finished' without successful finish payload
```

Audit remaining `?? 0` / `?? []` on exam/dashboard paths when touching those files.

---

## Docs skill updates (F-10 FE side)

Update vue-guide / project-conventions:

- Features folder is the norm (not mid-migration empty state).
- Lint/test gates exist.
- Link to this plan’s data-access rule.

---

## Next

→ [08-product-roadmap.md](./08-product-roadmap.md) — Phase 2–5 gated by foundation.
