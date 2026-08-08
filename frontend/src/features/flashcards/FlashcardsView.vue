<script setup lang="ts">
/**
 * Flashcards practice lobby — select mode (Review / Learn / Match) and collection,
 * then START. Review runs in-page; Learn/Match navigate to existing routes.
 */
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';
import { apiFetch } from '@/utils/api';
import { listDecks } from '@/features/library/api';
import type { LibraryDeck } from '@/features/library/types';
import AppButton from '@/shared/components/AppButton.vue';
import ReviewSession, { type ReviewCard } from './components/ReviewSession.vue';

type PracticeMode = 'review' | 'learn' | 'match';
type Phase = 'lobby' | 'review';

/** Synthetic collection id: all due cards across decks (Review only). */
const DUE_ALL_ID = '__due_all__';

const STORAGE_MODE = 'linguflow.flashcards.lastMode';
const STORAGE_DECK = 'linguflow.flashcards.lastDeckId';

const { t } = useI18n();
const router = useRouter();

const phase = ref<Phase>('lobby');
const isLoading = ref(true);
const loadError = ref('');
const mode = ref<PracticeMode>('review');
const selectedCollectionId = ref<string>(DUE_ALL_ID);

const decks = ref<LibraryDeck[]>([]);
const dueCards = ref<ReviewCard[]>([]);

const modes = computed(() => [
  {
    id: 'review' as const,
    title: t('flashcards.modeReview'),
    blurb: t('flashcards.modeReviewBlurb'),
    srs: t('flashcards.srsYes'),
  },
  {
    id: 'learn' as const,
    title: t('flashcards.modeLearn'),
    blurb: t('flashcards.modeLearnBlurb'),
    srs: t('flashcards.srsYes'),
  },
  {
    id: 'match' as const,
    title: t('flashcards.modeMatch'),
    blurb: t('flashcards.modeMatchBlurb'),
    srs: t('flashcards.srsNo'),
  },
]);

const dueByDeckId = computed(() => {
  const map = new Map<string, number>();
  for (const card of dueCards.value) {
    const key = card.deckId ?? '';
    if (!key) continue;
    map.set(key, (map.get(key) ?? 0) + 1);
  }
  return map;
});

const totalDue = computed(() => dueCards.value.length);

const deckNameById = computed(() => {
  const m = new Map<string, string>();
  for (const d of decks.value) m.set(d.id, d.name);
  return m;
});

/** Enrich due cards with deck names for the review chrome. */
const enrichedDueCards = computed((): ReviewCard[] =>
  dueCards.value.map((c) => ({
    ...c,
    deckName: c.deckId ? (deckNameById.value.get(c.deckId) ?? c.deckName) : c.deckName,
  })),
);

const collectionRows = computed(() => {
  if (mode.value === 'review') {
    return [
      {
        id: DUE_ALL_ID,
        name: t('flashcards.dueAll'),
        cardCount: totalDue.value,
        dueCount: totalDue.value,
        isDueAll: true,
      },
      ...decks.value.map((d) => ({
        id: d.id,
        name: d.name,
        cardCount: d.cardCount,
        dueCount: dueByDeckId.value.get(d.id) ?? 0,
        isDueAll: false,
      })),
    ];
  }
  return decks.value.map((d) => ({
    id: d.id,
    name: d.name,
    cardCount: d.cardCount,
    dueCount: dueByDeckId.value.get(d.id) ?? 0,
    isDueAll: false,
  }));
});

const selectedRow = computed(
  () => collectionRows.value.find((r) => r.id === selectedCollectionId.value) ?? null,
);

const reviewQueue = computed((): ReviewCard[] => {
  const cards = enrichedDueCards.value;
  if (selectedCollectionId.value === DUE_ALL_ID) return cards;
  return cards.filter((c) => c.deckId === selectedCollectionId.value);
});

const startBlockedReason = computed((): string | null => {
  if (mode.value === 'review') {
    if (totalDue.value === 0) return t('flashcards.blockNoDue');
    if (reviewQueue.value.length === 0) return t('flashcards.blockNoDueInDeck');
    return null;
  }
  if (!selectedCollectionId.value || selectedCollectionId.value === DUE_ALL_ID) {
    return t('flashcards.blockPickDeck');
  }
  const deck = decks.value.find((d) => d.id === selectedCollectionId.value);
  if (!deck) return t('flashcards.blockPickDeck');
  if (deck.cardCount === 0) return t('flashcards.blockEmptyDeck');
  if (mode.value === 'match' && deck.cardCount < 2) return t('flashcards.blockMatchMin');
  return null;
});

const canStart = computed(() => !isLoading.value && !startBlockedReason.value);

const startLabel = computed(() => {
  if (mode.value === 'review') return t('flashcards.startReview');
  if (mode.value === 'learn') return t('flashcards.startLearn');
  return t('flashcards.startMatch');
});

const summaryLine = computed(() => {
  if (!selectedRow.value) return t('flashcards.summaryNone');
  if (mode.value === 'review') {
    return t('flashcards.summaryReview', {
      name: selectedRow.value.name,
      count: reviewQueue.value.length,
    });
  }
  return t('flashcards.summaryDeck', {
    name: selectedRow.value.name,
    count: selectedRow.value.cardCount,
  });
});

function persistPrefs() {
  try {
    localStorage.setItem(STORAGE_MODE, mode.value);
    if (selectedCollectionId.value !== DUE_ALL_ID) {
      localStorage.setItem(STORAGE_DECK, selectedCollectionId.value);
    }
  } catch {
    /* ignore quota / private mode */
  }
}

function loadPrefs(): { mode: PracticeMode | null; deckId: string | null } {
  try {
    const m = localStorage.getItem(STORAGE_MODE);
    const deckId = localStorage.getItem(STORAGE_DECK);
    const modeOk = m === 'review' || m === 'learn' || m === 'match' ? m : null;
    return { mode: modeOk, deckId };
  } catch {
    return { mode: null, deckId: null };
  }
}

function applySmartDefaults() {
  const prefs = loadPrefs();

  if (totalDue.value > 0) {
    mode.value = prefs.mode === 'learn' || prefs.mode === 'match' ? prefs.mode : 'review';
  } else if (prefs.mode === 'review' || !prefs.mode) {
    mode.value = 'learn';
  } else {
    mode.value = prefs.mode;
  }

  if (mode.value === 'review') {
    selectedCollectionId.value = DUE_ALL_ID;
  } else if (prefs.deckId && decks.value.some((d) => d.id === prefs.deckId)) {
    selectedCollectionId.value = prefs.deckId;
  } else if (decks.value[0]) {
    selectedCollectionId.value = decks.value[0].id;
  } else {
    selectedCollectionId.value = DUE_ALL_ID;
  }
}

function selectMode(next: PracticeMode) {
  mode.value = next;
  if (next === 'review') {
    selectedCollectionId.value = DUE_ALL_ID;
  } else if (selectedCollectionId.value === DUE_ALL_ID) {
    const prefs = loadPrefs();
    if (prefs.deckId && decks.value.some((d) => d.id === prefs.deckId)) {
      selectedCollectionId.value = prefs.deckId;
    } else if (decks.value[0]) {
      selectedCollectionId.value = decks.value[0].id;
    }
  }
  persistPrefs();
}

function selectCollection(id: string) {
  selectedCollectionId.value = id;
  persistPrefs();
}

function start() {
  if (!canStart.value) return;
  persistPrefs();

  if (mode.value === 'review') {
    phase.value = 'review';
    return;
  }
  const deckId = selectedCollectionId.value;
  if (mode.value === 'learn') {
    void router.push({ name: 'learn', params: { deckId } });
    return;
  }
  void router.push({ name: 'match', params: { deckId } });
}

async function onReviewExit() {
  phase.value = 'lobby';
  await fetchData();
}

async function onReviewComplete() {
  phase.value = 'lobby';
  await fetchData();
}

async function fetchData() {
  isLoading.value = true;
  loadError.value = '';
  try {
    const [deckList, studyRes] = await Promise.all([
      listDecks(),
      apiFetch('/api/cards/study'),
    ]);
    if (!studyRes.ok) {
      throw new Error(t('common.requestFailed', { status: studyRes.status }));
    }
    const raw = (await studyRes.json()) as Record<string, unknown>[];
    decks.value = deckList;
    dueCards.value = raw.map((c) => ({
      id: c.id as string,
      front: c.front as string,
      back: c.back as string,
      deckId: (c.deckId as string | null | undefined) ?? null,
      deckName: (c.deckName as string | undefined) ?? undefined,
    }));
    if (phase.value === 'lobby') {
      applySmartDefaults();
    }
  } catch (err) {
    loadError.value = err instanceof Error ? err.message : t('dashboard.error');
  } finally {
    isLoading.value = false;
  }
}

function goLibrary() {
  void router.push({ name: 'decks' });
}

function onLobbyKey(e: KeyboardEvent) {
  if (phase.value !== 'lobby') return;
  if (['INPUT', 'TEXTAREA'].includes((e.target as HTMLElement).tagName)) return;

  if (e.key === '1') {
    e.preventDefault();
    selectMode('review');
    return;
  }
  if (e.key === '2') {
    e.preventDefault();
    selectMode('learn');
    return;
  }
  if (e.key === '3') {
    e.preventDefault();
    selectMode('match');
    return;
  }
  if (e.key === 'Enter') {
    e.preventDefault();
    start();
    return;
  }

  const rows = collectionRows.value;
  if (!rows.length) return;
  const idx = rows.findIndex((r) => r.id === selectedCollectionId.value);
  if (e.key === 'ArrowDown') {
    e.preventDefault();
    const next = rows[Math.min(idx + 1, rows.length - 1)] ?? rows[0];
    if (next) selectCollection(next.id);
  }
  if (e.key === 'ArrowUp') {
    e.preventDefault();
    const prev = rows[Math.max(idx - 1, 0)] ?? rows[0];
    if (prev) selectCollection(prev.id);
  }
}

watch(mode, () => {
  if (mode.value !== 'review' && selectedCollectionId.value === DUE_ALL_ID && decks.value[0]) {
    selectedCollectionId.value = decks.value[0].id;
  }
});

onMounted(() => {
  void fetchData();
  window.addEventListener('keydown', onLobbyKey);
});
onUnmounted(() => {
  window.removeEventListener('keydown', onLobbyKey);
});
</script>

<template>
  <div class="fc-root">
    <ReviewSession
      v-if="phase === 'review'"
      :cards="reviewQueue"
      @exit="onReviewExit"
      @complete="onReviewComplete"
    />

    <div v-else class="lobby">
      <header class="lobby-header">
        <div class="lobby-heading">
          <h1 class="lobby-title font-body">{{ t('flashcards.title') }}</h1>
          <p class="lobby-tagline font-body">{{ t('flashcards.tagline') }}</p>
        </div>
        <div class="lobby-stats font-label">
          <span class="lobby-stat">
            <span class="lobby-stat-k">{{ t('flashcards.statDue') }}</span>
            <span class="lobby-stat-v" :class="{ 'lobby-stat-v--hot': totalDue > 0 }">
              {{ totalDue }}
            </span>
          </span>
          <span class="lobby-stat">
            <span class="lobby-stat-k">{{ t('flashcards.statDecks') }}</span>
            <span class="lobby-stat-v">{{ decks.length }}</span>
          </span>
        </div>
      </header>

      <p v-if="loadError" class="lobby-error font-body" role="alert">
        {{ loadError }}
        <AppButton variant="secondary" @click="fetchData">{{ t('common.retry') }}</AppButton>
      </p>

      <div v-if="isLoading" class="lobby-status font-label">{{ t('flashcards.loading') }}</div>

      <template v-else-if="!loadError">
        <div v-if="!decks.length && totalDue === 0" class="lobby-empty">
          <p class="lobby-empty-title font-body">{{ t('flashcards.noDecks') }}</p>
          <p class="lobby-empty-sub font-body">{{ t('flashcards.noDecksSub') }}</p>
          <AppButton @click="goLibrary">{{ t('flashcards.goLibrary') }}</AppButton>
        </div>

        <div v-else class="lobby-body">
          <section class="lobby-modes" :aria-label="t('flashcards.modeSection')">
            <h2 class="section-label font-label">{{ t('flashcards.modeSection') }}</h2>
            <div class="cartridge-list" role="listbox" :aria-label="t('flashcards.modeSection')">
              <button
                v-for="(m, i) in modes"
                :key="m.id"
                type="button"
                role="option"
                class="cartridge"
                :class="{ 'cartridge--active': mode === m.id }"
                :aria-selected="mode === m.id"
                @click="selectMode(m.id)"
              >
                <span class="cartridge-index font-label">{{ i + 1 }}</span>
                <span class="cartridge-body">
                  <span class="cartridge-title font-body">{{ m.title }}</span>
                  <span class="cartridge-blurb font-body">{{ m.blurb }}</span>
                  <span class="cartridge-srs font-label">{{ m.srs }}</span>
                </span>
              </button>
            </div>
          </section>

          <section class="lobby-collections" :aria-label="t('flashcards.collectionSection')">
            <h2 class="section-label font-label">{{ t('flashcards.collectionSection') }}</h2>

            <div v-if="!collectionRows.length" class="lobby-status font-label">
              {{ t('flashcards.noDecks') }}
            </div>

            <div v-else class="collection-scroll" role="listbox">
              <button
                v-for="row in collectionRows"
                :key="row.id"
                type="button"
                role="option"
                class="collection-row"
                :class="{
                  'collection-row--active': selectedCollectionId === row.id,
                  'collection-row--due-all': row.isDueAll,
                }"
                :aria-selected="selectedCollectionId === row.id"
                @click="selectCollection(row.id)"
              >
                <span class="collection-main">
                  <span class="collection-name font-body">{{ row.name }}</span>
                  <span class="collection-meta font-label">
                    <span v-if="row.isDueAll">
                      {{ t('flashcards.dueCount', { count: row.dueCount }) }}
                    </span>
                    <template v-else>
                      <span>{{ t('decks.cardCount', { count: row.cardCount }) }}</span>
                      <span v-if="mode === 'review' && row.dueCount > 0" class="due-badge">
                        {{ t('flashcards.dueCount', { count: row.dueCount }) }}
                      </span>
                    </template>
                  </span>
                </span>
                <span class="collection-radio" aria-hidden="true" />
              </button>
            </div>

            <footer class="lobby-footer">
              <div class="lobby-summary">
                <p class="summary-line font-body">{{ summaryLine }}</p>
                <p v-if="startBlockedReason" class="block-reason font-label">
                  {{ startBlockedReason }}
                </p>
                <p class="key-hint font-label">{{ t('flashcards.lobbyKeys') }}</p>
              </div>
              <div class="lobby-cta">
                <AppButton :disabled="!canStart" @click="start">{{ startLabel }}</AppButton>
                <AppButton variant="secondary" @click="goLibrary">
                  {{ t('flashcards.goLibrary') }}
                </AppButton>
              </div>
            </footer>
          </section>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.fc-root {
  flex: 1 1 0;
  min-height: 0;
  width: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.lobby {
  flex: 1 1 0;
  min-height: 0;
  width: 100%;
  box-sizing: border-box;
  /* stylelint-disable-next-line scale-unlimited/declaration-strict-value -- full-bleed console padding */
  padding: 20px var(--space-9) var(--space-8);
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
  overflow: hidden;
}

.lobby-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-7);
  flex-wrap: wrap;
  flex-shrink: 0;
}
.lobby-title {
  margin: 0 0 var(--space-2);
  font-size: var(--font-size-xl);
  font-weight: 700;
  color: var(--color-accent);
}
.lobby-tagline {
  margin: 0;
  font-size: var(--font-size-md);
  color: var(--text-secondary);
}
.lobby-stats {
  display: flex;
  gap: var(--space-6);
  flex-wrap: wrap;
}
.lobby-stat {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  background: var(--surface-page);
  border: var(--space-1) solid var(--surface-panel-border);
  padding: var(--space-3) var(--space-5);
  min-width: 72px;
}
.lobby-stat-k {
  font-size: var(--font-size-2xs);
  letter-spacing: var(--tracking-wide);
  color: var(--text-secondary);
}
.lobby-stat-v {
  font-size: var(--font-size-lg);
  font-weight: 700;
  color: var(--text-primary);
}
.lobby-stat-v--hot {
  color: var(--color-accent);
}

.lobby-error {
  color: var(--status-danger);
  font-size: var(--font-size-md);
  margin: 0;
  display: flex;
  align-items: center;
  gap: var(--space-5);
  flex-wrap: wrap;
  flex-shrink: 0;
}
.lobby-status {
  color: var(--text-secondary);
  font-size: var(--font-size-md);
  margin: 0;
  flex-shrink: 0;
}

.lobby-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
  gap: var(--space-5);
  max-width: 480px;
}
.lobby-empty-title {
  margin: 0;
  font-size: var(--font-size-lg);
  font-weight: 700;
  color: var(--text-primary);
}
.lobby-empty-sub {
  margin: 0;
  font-size: var(--font-size-md);
  color: var(--text-secondary);
}

.lobby-body {
  flex: 1 1 0;
  min-height: 0;
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--space-7);
  overflow: hidden;
}
@media (min-width: 900px) {
  .lobby-body {
    grid-template-columns: minmax(0, 5fr) minmax(0, 6fr);
  }
}

.section-label {
  margin: 0 0 var(--space-4);
  font-size: var(--font-size-2xs);
  letter-spacing: var(--tracking-wide);
  color: var(--text-secondary);
  flex-shrink: 0;
}

.lobby-modes,
.lobby-collections {
  display: flex;
  flex-direction: column;
  min-height: 0;
  min-width: 0;
  overflow: hidden;
}

/* ── Mode cartridges (signature) ── */
.cartridge-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  flex: 1 1 0;
  min-height: 0;
  overflow-y: auto;
}
.cartridge {
  display: flex;
  align-items: stretch;
  gap: 0;
  text-align: left;
  background: var(--surface-panel);
  border: var(--space-1) solid var(--surface-panel-border);
  border-left: var(--border-width-accent) solid var(--surface-panel-border);
  padding: 0;
  cursor: pointer;
  color: inherit;
  transition:
    border-color 0.12s ease,
    background 0.12s ease;
}
.cartridge:hover {
  background: var(--state-hover-surface);
  border-left-color: var(--color-accent);
}
.cartridge--active {
  background: var(--state-hover-surface);
  border-color: var(--color-accent);
  border-left-color: var(--color-accent);
  box-shadow: inset 0 0 0 1px var(--color-accent);
}
.cartridge:focus-visible {
  outline: var(--focus-ring-width) solid var(--color-focus-ring);
  outline-offset: 2px;
}
.cartridge-index {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 40px;
  padding: var(--space-5) var(--space-4);
  background: var(--surface-page);
  border-right: var(--space-1) solid var(--surface-panel-border);
  font-size: var(--font-size-sm);
  font-weight: 700;
  letter-spacing: var(--tracking-wide);
  color: var(--text-secondary);
}
.cartridge--active .cartridge-index {
  background: var(--state-selected-bg);
  color: var(--text-on-accent);
  border-right-color: var(--color-accent);
}
.cartridge-body {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  padding: var(--space-5) var(--space-6);
  min-width: 0;
}
.cartridge-title {
  font-size: var(--font-size-md-plus);
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: var(--tracking-normal);
}
.cartridge--active .cartridge-title {
  color: var(--color-accent);
}
.cartridge-blurb {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  line-height: 1.45;
}
.cartridge-srs {
  font-size: var(--font-size-2xs);
  letter-spacing: var(--tracking-wide);
  color: var(--text-disabled);
  text-transform: uppercase;
  margin-top: var(--space-1);
}
.cartridge--active .cartridge-srs {
  color: var(--text-secondary);
}

/* ── Collections ── */
.collection-scroll {
  flex: 1 1 0;
  min-height: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}
.collection-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-5);
  text-align: left;
  background: var(--surface-panel);
  border: var(--space-1) solid var(--surface-panel-border);
  border-left: var(--border-width-accent) solid var(--surface-panel-border);
  padding: var(--space-5) var(--space-6);
  cursor: pointer;
  color: inherit;
}
.collection-row:hover {
  background: var(--state-hover-surface);
  border-left-color: var(--color-accent);
}
.collection-row--active {
  border-color: var(--color-accent);
  border-left-color: var(--color-accent);
  background: var(--state-hover-surface);
}
.collection-row--due-all {
  border-style: dashed;
}
.collection-row:focus-visible {
  outline: var(--focus-ring-width) solid var(--color-focus-ring);
  outline-offset: 2px;
}
.collection-main {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  min-width: 0;
}
.collection-name {
  font-size: var(--font-size-md);
  font-weight: 600;
  color: var(--text-primary);
}
.collection-meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-4);
  font-size: var(--font-size-2xs);
  letter-spacing: var(--tracking-wide);
  color: var(--text-secondary);
}
.due-badge {
  color: var(--color-accent);
  font-weight: 700;
}
.collection-radio {
  width: 12px;
  height: 12px;
  flex-shrink: 0;
  border: var(--space-1) solid var(--surface-panel-border);
  background: transparent;
}
.collection-row--active .collection-radio {
  background: var(--color-accent);
  border-color: var(--color-accent);
}

.lobby-footer {
  flex-shrink: 0;
  margin-top: var(--space-5);
  padding-top: var(--space-5);
  border-top: var(--space-1) solid var(--surface-panel-border);
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}
@media (min-width: 640px) {
  .lobby-footer {
    flex-direction: row;
    align-items: flex-end;
    justify-content: space-between;
  }
}
.lobby-summary {
  min-width: 0;
  flex: 1;
}
.summary-line {
  margin: 0 0 var(--space-2);
  font-size: var(--font-size-md);
  color: var(--text-primary);
}
.block-reason {
  margin: 0 0 var(--space-2);
  font-size: var(--font-size-sm);
  color: var(--status-danger);
}
.key-hint {
  margin: 0;
  font-size: var(--font-size-2xs);
  letter-spacing: var(--tracking-wide);
  color: var(--text-disabled);
}
.lobby-cta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-4);
  flex-shrink: 0;
}
</style>
