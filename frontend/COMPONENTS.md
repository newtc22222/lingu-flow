# LinguFlow Component Inventory

Post-Step-3.5 state: documents the arcade design system's core UI primitives
after the shared-component extraction (`AppButton.vue`, `ManageListShell.vue`)
and the accompanying token additions (`--focus-ring-width`,
`--font-size-md-plus`, `--tracking-wider`). Priority order: Button, Input,
Modal/Dialog, the manage-list pattern, ExamHud, FlashCard, PixelFrame,
MarkdownRenderer.

---

## AppButton

`frontend/src/shared/components/AppButton.vue` — the extracted shared button, replacing 6+ independent `.btn-arcade`/`.btn-guest`/`.btn-edit`/`.btn-delete` definitions plus FlashcardsView's `.btn-fc` pair. `type`/`disabled` and any listener (`@click`) fall through to the root `<button>` automatically via Vue's attribute inheritance — no explicit `emits` declaration needed.

### Props
| Prop | Type | Default | Notes |
|---|---|---|---|
| `variant` | `'primary' \| 'danger' \| 'secondary' \| 'edit' \| 'delete'` | `'primary'` | see table below |
| `type` | `'button' \| 'submit' \| 'reset'` | `'button'` | passed straight to the native `<button>` |
| `disabled` | `boolean` | `false` | |

### Variants
| Variant | Was | Background | Text | Use case |
|---|---|---|---|---|
| `primary` | `.btn-arcade`, `.btn-fc.yes` | `var(--status-success)` | `var(--text-on-accent)` | primary submit/confirm action |
| `danger` | `.btn-fc.no` | `var(--status-danger)` | `var(--text-on-accent)` | destructive/negative primary action (flashcard "don't know") |
| `secondary` | `.btn-guest` | transparent | `var(--text-secondary)` | cancel/back/secondary action |
| `edit` | `.btn-edit` | `var(--surface-panel-border)` | `var(--color-accent)` | row-level edit action |
| `delete` | `.btn-delete` | `var(--surface-panel-border)` | `var(--status-danger)` | row-level destructive action |

### States
| State | Treatment |
|---|---|
| default | variant-specific |
| hover | `secondary`/`edit`/`delete` only (`primary`/`danger` use press-shadow instead) |
| active | `primary`/`danger` only — `transform: translateY(4px); box-shadow: none` (pressed-button effect) |
| disabled | **new, uniform across all variants**: `opacity: 0.5; cursor: not-allowed; pointer-events: none` |
| focus-visible | `outline: var(--focus-ring-width) solid var(--color-focus-ring); outline-offset: 2px` — now defined **once**, in the component |

### Token usage
Fully tokenized — every variant uses `var(--space-*)`, `var(--font-size-*)`, `var(--tracking-*)`, `var(--focus-ring-width)`. No raw literals anywhere in the component.

### Normalizations made during extraction (visible deltas, not regressions — noted for spot-checking)
- **Disabled state is now uniform.** Before extraction, `.btn-arcade:disabled` existed in `ExamCreator.vue`/`AuthView.vue`/`QuestionCard.vue` (at inconsistent opacities: 0.4, 0.6, 0.5) but was **undefined** in `CardManagementView.vue`/`DeckManagementView.vue` and had no disabled state at all in `FlashcardsView.vue`/`ExamHub.vue`. All variants now share one `opacity: 0.5` disabled treatment. This is a net accessibility/consistency improvement, but the exact opacity changed in 2 of the 3 files that previously had a custom value.
- **Focus-visible outline now exists on every button, including 2 that never had one.** `QuestionCard.vue`'s submit button and `FlashcardsView.vue`'s yes/no buttons had no `:focus-visible` rule defined anywhere before extraction — a real pre-existing a11y gap, now fixed as a side effect of centralizing the style.
- **`primary`/`danger` sizing is normalized.** Before extraction, `.btn-arcade` padding/font-size varied per file (`var(--space-6) var(--space-10)` in most, `var(--space-7)` all-around in `ExamCreator.vue`/`AuthView.vue`, `var(--space-8) 28px` in `QuestionCard.vue`) and `.btn-fc` used yet another combination (`var(--space-7) var(--space-9)`, `--font-size-base`). All now render at the canonical `.btn-arcade` dimensions (`var(--space-6) var(--space-10)`, `--font-size-md`) — a ~1-4px visual shift on 5 of the 8 migrated call sites. Layout-specific overrides (full-width buttons, extra margin) were preserved via a supplementary class on the `AppButton` usage (e.g. `AuthView.vue`'s `.auth-submit-btn`/`.auth-guest-btn`, `ExamCreator.vue`'s existing `.full-width`) rather than baked into the component.

### Not folded into AppButton (deliberately left as local one-offs)
`ExamCreator.vue`'s `.btn-remove` (small text-only "remove question" link) and `.btn-add-question` (full-width dashed "add question" affordance), and `QuestionCard.vue`'s `.answer-key` toggle chips are structurally distinct, single-use affordances — extracting them would add variant surface area nobody else needs. Not touched.

### Consumers (8 files)
`ExamCreator.vue` (×2), `ExamHub.vue`, `ExamResults.vue`, `AuthView.vue` (×2), `QuestionCard.vue`, `FlashcardsView.vue` (×2, `primary`/`danger`), `CardManagementView.vue` (via itself + `ManageListShell`), `DeckManagementView.vue` (via itself + `ManageListShell`).

---

## Input

Unchanged from the pre-extraction audit — still a real shared CSS-only pattern in `tokens.css` (`.arcade-field`/`.arcade-label`/`.arcade-input`), not a component. Not in scope for Step 3.5 (only Button and the manage-list pattern were extracted).

### Token usage update
`.arcade-input`'s previously-untokenized `font-size: 14px` is now `var(--font-size-md-plus)` (see token-addition summary below).

**Still flagged, unresolved:** no component exists to extract into; disabled/error states are still undefined anywhere in the codebase.

---

## Modal / Dialog

**Status: still does not exist** — no component was built, per your explicit instruction. Confirmed `confirm()` call sites for the `ui-guidelines.md` backlog note:

| File:Line | Message |
|---|---|
| `frontend/src/features/library/CardManagementView.vue:90` | `Bạn có chắc muốn xóa thẻ này?` (delete card) |
| `frontend/src/features/library/DeckManagementView.vue:73` | `Bạn có chắc muốn xóa bộ thẻ này?` (delete deck) |

Both are the only native-`confirm()` usages in the entire frontend. Neither was touched by the `ManageListShell` extraction — the shell only emits `delete(id)` up to the parent; the `confirm()` gate and its per-entity message stay in each view's own `deleteCard`/`deleteDeck` handler.

---

## ManageListShell

`frontend/src/shared/components/ManageListShell.vue` — generic (`<script setup generic="T extends { id: string }">`) shell extracted from `CardManagementView.vue`/`DeckManagementView.vue`'s ~60%-duplicated CSS/structure: header + count badge, loading/empty status text, row shell (border, hover, spacing), and the edit/delete action buttons (now `AppButton` instances). The create/edit form area and each row's info content stay in the parent view via slots, since those are the genuinely different parts (Card's 2-column form + live markdown preview vs. Deck's single-column form; front/back vs. name/description row content).

### Props
| Prop | Type | Purpose |
|---|---|---|
| `title` | `string` | header `<h2>` text |
| `countLabel` | `string` | badge suffix (`"THẺ"` / `"BỘ"`) |
| `count` | `number` | badge count |
| `isLoading` | `boolean` | gates loading-text vs. list/empty rendering |
| `loadingText` | `string` | shown while `isLoading` |
| `emptyText` | `string` | shown when `rows.length === 0` |
| `rows` | `T[]` | the list to render |

### Emits
| Event | Payload | Purpose |
|---|---|---|
| `edit` | `T` (full item) | parent opens its own edit form with the item |
| `delete` | `string` (id) | parent runs its own `confirm()` + API call |

### Slots
| Slot | Scope | Purpose |
|---|---|---|
| `header-extra` | — | optional content after the count badge (only `CardManagementView` uses this, for its "← QUAY LẠI" close button — `DeckManagementView` has no equivalent, so the slot renders nothing there) |
| `form` | — | the create/edit form area, entirely owned by the parent |
| `row` | `{ item: T }` | the row's info content (left of the edit/delete buttons) |

### Anatomy
```
┌───────────────────────────────────────────┐
│ Title                    [count] [extra?] │
├───────────────────────────────────────────┤
│ <slot name="form" />                      │
├───────────────────────────────────────────┤
│ loading text / empty text / row list:     │
│  ┌─────────────────────────────────────┐  │
│  │ <slot name="row"/>      [SỬA][XÓA]  │  │
│  └─────────────────────────────────────┘  │
└───────────────────────────────────────────┘
```

### Token usage
Fully tokenized — carries forward every `var(--space-*)`/`var(--font-size-*)`/`var(--tracking-*)`/`var(--border-width-accent)` reference from the two original files' shared blocks.

### Normalization made during extraction (visible delta — flag for spot-check)
**Row vertical alignment changed for `DeckManagementView`.** The original `.card-row` used `align-items: flex-start` (correct for its 4-line front/back content) while `.deck-row` used `align-items: center` (fine for its shorter 2-line name/description content). The shared `.manage-row` uses `flex-start` (the `CardManagementView` behavior) for both, since a single shell can only pick one. Deck rows will now render with their edit/delete buttons top-aligned instead of vertically centered against the name/description text — a subtle but real visual change worth a look.

### Consumers
`CardManagementView.vue`, `DeckManagementView.vue` — the only two manage-list views in the app.

---

## ExamHud

Unchanged structurally from the pre-extraction audit. Token updates from this round: `.hud-lives`'s `font-size: 14px` → `var(--font-size-md-plus)`, `letter-spacing: 3px` → `var(--tracking-wider)`. No longer any untokenized literals in this file's `<style>` block except the still-intentionally-local `.hud-bar-track { height: 20px }` and `.hud-time { min-width: 64px }` (one-off layout constants, correctly out of scope).

---

## FlashCard

Unchanged — not touched by Step 3.5 (it doesn't use any button pattern; its flip-toggle is a `role="button"` div, not a `<button>`, so it was never a candidate for `AppButton`). Still the best-tokenized, best-documented component in the inventory alongside `PixelFrame`.

---

## PixelFrame

Unchanged. Still the model example — full JSDoc, clean token usage, no flags.

---

## MarkdownRenderer

Unchanged. Still at `shared/components/MarkdownRenderer.vue` (relocated in the earlier prep commit). `rgba(255,255,255,0.1)` on `:deep(code)` remains a deliberate local literal per your standing instruction.

---

## Token additions this round

| Token | Value | Applied to (file:line) |
|---|---|---|
| `--focus-ring-width` | `2px` | `ExamCreator.vue:621`, `ExamHub.vue:519,523`, `ExamResults.vue:617`, `AuthView.vue:305`, `FlashCard.vue:76`, `CardManagementView.vue:295` (`.arcade-input:focus-visible`), `DeckManagementView.vue:181` (`.arcade-input:focus-visible`) — line numbers as of the post-extraction file state; plus baked into `AppButton.vue` itself (all 8 button consumers inherit it for free instead of each declaring their own `outline: 2px solid` rule) |
| `--font-size-md-plus` | `14px` | `ExamHud.vue:69` (`.hud-lives`), `QuestionCard.vue:76` (`.q-passage`), `CardManagementView.vue` (`.card-row-text`), `tokens.css` (`.arcade-input`) — **4 sites, not the 3 originally estimated**; `QuestionCard.vue`'s `.q-passage` (exam reading-passage text) was missed in the original token-extraction audit and only surfaced when re-grepping for this token |
| `--tracking-wider` | `3px` | `ExamHud.vue:71` (`.hud-lives`) — the only occurrence in the codebase |

## Verification
`vue-tsc -b --noEmit` and `vite build` both run clean after every stage of this round (token additions, `AppButton` extraction + 8-file migration, `ManageListShell` extraction + 2-file migration).

## Cross-cutting flags resolved this round
The 3 flags raised at the end of the previous `COMPONENTS.md` pass are now closed:
1. ~~`outline: 2px solid` repeated raw~~ → `--focus-ring-width`, now centralized in `AppButton` for its 8 consumers and tokenized everywhere else it still appears locally (`Input`, `FlashCard`).
2. ~~`font-size: 14px` in 3 unrelated components~~ → `--font-size-md-plus`, applied to the (actually 4) real sites.
3. ~~Button duplication~~ → `AppButton.vue`, 8 call sites migrated, 0 remaining local `.btn-arcade`/`.btn-guest`/`.btn-edit`/`.btn-delete`/`.btn-fc` definitions anywhere in `frontend/src`.

## New flags from this round
- The three visual normalizations documented above (`AppButton` disabled-state/sizing, `ManageListShell` row alignment) are deliberate but real deltas from the pre-extraction pixel-exact appearance — worth a manual visual pass before treating this as done, since no visual regression testing tooling exists in this project (per CLAUDE.md, no test suite exists yet for the frontend).
- `ExamCreator.vue`'s `.btn-remove`/`.btn-add-question` and `QuestionCard.vue`'s `.answer-key` remain un-extracted, single-use, un-tokenized-beyond-existing button-adjacent patterns — not part of this round's scope, flagged for a future pass if they ever gain a second consumer.
