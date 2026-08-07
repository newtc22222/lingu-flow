<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { apiFetch } from '@/utils/api';
import AppButton from '@/shared/components/AppButton.vue';
import PixelFrame from '@/shared/components/PixelFrame.vue';
import CardRow from './components/CardRow.vue';
import type { DeckCard } from './types';

const props = defineProps<{ deckId: string }>();

const { t } = useI18n();

const deckName = ref('');
const cards = ref<DeckCard[]>([]);
const isLoading = ref(true);
const notFound = ref(false);
const isSavingOrder = ref(false);
const orderSaved = ref(false);

/** Index currently being dragged, or null when no drag is in flight. */
const draggingIndex = ref<number | null>(null);

/** The order differs from what the server last confirmed. */
const savedOrder = ref<string[]>([]);
const isDirty = computed(
  () =>
    cards.value.length === savedOrder.value.length &&
    cards.value.some((card, i) => card.id !== savedOrder.value[i]),
);

async function fetchDeck() {
  isLoading.value = true;
  notFound.value = false;
  try {
    // There is no GET /api/decks/{id}; the list endpoint is the only source of
    // deck metadata, so the name is looked up from it.
    const [decksRes, cardsRes] = await Promise.all([
      apiFetch('/api/decks'),
      apiFetch(`/api/decks/${props.deckId}/cards`),
    ]);
    if (!decksRes.ok || !cardsRes.ok) throw new Error('Request failed');

    const decks = (await decksRes.json()) as { id: string; name: string }[];
    const deck = decks.find((d) => d.id === props.deckId);
    if (!deck) {
      notFound.value = true;
      return;
    }
    deckName.value = deck.name;
    cards.value = (await cardsRes.json()) as DeckCard[];
    savedOrder.value = cards.value.map((c) => c.id);
  } catch (err) {
    console.error('Failed to load deck:', err);
    notFound.value = true;
  } finally {
    isLoading.value = false;
  }
}

function onDragStart(index: number) {
  draggingIndex.value = index;
  orderSaved.value = false;
}

/** Live-reorders as the pointer crosses each row, so the list previews the drop. */
function onDragEnter(index: number) {
  const from = draggingIndex.value;
  if (from === null || from === index) return;
  const [moved] = cards.value.splice(from, 1);
  cards.value.splice(index, 0, moved);
  draggingIndex.value = index;
}

function onDragEnd() {
  draggingIndex.value = null;
}

async function saveOrder() {
  isSavingOrder.value = true;
  try {
    const res = await apiFetch(`/api/decks/${props.deckId}/cards/reorder`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ cardIds: cards.value.map((c) => c.id) }),
    });
    if (!res.ok) throw new Error('Request failed');
    cards.value = (await res.json()) as DeckCard[];
    savedOrder.value = cards.value.map((c) => c.id);
    orderSaved.value = true;
  } catch (err) {
    console.error('Failed to save card order:', err);
  } finally {
    isSavingOrder.value = false;
  }
}

onMounted(fetchDeck);
</script>

<template>
  <div class="deck-detail">
    <p v-if="isLoading" class="dd-status font-label">{{ t('deckDetail.loading') }}</p>
    <p v-else-if="notFound" class="dd-status dd-status--error font-label">
      {{ t('deckDetail.notFound') }}
    </p>

    <template v-else>
      <div class="dd-header">
        <h1 class="dd-title font-label">{{ deckName }}</h1>
        <div class="dd-actions">
          <AppButton
            variant="secondary"
            @click="$router.push({ name: 'learn', params: { deckId: props.deckId } })"
          >
            {{ t('deckDetail.startLearn') }}
          </AppButton>
          <AppButton
            variant="secondary"
            @click="$router.push({ name: 'match', params: { deckId: props.deckId } })"
          >
            {{ t('deckDetail.startMatch') }}
          </AppButton>
        </div>
      </div>

      <p v-if="cards.length === 0" class="dd-status font-label">{{ t('deckDetail.empty') }}</p>

      <template v-else>
        <div class="dd-reorder-bar">
          <span class="dd-hint font-body">{{ t('deckDetail.reorderHint') }}</span>
          <span v-if="orderSaved && !isDirty" class="dd-saved font-label">
            {{ t('deckDetail.orderSaved') }}
          </span>
          <AppButton :disabled="!isDirty || isSavingOrder" @click="saveOrder">
            {{ t('deckDetail.saveOrder') }}
          </AppButton>
        </div>

        <PixelFrame surface="cabinet" :ring-width="3">
          <ol class="dd-list">
            <CardRow
              v-for="(card, index) in cards"
              :key="card.id"
              :card="card"
              :index="index"
              :is-dragging="draggingIndex === index"
              @dragstart="onDragStart(index)"
              @dragenter="onDragEnter(index)"
              @dragend="onDragEnd"
            />
          </ol>
        </PixelFrame>
      </template>
    </template>
  </div>
</template>

<style scoped>
.dd-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--space-7);
  margin-bottom: var(--space-9);
}
.dd-title {
  font-size: var(--font-size-xl);
  font-weight: 700;
  color: var(--color-accent);
  margin: 0;
}
.dd-actions {
  display: flex;
  gap: var(--space-5);
}
.dd-reorder-bar {
  display: flex;
  align-items: center;
  gap: var(--space-7);
  flex-wrap: wrap;
  margin-bottom: var(--space-7);
}
.dd-hint {
  flex: 1;
  min-width: 200px;
  font-size: var(--font-size-md);
  color: var(--text-secondary);
}
.dd-saved {
  font-size: var(--font-size-sm);
  color: var(--status-success);
}
.dd-list {
  list-style: none;
  margin: 0;
  padding: 0;
}
.dd-status {
  color: var(--text-secondary);
  font-size: var(--font-size-md);
  text-align: center;
  padding: var(--space-11) 0;
}
.dd-status--error {
  color: var(--status-danger);
}
</style>
