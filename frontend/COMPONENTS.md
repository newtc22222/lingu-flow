# LinguFlow Component Inventory

Post-Step-3.5 state: documents the arcade design system's core UI primitives
after the shared-component extraction (`AppButton.vue`, and `ManageListShell.vue`
— since superseded by `KeyboardGridList.vue`, see below)
and the accompanying token additions (`--focus-ring-width`,
`--font-size-md-plus`, `--tracking-wider`). Priority order: Button, Input,
Modal/Dialog, the manage-list pattern, ExamHud, FlashCard, PixelFrame,
MarkdownRenderer.

**Phase 1.5 update.** The flat `src/components/` folder is gone — every
component now lives under `features/<domain>/` or `shared/components/`. The
exam trio moved and was renamed (`ExamHub.vue` → `features/exam/ExamHubView.vue`,
`ExamResults.vue` → `ExamResultsView.vue`, `ExamCreator.vue` →
`ExamCreatorView.vue`), and the orphaned `HelloWorld.vue`/`StudyDashboard.vue`
were deleted. Older file paths in the sections below refer to those pre-move
locations; the components themselves are unchanged unless noted. Five new
components landed this phase — `CardRow`, `McqPrompt`, `WrittenRecallPrompt`
(documented below), plus the `DeckDetailView`/`LearnView`/`MatchView` route
views that own them.

All user-facing copy is now routed through `vue-i18n` (`src/locales/{vi,en}.json`).
A component that renders text must take it from `t()` rather than hardcoding a
string — this includes prop defaults, which is why `FlashCard`'s eyebrow/hint
defaults became computed values instead of `withDefaults` literals.

---

## AppButton

`frontend/src/shared/components/AppButton.vue` — the extracted shared button, replacing 6+ independent `.btn-arcade`/`.btn-guest`/`.btn-edit`/`.btn-delete` definitions plus FlashcardsView's `.btn-fc` pair. `type`/`disabled` and any listener (`@click`) fall through to the root `<button>` automatically via Vue's attribute inheritance — no explicit `emits` declaration needed.

### Props

| Prop       | Type                                                         | Default     | Notes                                    |
| ---------- | ------------------------------------------------------------ | ----------- | ---------------------------------------- |
| `variant`  | `'primary' \| 'danger' \| 'secondary' \| 'edit' \| 'delete'` | `'primary'` | see table below                          |
| `type`     | `'button' \| 'submit' \| 'reset'`                            | `'button'`  | passed straight to the native `<button>` |
| `disabled` | `boolean`                                                    | `false`     |                                          |

### Variants

| Variant     | Was                          | Background                    | Text                    | Use case                                                     |
| ----------- | ---------------------------- | ----------------------------- | ----------------------- | ------------------------------------------------------------ |
| `primary`   | `.btn-arcade`, `.btn-fc.yes` | `var(--status-success)`       | `var(--text-on-accent)` | primary submit/confirm action                                |
| `danger`    | `.btn-fc.no`                 | `var(--status-danger)`        | `var(--text-on-accent)` | destructive/negative primary action (flashcard "don't know") |
| `secondary` | `.btn-guest`                 | transparent                   | `var(--text-secondary)` | cancel/back/secondary action                                 |
| `edit`      | `.btn-edit`                  | `var(--surface-panel-border)` | `var(--color-accent)`   | row-level edit action                                        |
| `delete`    | `.btn-delete`                | `var(--surface-panel-border)` | `var(--status-danger)`  | row-level destructive action                                 |

### States

| State         | Treatment                                                                                                                      |
| ------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| default       | variant-specific                                                                                                               |
| hover         | `secondary`/`edit`/`delete` only (`primary`/`danger` use press-shadow instead)                                                 |
| active        | `primary`/`danger` only — `transform: translateY(4px); box-shadow: none` (pressed-button effect)                               |
| disabled      | **new, uniform across all variants**: `opacity: 0.5; cursor: not-allowed; pointer-events: none`                                |
| focus-visible | `outline: var(--focus-ring-width) solid var(--color-focus-ring); outline-offset: 2px` — now defined **once**, in the component |

### Token usage

Fully tokenized — every variant uses `var(--space-*)`, `var(--font-size-*)`, `var(--tracking-*)`, `var(--focus-ring-width)`. No raw literals anywhere in the component.

### Normalizations made during extraction (visible deltas, not regressions — noted for spot-checking)

- **Disabled state is now uniform.** Before extraction, `.btn-arcade:disabled` existed in `ExamCreator.vue`/`AuthView.vue`/`QuestionCard.vue` (at inconsistent opacities: 0.4, 0.6, 0.5) but was **undefined** in `CardManagementView.vue`/`DeckManagementView.vue` and had no disabled state at all in `FlashcardsView.vue`/`ExamHub.vue`. All variants now share one `opacity: 0.5` disabled treatment. This is a net accessibility/consistency improvement, but the exact opacity changed in 2 of the 3 files that previously had a custom value.
- **Focus-visible outline now exists on every button, including 2 that never had one.** `QuestionCard.vue`'s submit button and `FlashcardsView.vue`'s yes/no buttons had no `:focus-visible` rule defined anywhere before extraction — a real pre-existing a11y gap, now fixed as a side effect of centralizing the style.
- **`primary`/`danger` sizing is normalized.** Before extraction, `.btn-arcade` padding/font-size varied per file (`var(--space-6) var(--space-10)` in most, `var(--space-7)` all-around in `ExamCreator.vue`/`AuthView.vue`, `var(--space-8) 28px` in `QuestionCard.vue`) and `.btn-fc` used yet another combination (`var(--space-7) var(--space-9)`, `--font-size-base`). All now render at the canonical `.btn-arcade` dimensions (`var(--space-6) var(--space-10)`, `--font-size-md`) — a ~1-4px visual shift on 5 of the 8 migrated call sites. Layout-specific overrides (full-width buttons, extra margin) were preserved via a supplementary class on the `AppButton` usage (e.g. `AuthView.vue`'s `.auth-submit-btn`/`.auth-guest-btn`, `ExamCreator.vue`'s existing `.full-width`) rather than baked into the component.

### Not folded into AppButton (deliberately left as local one-offs)

`ExamCreator.vue`'s `.btn-remove` (small text-only "remove question" link) and `.btn-add-question` (full-width dashed "add question" affordance), and `QuestionCard.vue`'s `.answer-key` toggle chips are structurally distinct, single-use affordances — extracting them would add variant surface area nobody else needs. Not touched.

### Consumers

`features/exam/ExamCreatorView.vue` (×2), `ExamHubView.vue`, `ExamResultsView.vue` (×2 — a retake button was added alongside back-to-exams), `features/exam/components/QuestionCard.vue`, `features/auth/AuthView.vue` (×2), `features/dashboard/DashboardView.vue` (×2), `features/flashcards/FlashcardsView.vue` (×2, `primary`/`danger`), `features/library/DeckManagementView.vue` and `DeckDetailView.vue` (via themselves + `KeyboardGridList` + `ConsoleHeader` + form components).

Phase 1.5 additions: `features/library/DeckDetailView.vue`, `features/flashcards/LearnView.vue`, `MatchView.vue`, and `components/McqPrompt.vue` (which renders one `AppButton` per option).

---

## Input

Unchanged from the pre-extraction audit — still a real shared CSS-only pattern in `tokens.css` (`.arcade-field`/`.arcade-label`/`.arcade-input`), not a component. Not in scope for Step 3.5 (only Button and the manage-list pattern were extracted).

### Token usage update

`.arcade-input`'s previously-untokenized `font-size: 14px` is now `var(--font-size-md-plus)` (see token-addition summary below).

**Still flagged, unresolved:** no component exists to extract into; disabled/error states are still undefined anywhere in the codebase.

---

## Modal / Dialog

`frontend/src/shared/components/ConfirmDialog.vue` — shared accessible modal primitive for action confirmation (e.g. logout warning, destructive prompts). Built with `PixelFrame`, `AppButton`, Teleport overlay, keyboard Escape handler, and focus ring management.

### Props

| Prop          | Type                    | Default    | Purpose                                                               |
| ------------- | ----------------------- | ---------- | --------------------------------------------------------------------- |
| `isOpen`      | `boolean`               | (required) | Controls modal visibility (`v-model:isOpen`)                          |
| `title`       | `string`                | (required) | Header title text                                                     |
| `message`     | `string`                | (required) | Body explanation text                                                 |
| `confirmText` | `string`                | `''`       | Confirm button label (falls back to `common.delete` or `common.save`) |
| `cancelText`  | `string`                | `''`       | Cancel button label (falls back to `common.cancel`)                   |
| `variant`     | `'primary' \| 'danger'` | `'danger'` | Confirm button variant and `PixelFrame` border styling                |

### Emits

| Event           | Payload   | Purpose                                                      |
| --------------- | --------- | ------------------------------------------------------------ |
| `update:isOpen` | `boolean` | Two-way binding for dialog open state                        |
| `confirm`       | —         | Emitted when user clicks confirm button                      |
| `cancel`        | —         | Emitted when user clicks cancel, backdrop, or presses Escape |

### Consumers

`App.vue` (logout warning), `DeckManagementView.vue` (delete deck), `DeckDetailView.vue` (delete card), `QuestionBankView.vue` (delete question).

---

## KeyboardGridList

`frontend/src/shared/components/KeyboardGridList.vue` — generic (`<script setup generic="T extends { id: string }">`) keyboard-navigable list. **Replaced `ManageListShell.vue`**, which was deleted once the library views moved to the full-width console layout and its last consumers went away (`QuestionBankView` had already stopped using it).

The split honours `ManageListShell`'s own tripwire (_"a fifth opt-in flag means split into chrome + a thin wrapper"_): the console needed the list to own `overflow-y: auto`, which would have been that flag. Header, count badge and form moved out to `ConsoleHeader` and the form bay; this component renders one grid and nothing else.

### Props

| Prop            | Type                                | Purpose                                                                                                      |
| --------------- | ----------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| `rows`          | `T[]`                               | the list to render                                                                                           |
| `isLoading`     | `boolean`                           | gates loading-text vs. list/empty rendering                                                                  |
| `loadingText`   | `string`                            | shown while `isLoading`                                                                                      |
| `emptyText`     | `string`                            | shown when `rows.length === 0`                                                                               |
| `listLabel`     | `string`                            | `aria-label` on the grid                                                                                     |
| `activeIndex`   | `number`                            | which row holds the tab stop (controlled by the parent's `useRovingList`). Default `-1`                      |
| `canModify`     | `(item: T) => boolean` _(optional)_ | per-row guard; return false to disable that row's edit/delete. Used to freeze the synthetic Unfiled row      |
| `draggableRows` | `boolean`                           | Default `false`. When true each `<li>` is `draggable` and emits drag lifecycle events. Parent owns the array |

ARIA is always on (grid/row/gridcell + roving tabindex) — it is no longer opt-in, because a list that is not keyboard-navigable has no reason to use this component.

### Emits

| Event           | Payload            | Purpose                                                      |
| --------------- | ------------------ | ------------------------------------------------------------ |
| `edit`          | `T` (full item)    | parent opens its own edit form with the item                 |
| `delete`        | `string` (id)      | parent runs its own ConfirmDialog + API call                 |
| `row-activate`  | `(item: T, index)` | double-click / activate (Enter handled by parent composable) |
| `row-focus`     | `index`            | row received focus or click — sync roving index              |
| `row-dragstart` | `index`            | drag started on a draggable row                              |
| `row-dragenter` | `index`            | drag entered another row (live reorder preview)              |
| `row-dragend`   | —                  | drag finished                                                |

### Slots

| Slot  | Scope                        | Purpose                                                  |
| ----- | ---------------------------- | -------------------------------------------------------- |
| `row` | `{ item: T, index: number }` | the row's info content (left of the edit/delete buttons) |

### Scroll containment

`.grid-list-wrap` is `flex: 1 1 auto; min-height: 0; overflow-y: auto`. Basis `auto` (not `0`) is deliberate: inside a height-constrained console bay it shrinks and scrolls; in normal document flow (mobile, where the console model is off) it takes its content height instead of collapsing to `0px`.

The focus ring uses `outline-offset: -2px` so it draws _inside_ the row and is not clipped by the scroll container on the first/last row.

### Consumers

`DeckManagementView.vue` (rack), `DeckDetailView.vue` (workspace).

---

## ConsoleHeader

`frontend/src/features/library/components/ConsoleHeader.vue` — the console top bar: optional back button, title, optional count badge, and an `#actions` slot. Props: `title`, `backLabel?` (omit → no back button), `count?`, `countLabel?` (a negative `count` hides the badge, used while loading). Emits `back`.

Feature-private. `QuestionBankView`'s own title+count header is the obvious third consumer — fold it in and promote to `shared/` the next time that file is touched.

---

## ModalShell

`frontend/src/shared/components/ModalShell.vue` — overlay + cabinet frame shared by every modal. Owns Teleport, backdrop, `Escape`, body scroll lock, click-outside, and a **real focus trap**: initial focus in (falling back to the dialog container when there are no focusable children, as in the hotkeys legend), Tab/Shift+Tab cycling, and focus restored to the trigger on close. Props: `isOpen`, `title`, `variant?` (`primary`|`danger`, drives the frame ring). Emits `update:isOpen`, `close`. Slots: default, `footer`.

Consumers: `ConfirmDialog.vue`, `HotkeysDialog.vue`. This closes the previously-flagged "ConfirmDialog has no focus trap and no autofocus" issue for every dialog at once.

---

## HotkeysDialog

`frontend/src/features/library/components/HotkeysDialog.vue` — the console's legend plate. Props: `isOpen`, `title`, `groups: { label, items, note? }[]`.

Not a static cheat sheet: callers build `groups` from current state, so the ORDER group can arrive **muted with a `note`** explaining why its keys are unavailable (Unfiled cards can't be reordered; a search filter is active) instead of silently disappearing. Opened by the header button or `?`; the parent must include it in `isBlocked` so row shortcuts stay inert behind it.

---

## QuestionFilters

`frontend/src/shared/components/QuestionFilters.vue` — exam-type / part / difficulty / tag / search filter bar for the question bank.

**Lives in `shared/`, not in `features/question-bank/`.** Issue #33 specified the feature-private path, but the exam composer consumes it too, and `ui-guidelines.md` forbids cross-feature imports ("if a feature-private component gains a second feature's consumer, promote it to `shared/components/`"). It was placed here from the start rather than moved a PR later.

Controlled via `v-model` on a `QuestionFilterState`; emits `reset`. Part and tag options come from the server (`GET /api/questions/{parts,tags}`) rather than a hardcoded list, because `part` is free-form.

### Consumers

`features/question-bank/QuestionBankView.vue`, `features/exam/ExamComposerView.vue`.

---

## QuestionForm

`frontend/src/features/question-bank/components/QuestionForm.vue` — create/edit form for a bank question (text, passage, passage group, 4 options, correct answer, explanation, difficulty, exam type, part, tags).

The four option inputs hold **bare** text. The stored `"A. "` prefix is stripped on load and re-applied on submit via `@/utils/options`, so the user never edits a letter they can't meaningfully change. That helper re-derives the letter from the index, so reordering options can't leave a stale label; the backend normalizes identically.

Prop `framed` (default `true`): wraps in `PixelFrame`. Pass `framed={false}` when a parent bay owns the frame (Question Bank dual-bay console).

Used both standalone (bank, unframed inside Compose bay) and inline inside the composer's create-new flow (framed).

## Question Bank console layout

`QuestionBankView.vue` is a **full-bleed, full-width** operator console: **left** COMPOSE form (amber), **right** SCAN filters + RESULTS list stacked. Form and list scroll independently inside the viewport. Route sets `meta.fullBleed`. Delete uses `ConfirmDialog`.

## Library console layout

`DeckManagementView.vue` (rack) and `DeckDetailView.vue` (workspace) follow the same console pattern, deliberately reusing the bank's conventions rather than inventing parallel ones: `minmax(0, 2fr) minmax(0, 3fr)` split, amber ring on the left form bay, `font-label` section labels, independently scrolling panes. Routes set `meta.fullBleed`.

Two deliberate differences from the bank:

- **The console model is a `@media (min-width: 768px)` opt-in.** Below that the bays stack and the page scrolls normally. Pinning the viewport on a phone leaves the list fighting the form for ~90px of height and rendering at `0px` — measured, not theorised.
- **The rack's left bay hugs its content** (`align-items: start`) while the workspace's fills the column. The deck form is two fields; stretching it would recreate the empty space the full-width layout exists to remove.

---

## ExamQuestionRow

`frontend/src/features/exam/components/ExamQuestionRow.vue` — one draggable question in an exam's composition. Same parent-owns-the-array split as `CardRow` (below): emits `dragstart`/`dragenter`/`dragend` and never reorders itself.

Its destructive action is **detach**, labelled "remove from exam" — the question survives in the bank and in any other exam using it. This wording is load-bearing: the bank's own delete is one screen away and means something materially different.

---

## CardRow

`frontend/src/features/library/components/CardRow.vue` — **row content only** for a card inside `KeyboardGridList` (deck workspace). Renders handle glyph, zero-padded index, optional ▲/▼ reorder controls, term/definition cells, and thumbnail. The list owns the `<li>`, drag listeners, and focus ring.

### Props

| Prop            | Type       | Purpose                                                     |
| --------------- | ---------- | ----------------------------------------------------------- |
| `card`          | `DeckCard` | the card to render (see `features/library/types.ts`)        |
| `index`         | `number`   | zero-based position, displayed as zero-padded `01`/`02`/…   |
| `isDragging`    | `boolean`  | dims the row while it's the one being dragged               |
| `isReorderable` | `boolean`  | when false, hides handle and ▲/▼ (Unfiled / filtered lists) |

### Emits

`move-up`, `move-down` — parent reorders. **The component deliberately does not reorder anything itself.**

---

## CardForm

`frontend/src/features/library/components/CardForm.vue` — create/edit form for a card with live `MarkdownRenderer` preview. Props: `card`, `decks`, `defaultDeckId`, `isSaving`, `error`, `showDeckSelect?`. Emits `submit(payload)` / `cancel`. Exposes `focusFirstField()` for `N`/`E` shortcuts. Reset deck select to `defaultDeckId` on create so a card made inside a deck lands in that deck.

## DeckForm

`frontend/src/features/library/components/DeckForm.vue` — create/edit form for a deck (name + description). Props: `deck`, `isSaving`, `error`. Emits `submit` / `cancel`. Exposes `focusFirstField()`.

## KeycapLegend

`frontend/src/features/library/components/KeycapLegend.vue` — keyboard shortcut display. Props: `items: KeycapItem[]` (`{ keys: string[]; label: string }`), `legendLabel` (group accessible name; not named `ariaLabel` because Vue treats `aria-*` specially on component props), `layout?: 'strip' | 'panel'`, `muted?: boolean`. Contains **no** key values or copy of its own — callers pass literal glyphs and already-translated labels. Caps use `font-label`; labels use `font-body`.

`layout="strip"` (default) is the inline row, hidden below 768px. `layout="panel"` is the form used inside `HotkeysDialog`: always visible at every width — that width gate is precisely why the modal replaced the always-on strip in the library — and laid out as a wrapping two-column grid. `muted` dims the caps for a group whose keys are unavailable in the current context.

## useRovingList

`frontend/src/features/library/composables/useRovingList.ts` — roving-focus key handler for library lists (arrow navigate, Home/End/PgUp/PgDn, cell drill, Enter/E/N/Del/`/`/S, Alt+arrows, Escape ladder, IME guard). Feature-private; promote to `shared/composables/` when a second feature imports it.

---

## McqPrompt / WrittenRecallPrompt

`frontend/src/features/flashcards/components/` — the two question types in Learn mode.

`McqPrompt` renders the card front plus four `AppButton` options, recolouring them to `primary` (correct) / `danger` (the user's wrong pick) once `selected` is non-null. Distractors are chosen by the parent, not here.

`WrittenRecallPrompt` renders a single text input that auto-focuses and clears on each new prompt, so a round is fully keyboard-playable. Its submit button doubles as "check" then "next", driven by the `verdict` prop.

Both are presentational — neither calls the API, and neither knows about SM-2. Grading lives in `LearnView`.

---

## ExamHud

`features/exam/components/ExamHud.vue` — live-booth chrome: exam title, CRT time bar (scan-line amber → red under 20%), answered/total, and **SUBMIT EXAM**. Lives/hearts were removed in Phase 1.5 (no API support).

## ExamAnswerSheet

`features/exam/components/ExamAnswerSheet.vue` — signature answer-sheet map (`01…N`). Current / filled / empty states; emits `select(index)` to `examStore.goToQuestion`.

## Exam flows (proctored CRT booth)

| Surface          | Route                          | Notes                                                                                                        |
| ---------------- | ------------------------------ | ------------------------------------------------------------------------------------------------------------ |
| Lobby            | `/exams` fullBleed             | Catalog + history; **TAKE** → session briefing; **EDIT** when `!isPublic`                                    |
| Briefing → booth | `/exams/session/:id` fullBleed | Loads template meta **without** creating a session until START; then HUD + split passage/stem + answer sheet |
| Report           | `/exams/results/:id` fullBleed | Score hero + scrollable review; RETAKE → briefing again                                                      |

---

## FlashCard

Not touched by Step 3.5 (it doesn't use any button pattern; its flip-toggle is a `role="button"` div, not a `<button>`, so it was never a candidate for `AppButton`). Still among the best-tokenized components alongside `PixelFrame`.

**Phase 1.5 change:** `frontEyebrow`/`backEyebrow`/`hint` were `withDefaults` literals holding hardcoded Vietnamese. They are now plain optional props resolved through `computed` + `t()`, so the defaults follow the active locale while callers can still override them.

---

## PixelFrame

Unchanged. Still the model example — full JSDoc, clean token usage, no flags.

---

## MarkdownRenderer

Unchanged. Still at `shared/components/MarkdownRenderer.vue` (relocated in the earlier prep commit). `rgba(255,255,255,0.1)` on `:deep(code)` remains a deliberate local literal per your standing instruction.

---

## AppFooter

`frontend/src/shared/components/AppFooter.vue` — shared arcade footer component rendering brand indicator (`LINGU FLOW - 1.0.0`) and footer navigation links (`PROTOCOL`, `DOCUMENTATION`, `SUPPORT`). Rendered at the bottom of the viewport shell in `App.vue` for all authenticated application routes.

### Consumers

`App.vue`.

---

## Token additions this round

| Token                 | Value  | Applied to (file:line)                                                                                                                                                                                                                                                                                                                                                                                                                         |
| --------------------- | ------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `--focus-ring-width`  | `2px`  | `ExamCreator.vue:621`, `ExamHub.vue:519,523`, `ExamResults.vue:617`, `AuthView.vue:305`, `FlashCard.vue:76`, `CardManagementView.vue:295` (`.arcade-input:focus-visible`), `DeckManagementView.vue:181` (`.arcade-input:focus-visible`) — line numbers as of the post-extraction file state; plus baked into `AppButton.vue` itself (all 8 button consumers inherit it for free instead of each declaring their own `outline: 2px solid` rule) |
| `--font-size-md-plus` | `14px` | `ExamHud.vue:69` (`.hud-lives`), `QuestionCard.vue:76` (`.q-passage`), `CardManagementView.vue` (`.card-row-text`), `tokens.css` (`.arcade-input`) — **4 sites, not the 3 originally estimated**; `QuestionCard.vue`'s `.q-passage` (exam reading-passage text) was missed in the original token-extraction audit and only surfaced when re-grepping for this token                                                                            |
| `--tracking-wider`    | `3px`  | `ExamHud.vue:71` (`.hud-lives`) — the only occurrence in the codebase                                                                                                                                                                                                                                                                                                                                                                          |

## Verification

`vue-tsc -b --noEmit` and `vite build` both run clean after every stage of this round (token additions, `AppButton` extraction + 8-file migration, `ManageListShell` extraction + 2-file migration).

**Phase 1.5 re-verification:** `npm run build` (vue-tsc + vite), `npm run lint:style`, and `npm run lint:js` all pass, and the backend suite is 46 green (`pytest`). One lint fix was needed as a direct result of the file moves: `.stylelintrc.json`'s override exempting `ExamCreator.vue`'s two documented `.btn-*` selectors still pointed at `src/components/ExamCreator.vue`, so those selectors started failing `selector-disallowed-list` once the file moved. The override now targets `src/features/exam/ExamCreatorView.vue`. Worth remembering: **path-scoped lint overrides do not follow renames**, so check `.stylelintrc.json` and `eslint.config.js` whenever a component moves.

## Cross-cutting flags resolved this round

The 3 flags raised at the end of the previous `COMPONENTS.md` pass are now closed:

1. ~~`outline: 2px solid` repeated raw~~ → `--focus-ring-width`, now centralized in `AppButton` for its 8 consumers and tokenized everywhere else it still appears locally (`Input`, `FlashCard`).
2. ~~`font-size: 14px` in 3 unrelated components~~ → `--font-size-md-plus`, applied to the (actually 4) real sites.
3. ~~Button duplication~~ → `AppButton.vue`, 8 call sites migrated, 0 remaining local `.btn-arcade`/`.btn-guest`/`.btn-edit`/`.btn-delete`/`.btn-fc` definitions anywhere in `frontend/src`.

## New flags from this round

- The three visual normalizations documented above (`AppButton` disabled-state/sizing, `ManageListShell` row alignment) are deliberate but real deltas from the pre-extraction pixel-exact appearance — worth a manual visual pass before treating this as done, since no visual regression testing tooling exists in this project (per CLAUDE.md, no test suite exists yet for the frontend).
- `ExamCreator.vue`'s `.btn-remove`/`.btn-add-question` and `QuestionCard.vue`'s `.answer-key` remain un-extracted, single-use, un-tokenized-beyond-existing button-adjacent patterns — not part of this round's scope, flagged for a future pass if they ever gain a second consumer.
