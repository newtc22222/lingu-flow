<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { apiFetch } from '@/utils/api'
import FlashCard from './components/FlashCard.vue'
import DeckProgress from './components/DeckProgress.vue'

interface Card {
  id: string
  front: string
  back: string
  deckName?: string
}

/**
 * The binary "chưa thuộc / đã thuộc" review UI simplifies the SM-2 grading
 * scale down to its two clearest poles for quick arcade-style review.
 * DONT_KNOW maps to the lowest grade (full reset), KNOW to a confident pass.
 * Revisit these constants if the backend's SM-2 scale changes.
 */
const SCORE_DONT_KNOW = 1
const SCORE_KNOW = 4

const cards = ref<Card[]>([])
const currentIndex = ref(0)
const flipped = ref(false)
const isLoading = ref(true)
const error = ref<string | null>(null)

const currentCard = computed(() => cards.value[currentIndex.value] ?? null)
const deckName = computed(() => currentCard.value?.deckName?.toUpperCase() ?? 'ÔN TẬP HÔM NAY')

async function fetchCards() {
  isLoading.value = true
  error.value = null
  try {
    const res = await apiFetch('/api/cards/study')
    if (!res.ok) throw new Error('Request failed')
    const raw = (await res.json()) as Record<string, unknown>[]
    cards.value = raw.map((c) => ({
      id: (c.id ?? c._id) as string,
      front: c.front as string,
      back: c.back as string,
      deckName: c.deckName as string | undefined,
    }))
  } catch (err) {
    console.error('Failed to fetch cards:', err)
    error.value = 'Không thể tải thẻ. Vui lòng thử lại sau.'
  } finally {
    isLoading.value = false
  }
}

async function submitReview(score: number) {
  if (!currentCard.value) return
  try {
    await apiFetch(`/api/cards/review/${currentCard.value.id}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ score }),
    })
  } catch (err) {
    console.error('Failed to submit review:', err)
  } finally {
    flipped.value = false
    currentIndex.value++
  }
}

function onKeyDown(e: KeyboardEvent) {
  if (['INPUT', 'TEXTAREA'].includes((e.target as HTMLElement).tagName)) return
  if (e.code === 'Space' && currentCard.value) {
    e.preventDefault()
    flipped.value = !flipped.value
  }
}

onMounted(() => {
  void fetchCards()
  window.addEventListener('keydown', onKeyDown)
})
onUnmounted(() => {
  window.removeEventListener('keydown', onKeyDown)
})
</script>

<template>
  <div class="flashcards-view">
    <div v-if="isLoading" class="fc-status font-label">▸ ĐANG TẢI THẺ…</div>
    <div v-else-if="error" class="fc-status fc-status--error font-label">{{ error }}</div>

    <template v-else-if="currentCard">
      <div class="fc-top font-label">
        <span>DECK: {{ deckName }}</span>
        <DeckProgress :total="cards.length" :current-index="currentIndex" />
      </div>

      <FlashCard :front="currentCard.front" :back="currentCard.back" :flipped="flipped" @toggle="flipped = !flipped" />

      <div class="fc-actions">
        <button type="button" class="btn-fc no font-label" @click="submitReview(SCORE_DONT_KNOW)">
          ✕ CHƯA THUỘC
        </button>
        <button type="button" class="btn-fc yes font-label" @click="submitReview(SCORE_KNOW)">
          ✓ ĐÃ THUỘC
        </button>
      </div>
    </template>

    <div v-else class="fc-status font-label">▸ ĐÃ ÔN XONG TẤT CẢ THẺ HÔM NAY</div>
  </div>
</template>

<style scoped>
.fc-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-9);
  font-size: var(--font-size-md);
  color: var(--text-secondary);
}
.fc-actions {
  display: flex;
  gap: var(--space-6);
  justify-content: center;
}
.btn-fc {
  font-weight: 700;
  font-size: var(--font-size-base);
  letter-spacing: var(--tracking-normal);
  text-transform: uppercase;
  border: none;
  padding: var(--space-7) var(--space-9);
  cursor: pointer;
}
.btn-fc.no {
  background: var(--status-danger);
  color: var(--text-on-accent);
  box-shadow: 0 4px 0 var(--status-danger-subtle);
}
.btn-fc.yes {
  background: var(--status-success);
  color: var(--text-on-accent);
  box-shadow: 0 4px 0 var(--status-success-subtle);
}
.btn-fc:active {
  transform: translateY(4px);
  box-shadow: none;
}
.fc-status {
  color: var(--text-secondary);
  font-size: var(--font-size-md);
  text-align: center;
  padding: 40px 0;
}
.fc-status--error {
  color: var(--status-danger);
}
</style>
