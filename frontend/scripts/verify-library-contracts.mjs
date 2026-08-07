/**
 * Structural + pure-logic checks for the library remake.
 * No vitest harness — run with: node scripts/verify-library-contracts.mjs
 * Asserts shipped source contracts and pure helpers that mirror production rules.
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const src = path.join(__dirname, '..', 'src');
const root = path.join(src, 'features', 'library');

let failed = 0;
function assert(cond, msg) {
  if (!cond) {
    console.error('FAIL:', msg);
    failed += 1;
  } else {
    console.log('OK:', msg);
  }
}

function read(rel) {
  return fs.readFileSync(path.join(src, rel), 'utf8');
}

// --- Pure production rules (same predicates as DeckDetailView / DeckManagementView) ---

/** Interactive reorder UI only (Alt/drag/legend/SAVE button). */
function canReorder(deckId, searchQuery) {
  return deckId !== null && searchQuery.trim() === '';
}

/**
 * Flush pending order before mutations. Independent of search filter —
 * a dirty order must still flush when the user types a query then mutates.
 */
function shouldFlushOrder(deckId, isDirty) {
  return Boolean(deckId && isDirty);
}

function coerceDeckId(deckId) {
  return deckId || null;
}

/**
 * Empty rack: suppress Unfiled only when count is *known* zero.
 * null (loading/failed) is NOT empty — still render Unfiled without a badge.
 */
function emptyRackPredicate(realDecksLength, unfiledCount) {
  return realDecksLength === 0 && unfiledCount === 0;
}

function shouldRenderUnfiledRow(realDecksLength, unfiledCount, searchMatches) {
  if (!searchMatches) return false;
  // Known empty library → no Unfiled (shell empty state).
  if (emptyRackPredicate(realDecksLength, unfiledCount)) return false;
  // null count (unknown) or >0 or decks present → render Unfiled.
  return true;
}

function activeIndexAfterMove(from, delta, length) {
  const to = from + delta;
  if (to < 0 || to >= length) return from;
  return to;
}

function imeShouldBail(e) {
  return Boolean(e.isComposing || e.keyCode === 229);
}

// canReorder (interactive only)
assert(canReorder('abc', '') === true, 'canReorder true for real deck + empty search');
assert(canReorder(null, '') === false, 'canReorder false for unfiled');
assert(canReorder('abc', 'foo') === false, 'canReorder false when filtered');
assert(canReorder('abc', '  ') === true, 'canReorder true when search is whitespace-only');

// flush predicate — must NOT depend on search / canReorder
assert(shouldFlushOrder('abc', true) === true, 'flush when deckId + dirty');
assert(shouldFlushOrder('abc', false) === false, 'no flush when clean');
assert(shouldFlushOrder(null, true) === false, 'no flush for unfiled even if dirty');
assert(
  shouldFlushOrder('abc', true) === true && canReorder('abc', 'filter') === false,
  'flush still required when search active (canReorder false, dirty true)',
);

// null deckId coercion
assert(coerceDeckId('') === null, 'empty string deckId coerces to null');
assert(coerceDeckId(null) === null, 'null deckId stays null');
assert(coerceDeckId('x') === 'x', 'real deckId preserved');

// empty rack + Unfiled visibility
assert(emptyRackPredicate(0, 0) === true, 'empty rack when no decks and known 0 unfiled');
assert(emptyRackPredicate(0, 1) === false, 'not empty when unfiled exist');
assert(emptyRackPredicate(1, 0) === false, 'not empty when real decks exist');
assert(emptyRackPredicate(0, null) === false, 'null unfiled count is NOT empty');
assert(
  shouldRenderUnfiledRow(0, null, true) === true,
  'render Unfiled when count unknown (null) and no decks',
);
assert(shouldRenderUnfiledRow(0, 0, true) === false, 'suppress Unfiled when known empty library');
assert(
  shouldRenderUnfiledRow(1, 0, true) === true,
  'render Unfiled when decks exist and 0 unfiled',
);

// activeIndex follows move
assert(activeIndexAfterMove(2, 1, 5) === 3, 'activeIndex updates on move down');
assert(activeIndexAfterMove(0, -1, 5) === 0, 'activeIndex stays at boundary');
assert(activeIndexAfterMove(4, 1, 5) === 4, 'activeIndex stays at end boundary');

// IME guard
assert(imeShouldBail({ isComposing: true, keyCode: 69 }) === true, 'IME bail on isComposing');
assert(imeShouldBail({ isComposing: false, keyCode: 229 }) === true, 'IME bail on keyCode 229');
assert(imeShouldBail({ isComposing: false, keyCode: 69 }) === false, 'no IME bail for plain e');

// --- Source structure (production code, not reimplementation) ---

const api = read('features/library/api.ts');
assert(api.includes('if (!res.ok)'), 'api.ts checks res.ok');
assert(api.includes('form.deckId || null'), 'api.ts null-coerces deckId');
assert(api.includes('apiFetch'), 'api.ts is the only library apiFetch site');

const roving = read('features/library/composables/useRovingList.ts');
assert(roving.includes('e.isComposing || e.keyCode === 229'), 'IME guard present in useRovingList');
assert(roving.includes("key === 'Escape'"), 'Escape ladder present');

const detail = read('features/library/DeckDetailView.vue');
assert(detail.includes('withOrderFlushed'), 'DeckDetailView flushes order before mutations');

// Extract function bodies so later onSave/canReorder uses do not false-positive.
const flushBody = detail.match(
  /async function withOrderFlushed\([^)]*\)[^{]*\{([\s\S]*?)\n\}/,
)?.[1];
const saveOrderBody = detail.match(/async function saveOrder\(\)[^{]*\{([\s\S]*?)\n\}/)?.[1];
assert(Boolean(flushBody), 'withOrderFlushed function body extractable');
assert(Boolean(saveOrderBody), 'saveOrder function body extractable');
// Production flush must gate on deckId + isDirty, NOT canReorder.
assert(
  /if\s*\(\s*props\.deckId\s*&&\s*isDirty\.value\s*\)/.test(flushBody),
  'withOrderFlushed gates on props.deckId && isDirty (not canReorder)',
);
assert(!/canReorder/.test(flushBody), 'withOrderFlushed body must not reference canReorder');
// saveOrder early-return must not include canReorder; must rethrow on failure.
const saveOrderGuard = saveOrderBody.split('try')[0] || saveOrderBody;
assert(!/canReorder/.test(saveOrderGuard), 'saveOrder early-return must not gate on canReorder');
assert(/throw err/.test(saveOrderBody), 'saveOrder rethrows on failure so withOrderFlushed aborts');
assert(detail.includes('activeIndex.value = to'), 'DeckDetailView updates activeIndex on move');
assert(detail.includes('ConfirmDialog'), 'DeckDetailView uses ConfirmDialog');
assert(detail.includes('deckId: string | null'), 'DeckDetailView accepts null deckId');

const rack = read('features/library/DeckManagementView.vue');
assert(rack.includes('UNFILED_ROW_ID'), 'rack has synthetic Unfiled row');
assert(rack.includes('ConfirmDialog'), 'rack uses ConfirmDialog');
// Empty predicate must use strict === 0 on unfiledCount (not ?? 0).
assert(
  /realDecks\.value\.length\s*===\s*0\s*&&\s*unfiledCount\.value\s*===\s*0/.test(rack),
  'empty rack uses unfiledCount === 0 (null is not empty)',
);
assert(
  !/\(unfiledCount\.value\s*\?\?\s*0\)\s*===\s*0/.test(rack),
  'empty rack must not coerce null unfiledCount to 0',
);
assert(!rack.includes('confirm('), 'rack has no native confirm()');

const router = read('router/index.ts');
assert(router.includes("path: '/decks/unfiled'"), 'router has /decks/unfiled');
assert(router.includes('deckId: null'), 'unfiled props deckId null');
assert(router.includes("redirect: { name: 'decks' }"), '/cards redirects to decks');

const app = read('App.vue');
assert(app.includes("startsWith('/questions')"), 'BANK tab lights on /questions');
assert(!app.includes("startsWith('/question-bank')"), 'stale /question-bank path gone');
assert(!app.includes("'cards'"), "activeTab union has no 'cards'");

const shell = read('shared/components/ManageListShell.vue');
assert(shell.includes('rowNavigation'), 'ManageListShell has rowNavigation');
assert(shell.includes('draggableRows'), 'ManageListShell has draggableRows');
assert(shell.includes('prefers-reduced-motion'), 'ManageListShell reduced-motion guard');

// CardManagementView must be gone (Stage 8).
assert(
  !fs.existsSync(path.join(root, 'CardManagementView.vue')),
  'CardManagementView.vue hard-deleted',
);
assert(
  !fs
    .readdirSync(root, { withFileTypes: true })
    .some((f) => f.isFile() && f.name.includes('CardManagement')),
  'no CardManagement* files under library',
);

// No apiFetch outside api.ts in library views/components
function walkVue(dir) {
  for (const ent of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, ent.name);
    if (ent.isDirectory()) walkVue(p);
    else if (ent.name.endsWith('.vue')) {
      const body = fs.readFileSync(p, 'utf8');
      assert(!body.includes('apiFetch'), `${path.relative(root, p)} does not call apiFetch`);
    }
  }
}
walkVue(root);

if (failed > 0) {
  console.error(`\n${failed} assertion(s) failed`);
  process.exit(1);
}
console.log('\nAll library contracts passed.');
