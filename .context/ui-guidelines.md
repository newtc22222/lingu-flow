# LinguFlow UI Guidelines

Scope: `frontend/src`, Vue 3 arcade design system. Reflects the final state of
`styles/tokens.css`, `shared/components/AppButton.vue`, and
`shared/components/ManageListShell.vue` after the Step 3.5 extraction (see
`frontend/COMPONENTS.md` for the full inventory and rationale).

---

## [MUST]

### Always use `AppButton` for any button — never re-create `.btn-*` CSS locally

`shared/components/AppButton.vue` covers every button treatment in the app. `type`/`disabled` and any listener (`@click`) fall through to the root `<button>` automatically — don't declare them as props on your own component.

| `variant` | Use for |
|---|---|
| `primary` (default) | primary submit/confirm action, or a positive binary choice (e.g. flashcard "know it") |
| `danger` | a destructive or negative *primary* action rendered with the same weight as `primary` (e.g. flashcard "don't know it") — not for row-level delete, use `delete` below |
| `secondary` | cancel/back/secondary action |
| `edit` | row-level edit action in a list |
| `delete` | row-level destructive action in a list |

```vue
<!-- Before -->
<button type="submit" class="btn-arcade font-label" :disabled="isLoading">SAVE</button>

<!-- After -->
<AppButton type="submit" :disabled="isLoading">SAVE</AppButton>
```

If you need a layout tweak (full width, extra margin), add a class on the `AppButton` usage itself — don't fork the component's internal styles:

```vue
<AppButton class="full-width" @click="submit">SAVE</AppButton>
```
```css
.full-width { width: 100%; }
```

Do not write a new `.btn-*` class, even a "just this once" one-off, without checking whether it's really a 6th variant of something `AppButton` should own. (Two genuinely distinct one-off affordances — `ExamCreator.vue`'s dashed-border "add question" button and `QuestionCard.vue`'s answer-key toggle chips — were deliberately left outside `AppButton` because they're structurally unlike a button and each has exactly one consumer. If a second consumer ever shows up for either, that's the signal to extract.)

### Always use design tokens — never hardcode px/rem/rgba

Every spacing, font-size, tracking, border-width, and focus-ring value in the app has a token in `styles/tokens.css`. Reference the token, not the raw value:

```css
/* Wrong */
.thing { padding: 12px 24px; font-size: 13px; letter-spacing: 1.5px; outline: 2px solid var(--color-focus-ring); }

/* Right */
.thing { padding: var(--space-6) var(--space-10); font-size: var(--font-size-md); letter-spacing: var(--tracking-wide); outline: var(--focus-ring-width) solid var(--color-focus-ring); }
```

Token families:
- **Spacing**: `--space-1` (2px) through `--space-11` (26px) — padding, margin, gap.
- **Type scale**: `--font-size-xs` (10px) → `--font-size-display` (44px), including `--font-size-md-plus` (14px, the gap step between `md`/13px and `lg`/15px).
- **Tracking**: `--tracking-tight` (0.5px), `--tracking-normal` (1px), `--tracking-wide` (1.5px), `--tracking-wider` (3px).
- **Border width**: `--border-width-accent` (3px, accent-bar borders only). 2px panel borders reuse `--space-1` — there is no separate 2px border-width token, that's intentional, don't add one.
- **Focus ring**: `--focus-ring-width` (2px) — every `outline: ... solid var(--color-focus-ring)` should use this.

If you hit a value with no matching token (check `tokens.css` first — new steps get added there when a value repeats 3+ times across unrelated components, per the Aug 2026 audit process), treat it as a genuine one-off local literal rather than force-fitting the nearest token. Flag it in review rather than silently picking whichever token is numerically closest.

### Use `ManageListShell` for any new "list of rows with inline edit/delete" pattern

Don't write a new CRUD-list view from scratch — `shared/components/ManageListShell.vue` (generic over `T extends { id: string }`) owns the header/count badge, loading/empty status text, row shell, and edit/delete buttons. Only the create/edit form and each row's info content are yours to supply.

Reference usage (`DeckManagementView.vue` — the simpler of the two real consumers):

```vue
<ManageListShell
  title="QUẢN LÝ BỘ THẺ"
  count-label="BỘ"
  :count="decks.length"
  :is-loading="isLoading"
  loading-text="▸ ĐANG TẢI BỘ THẺ…"
  empty-text="CHƯA CÓ BỘ THẺ NÀO. TẠO BỘ THẺ ĐẦU TIÊN Ở TRÊN."
  :rows="decks"
  @edit="editDeck"
  @delete="deleteDeck"
>
  <template #form>
    <!-- your PixelFrame + create/edit form, entirely your own -->
  </template>

  <template #row="{ item }">
    <!-- just the row's info content; edit/delete buttons are the shell's job -->
    <div class="deck-row-name font-body">{{ item.name }}</div>
    <div class="deck-row-desc font-body">{{ item.description }}</div>
  </template>
</ManageListShell>
```

`CardManagementView.vue` is the reference for the fuller case: a 2-column form with a live preview pane (still just goes in `#form` — the shell doesn't care what's inside it) and an extra header button via `#header-extra`.

`@edit` receives the full row item; `@delete` receives just the id. Keep your own `confirm()`/API-call logic in the `edit`/`delete` handlers in the parent — the shell only renders and emits, it doesn't know about your delete-confirmation copy or your API.

---

## [SHOULD]

### Accessibility baseline: match what `AppButton` now does for free

`AppButton` bakes in a `focus-visible` outline (`var(--focus-ring-width) solid var(--color-focus-ring)`) on every variant. Before this extraction, 2 of the app's buttons (`QuestionCard.vue`'s submit, `FlashcardsView.vue`'s yes/no) had **no focus-visible outline at all** — a real gap that's now closed as a side effect of centralizing the style. Treat "every interactive element gets a visible focus-visible outline, no exceptions" as the baseline for any new interactive element you build outside `AppButton` (custom toggles, chips, etc.) — copy the same `outline: var(--focus-ring-width) solid var(--color-focus-ring); outline-offset: 2px;` pattern rather than skipping it or inventing a new width.

---

## [AVOID]

### Native `confirm()` for destructive actions

`CardManagementView.vue` and `DeckManagementView.vue` both gate their delete actions behind the browser's native `confirm()` — the only two such call sites in the app. This is a **known gap, not a pattern to extend**: no `ConfirmDialog`/modal component exists anywhere in the codebase (confirmed by a repo-wide search — there is no modal/dialog pattern of any kind to reuse). Don't add a third `confirm()` call site as a quick fix for a new destructive action; that just grows the debt. This is a backlog item — building a real confirmation dialog is out of scope for now, but new destructive-action UI should not silently work around the gap by copying the `confirm()` pattern either. Flag it and ask before shipping a third instance.

---

## Legacy `components/` vs. `features/<domain>/`

The frontend is mid-migration (see root `CLAUDE.md` for the full picture). Two conventions coexist:

- **`features/<domain>/{<Name>View.vue, components/, store/}`** — the current convention. New work goes here. Top-level route components use a `...View.vue` suffix (`AuthView.vue`, `DashboardView.vue`, `ExamView.vue`, `FlashcardsView.vue`, `CardManagementView.vue`, `DeckManagementView.vue`).
- **Legacy flat `components/`** — `ExamHub.vue`, `ExamResults.vue`, `ExamCreator.vue` are still live and actively wired into `App.vue`, not yet migrated to `features/exam/`. They don't follow the `...View.vue` naming convention. Don't add new files here; if you're touching one of these three for a feature change, migrating it to `features/exam/` first is worth raising, but isn't required for a small fix.

Both conventions already consume `AppButton`/`ManageListShell`/other `shared/components/*` identically — the shared-component layer is convention-agnostic, so this split doesn't change how you use any of the [MUST] rules above.
