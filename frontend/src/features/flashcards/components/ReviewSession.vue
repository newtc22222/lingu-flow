<script setup lang="ts">
/**
 * Binary know / don't-know review pass over a preloaded due-card queue.
 * Parent owns fetch + filtering; this component only flips, grades, and advances.
 */
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { apiFetch } from '@/utils/api';
import FlashCard from './FlashCard.vue';
import DeckProgress from './DeckProgress.vue';
import AppButton from '@/shared/components/AppButton.vue';

export interface ReviewCard {
  id: string;
  front: string;
  back: string;
  deckId?: string | null;
  deckName?: string;
}

const props = defineProps<{
  cards: ReviewCard[];
}>();

const emit = defineEmits<{
  exit: [];
  complete: [];
}>();

/** Binary poles of the backend 1–4 SM-2 scale. */
const SCORE_DONT_KNOW = 1;
const SCORE_KNOW = 4;

const { t } = useI18n();

const currentIndex = ref(0);
const flipped = ref(false);

const currentCard = computed(() => props.cards[currentIndex.value] ?? null);
const deckLabel = computed(() => {
  const name = currentCard.value?.deckName?.trim();
  if (name) return name.toUpperCase();
  return t('flashcards.reviewDeckFallback');
});
const isDone = computed(() => currentIndex.value >= props.cards.length);

watch(
  () => props.cards,
  () => {
    currentIndex.value = 0;
    flipped.value = false;
  },
);

async function submitReview(score: number) {
  if (!currentCard.value) return;
  try {
    await apiFetch(`/api/cards/review/${currentCard.value.id}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ score }),
    });
  } catch (err) {
    console.error('Failed to submit review:', err);
  } finally {
    flipped.value = false;
    currentIndex.value += 1;
    if (currentIndex.value >= props.cards.length) {
      emit('complete');
    }
  }
}

function onKeyDown(e: KeyboardEvent) {
  if (['INPUT', 'TEXTAREA'].includes((e.target as HTMLElement).tagName)) return;
  if (e.code === 'Escape') {
    e.preventDefault();
    emit('exit');
    return;
  }
  if (e.code === 'Space' && currentCard.value && !isDone.value) {
    e.preventDefault();
    flipped.value = !flipped.value;
  }
  if (!flipped.value || isDone.value) return;
  if (e.key === '1' || e.code === 'Digit1') {
    e.preventDefault();
    void submitReview(SCORE_DONT_KNOW);
  }
  if (e.key === '2' || e.code === 'Digit2') {
    e.preventDefault();
    void submitReview(SCORE_KNOW);
  }
}

onMounted(() => {
  window.addEventListener('keydown', onKeyDown);
});
onUnmounted(() => {
  window.removeEventListener('keydown', onKeyDown);
});
</script>

<template>
  <div class="review-session">
    <div class="review-top">
      <AppButton variant="secondary" @click="emit('exit')">
        {{ t('flashcards.backToLobby') }}
      </AppButton>
      <div class="review-meta font-label">
        <span>{{ t('flashcards.deckLabel', { name: deckLabel }) }}</span>
        <DeckProgress :total="cards.length" :current-index="Math.min(currentIndex, cards.length)" />
      </div>
    </div>

    <div v-if="isDone" class="review-done">
      <p class="review-done-title font-body">{{ t('flashcards.reviewComplete') }}</p>
      <p class="review-done-sub font-label">
        {{ t('flashcards.reviewCompleteSub', { count: cards.length }) }}
      </p>
      <AppButton @click="emit('complete')">{{ t('flashcards.backToLobby') }}</AppButton>
    </div>

    <template v-else-if="currentCard">
      <FlashCard
        :front="currentCard.front"
        :back="currentCard.back"
        :flipped="flipped"
        @toggle="flipped = !flipped"
      />

      <div class="review-actions">
        <AppButton variant="danger" :disabled="!flipped" @click="submitReview(SCORE_DONT_KNOW)">
          ✕ {{ t('flashcards.unknown') }}
        </AppButton>
        <AppButton variant="primary" :disabled="!flipped" @click="submitReview(SCORE_KNOW)">
          ✓ {{ t('flashcards.known') }}
        </AppButton>
      </div>
      <p class="review-keys font-label">{{ t('flashcards.reviewKeys') }}</p>
    </template>
  </div>
</template>

<style scoped>
.review-session {
  flex: 1 1 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-7);
  max-width: 720px;
  margin: 0 auto;
  width: 100%;
  box-sizing: border-box;
  padding: var(--space-8) var(--space-9);
}

.review-top {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
  flex-shrink: 0;
}
.review-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-5);
  font-size: var(--font-size-md);
  color: var(--text-secondary);
  flex-wrap: wrap;
}

.review-actions {
  display: flex;
  gap: var(--space-6);
  justify-content: center;
  flex-wrap: wrap;
}
.review-keys {
  margin: 0;
  text-align: center;
  font-size: var(--font-size-2xs);
  letter-spacing: var(--tracking-wide);
  color: var(--text-disabled);
}

.review-done {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-6);
  text-align: center;
  padding: var(--space-11) 0;
}
.review-done-title {
  margin: 0;
  font-size: var(--font-size-xl);
  font-weight: 700;
  color: var(--color-accent);
}
.review-done-sub {
  margin: 0;
  font-size: var(--font-size-md);
  color: var(--text-secondary);
}
</style>
