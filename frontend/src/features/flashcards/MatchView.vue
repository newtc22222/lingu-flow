<script setup lang="ts">
/**
 * Match minigame: pair each term with its definition against the clock.
 *
 * Deliberately read-only with respect to learning state — it fetches the deck
 * and then makes no further API calls, and never submits an SM-2 grade. It is a
 * warm-up game, not a review, so playing it must not move any card's schedule.
 */
import { computed, onMounted, onUnmounted, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { apiFetch } from '@/utils/api';
import AppButton from '@/shared/components/AppButton.vue';
import PixelFrame from '@/shared/components/PixelFrame.vue';
import type { DeckCard } from '@/features/library/types';

const props = defineProps<{ deckId: string }>();

const { t } = useI18n();

/** Cards per game — a full deck would make the grid unplayable. */
const MAX_PAIRS = 6;

interface Tile {
  key: string;
  cardId: string;
  label: string;
  side: 'term' | 'definition';
}

const cards = ref<DeckCard[]>([]);
const isLoading = ref(true);
const tiles = ref<Tile[]>([]);
const matchedIds = ref<Set<string>>(new Set());
const selectedKey = ref<string | null>(null);
/** Briefly set on a bad pair so both tiles can flash red. */
const wrongKeys = ref<string[]>([]);

const elapsedMs = ref(0);
const isComplete = ref(false);
let startedAt = 0;
let tickHandle: number | null = null;

const timeDisplay = computed(() => {
  const total = Math.floor(elapsedMs.value / 1000);
  const m = String(Math.floor(total / 60)).padStart(2, '0');
  const s = String(total % 60).padStart(2, '0');
  return `${m}:${s}`;
});

function stopClock() {
  if (tickHandle !== null) {
    window.clearInterval(tickHandle);
    tickHandle = null;
  }
}

function startClock() {
  stopClock();
  startedAt = Date.now();
  elapsedMs.value = 0;
  // Recomputed from the start timestamp rather than incremented, so a throttled
  // background tab can't make the clock drift.
  tickHandle = window.setInterval(() => {
    elapsedMs.value = Date.now() - startedAt;
  }, 250);
}

function shuffle<T>(items: T[]): T[] {
  const out = [...items];
  for (let i = out.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [out[i], out[j]] = [out[j], out[i]];
  }
  return out;
}

function newGame() {
  const picked = shuffle(cards.value).slice(0, MAX_PAIRS);
  tiles.value = shuffle(
    picked.flatMap((card) => [
      { key: `${card.id}-t`, cardId: card.id, label: card.front, side: 'term' as const },
      { key: `${card.id}-d`, cardId: card.id, label: card.back, side: 'definition' as const },
    ]),
  );
  matchedIds.value = new Set();
  selectedKey.value = null;
  wrongKeys.value = [];
  isComplete.value = false;
  startClock();
}

function tileFor(key: string | null) {
  return key === null ? null : (tiles.value.find((tile) => tile.key === key) ?? null);
}

function selectTile(tile: Tile) {
  if (isComplete.value || matchedIds.value.has(tile.cardId)) return;
  if (wrongKeys.value.length) return;

  const previous = tileFor(selectedKey.value);
  if (!previous) {
    selectedKey.value = tile.key;
    return;
  }
  if (previous.key === tile.key) {
    selectedKey.value = null;
    return;
  }

  // A pair is only valid across sides — two terms never match each other.
  if (previous.cardId === tile.cardId && previous.side !== tile.side) {
    matchedIds.value = new Set([...matchedIds.value, tile.cardId]);
    selectedKey.value = null;
    if (matchedIds.value.size === tiles.value.length / 2) {
      isComplete.value = true;
      stopClock();
    }
    return;
  }

  wrongKeys.value = [previous.key, tile.key];
  window.setTimeout(() => {
    wrongKeys.value = [];
    selectedKey.value = null;
  }, 500);
}

async function fetchCards() {
  isLoading.value = true;
  try {
    const res = await apiFetch(`/api/decks/${props.deckId}/cards`);
    if (!res.ok) throw new Error('Request failed');
    cards.value = (await res.json()) as DeckCard[];
    if (cards.value.length >= 2) newGame();
  } catch (err) {
    console.error('Failed to load deck cards:', err);
    cards.value = [];
  } finally {
    isLoading.value = false;
  }
}

onMounted(fetchCards);
onUnmounted(stopClock);
</script>

<template>
  <div class="match-view">
    <p v-if="isLoading" class="match-status font-label">{{ t('match.loading') }}</p>
    <p v-else-if="cards.length < 2" class="match-status font-label">{{ t('match.empty') }}</p>

    <template v-else>
      <div class="match-top font-label">
        <span>{{ t('match.title') }}</span>
        <span>{{ t('match.time') }}: {{ timeDisplay }}</span>
      </div>

      <p class="match-hint font-body">{{ t('match.instructions') }}</p>

      <PixelFrame v-if="isComplete" frame-color="amber" surface="cabinet" :ring-width="3">
        <div class="match-done">
          <p class="match-done-title font-label">{{ t('match.complete') }}</p>
          <p class="match-done-time font-body">{{ t('match.finalTime', { time: timeDisplay }) }}</p>
          <div class="match-done-actions">
            <AppButton variant="secondary" @click="newGame">{{ t('match.playAgain') }}</AppButton>
            <AppButton
              @click="$router.push({ name: 'deck-detail', params: { deckId: props.deckId } })"
            >
              {{ t('match.backToDeck') }}
            </AppButton>
          </div>
        </div>
      </PixelFrame>

      <div v-else class="match-grid">
        <button
          v-for="tile in tiles"
          :key="tile.key"
          type="button"
          class="match-tile font-body"
          :class="{
            'match-tile--matched': matchedIds.has(tile.cardId),
            'match-tile--selected': selectedKey === tile.key,
            'match-tile--wrong': wrongKeys.includes(tile.key),
          }"
          :disabled="matchedIds.has(tile.cardId)"
          @click="selectTile(tile)"
        >
          {{ tile.label }}
        </button>
      </div>
    </template>
  </div>
</template>

<style scoped>
.match-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-6);
  font-size: var(--font-size-md);
  color: var(--text-secondary);
}
.match-hint {
  font-size: var(--font-size-md);
  color: var(--text-secondary);
  margin: 0 0 var(--space-9);
}
.match-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-5);
}
@media (min-width: 640px) {
  .match-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}
.match-tile {
  min-height: 88px;
  padding: var(--space-7);
  background: var(--surface-panel);
  border: var(--space-1) solid var(--surface-panel-border);
  color: var(--text-primary);
  font-size: var(--font-size-md);
  cursor: pointer;
  transition:
    background 0.12s,
    border-color 0.12s,
    opacity 0.2s;
}
.match-tile:hover:not(:disabled) {
  background: var(--state-hover-surface);
  border-color: var(--color-accent);
}
.match-tile--selected {
  background: var(--state-selected-surface);
  border-color: var(--color-accent);
}
.match-tile--wrong {
  border-color: var(--status-danger);
  background: var(--status-danger-subtle);
}
.match-tile--matched {
  opacity: 0;
  pointer-events: none;
}
.match-tile:focus-visible {
  outline: var(--focus-ring-width) solid var(--color-focus-ring);
  outline-offset: 2px;
}
.match-done {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-7);
  padding: var(--space-11) var(--space-10);
  text-align: center;
}
.match-done-title {
  font-size: var(--font-size-xl);
  color: var(--status-success);
  margin: 0;
}
.match-done-time {
  font-size: var(--font-size-lg);
  color: var(--text-primary);
  margin: 0;
}
.match-done-actions {
  display: flex;
  gap: var(--space-6);
  flex-wrap: wrap;
  justify-content: center;
}
.match-status {
  color: var(--text-secondary);
  font-size: var(--font-size-md);
  text-align: center;
  padding: var(--space-11) 0;
}

@media (prefers-reduced-motion: reduce) {
  .match-tile {
    transition: none;
  }
}
</style>
