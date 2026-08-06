<script setup lang="ts">
/**
 * Learn mode: a graded pass over one deck.
 *
 * Round 1 asks every card as multiple choice, round 2 asks the same cards as
 * written recall. Mistakes are tallied per card across both rounds and, at the
 * end, converted into a single SM-2 grade per card — so Learn mode feeds the
 * same spaced-repetition state as normal review rather than running beside it.
 */
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { apiFetch } from '@/utils/api'
import AppButton from '@/shared/components/AppButton.vue'
import PixelFrame from '@/shared/components/PixelFrame.vue'
import McqPrompt from './components/McqPrompt.vue'
import WrittenRecallPrompt from './components/WrittenRecallPrompt.vue'
import type { DeckCard } from '@/features/library/types'

const props = defineProps<{ deckId: string }>()

const { t } = useI18n()

/**
 * Mistakes -> SM-2 grade. A clean card earns a confident pass; one slip still
 * counts as recalled but with effort; two or more resets the card's momentum.
 * These sit inside the backend's documented 1-4 scale.
 */
const SCORE_CLEAN = 4
const SCORE_ONE_MISS = 3
const SCORE_STRUGGLED = 2

const MCQ_OPTION_COUNT = 4

type Round = 'mcq' | 'written' | 'done'

const cards = ref<DeckCard[]>([])
const isLoading = ref(true)
const round = ref<Round>('mcq')
const index = ref(0)
const wrongCounts = ref<Record<string, number>>({})

// Per-question transient state, reset on every advance.
const selected = ref<string | null>(null)
const verdict = ref<'correct' | 'incorrect' | null>(null)

const currentCard = computed(() => cards.value[index.value] ?? null)

const correctTotal = computed(
  () => cards.value.filter((c) => (wrongCounts.value[c.id] ?? 0) === 0).length,
)

/**
 * Distractors are drawn from the rest of the deck, so a wrong option is always
 * a plausible sibling answer rather than filler.
 */
const mcqOptions = computed(() => {
  const card = currentCard.value
  if (!card) return []

  const distractors = cards.value
    .filter((c) => c.id !== card.id)
    .map((c) => c.back)
    .filter((back, i, all) => back !== card.back && all.indexOf(back) === i)

  // Deterministic per card (id-seeded) so re-rendering doesn't reshuffle the
  // options under the user mid-question.
  const seed = card.id.charCodeAt(0) + card.id.charCodeAt(card.id.length - 1)
  const picked = distractors.slice(0, MCQ_OPTION_COUNT - 1)
  const options = [...picked, card.back]
  return options.sort(
    (a, b) => ((a.length + seed) % options.length) - ((b.length + seed) % options.length),
  )
})

function markWrong(cardId: string) {
  wrongCounts.value[cardId] = (wrongCounts.value[cardId] ?? 0) + 1
}

function selectMcq(option: string) {
  const card = currentCard.value
  if (!card || selected.value !== null) return
  selected.value = option
  if (option !== card.back) markWrong(card.id)
  // Brief pause so the correct/incorrect colouring is visible before advancing.
  window.setTimeout(advance, 900)
}

function checkWritten(answer: string) {
  const card = currentCard.value
  if (!card || verdict.value !== null) return
  const isCorrect = answer.trim().toLowerCase() === card.back.trim().toLowerCase()
  verdict.value = isCorrect ? 'correct' : 'incorrect'
  if (!isCorrect) markWrong(card.id)
}

function advance() {
  selected.value = null
  verdict.value = null

  if (index.value + 1 < cards.value.length) {
    index.value += 1
    return
  }

  index.value = 0
  if (round.value === 'mcq') {
    round.value = 'written'
  } else {
    round.value = 'done'
    void submitGrades()
  }
}

function gradeFor(cardId: string): number {
  const wrong = wrongCounts.value[cardId] ?? 0
  if (wrong === 0) return SCORE_CLEAN
  if (wrong === 1) return SCORE_ONE_MISS
  return SCORE_STRUGGLED
}

async function submitGrades() {
  await Promise.all(
    cards.value.map((card) =>
      apiFetch(`/api/cards/review/${card.id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ score: gradeFor(card.id) }),
      }).catch((err) => console.error('Failed to submit Learn grade:', err)),
    ),
  )
}

function restart() {
  round.value = 'mcq'
  index.value = 0
  wrongCounts.value = {}
  selected.value = null
  verdict.value = null
}

async function fetchCards() {
  isLoading.value = true
  try {
    const res = await apiFetch(`/api/decks/${props.deckId}/cards`)
    if (!res.ok) throw new Error('Request failed')
    cards.value = (await res.json()) as DeckCard[]
  } catch (err) {
    console.error('Failed to load deck cards:', err)
    cards.value = []
  } finally {
    isLoading.value = false
  }
}

onMounted(fetchCards)
</script>

<template>
  <div class="learn-view">
    <p v-if="isLoading" class="learn-status font-label">{{ t('learn.loading') }}</p>
    <p v-else-if="cards.length === 0" class="learn-status font-label">{{ t('learn.empty') }}</p>

    <template v-else>
      <div class="learn-top font-label">
        <span>{{ t('learn.title') }}</span>
        <span v-if="round !== 'done'">{{ index + 1 }} / {{ cards.length }}</span>
      </div>

      <PixelFrame frame-color="amber" surface="cabinet" :ring-width="3">
        <div class="learn-panel">
          <template v-if="round === 'mcq' && currentCard">
            <span class="learn-eyebrow font-label">{{ t('learn.chooseAnswer') }}</span>
            <McqPrompt
              :prompt="currentCard.front"
              :options="mcqOptions"
              :selected="selected"
              :correct-answer="currentCard.back"
              :disabled="selected !== null"
              @select="selectMcq"
            />
          </template>

          <template v-else-if="round === 'written' && currentCard">
            <span class="learn-eyebrow font-label">{{ t('learn.typeAnswer') }}</span>
            <WrittenRecallPrompt
              :prompt="currentCard.front"
              :verdict="verdict"
              :correct-answer="currentCard.back"
              @check="checkWritten"
              @next="advance"
            />
          </template>

          <div v-else class="learn-done">
            <p class="learn-done-title font-label">{{ t('learn.roundComplete') }}</p>
            <p class="learn-done-score font-body">
              {{ t('learn.score', { correct: correctTotal, total: cards.length }) }}
            </p>
            <div class="learn-done-actions">
              <AppButton variant="secondary" @click="restart">{{ t('learn.restart') }}</AppButton>
              <AppButton
                @click="$router.push({ name: 'deck-detail', params: { deckId: props.deckId } })"
              >
                {{ t('learn.backToDeck') }}
              </AppButton>
            </div>
          </div>
        </div>
      </PixelFrame>
    </template>
  </div>
</template>

<style scoped>
.learn-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-9);
  font-size: var(--font-size-md);
  color: var(--text-secondary);
}
.learn-panel {
  padding: var(--space-11) var(--space-10);
}
.learn-eyebrow {
  display: block;
  font-size: var(--font-size-sm);
  letter-spacing: var(--tracking-normal);
  color: var(--text-label-accent);
  margin-bottom: var(--space-8);
  text-align: center;
}
.learn-done {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-7);
  text-align: center;
}
.learn-done-title {
  font-size: var(--font-size-xl);
  color: var(--status-success);
  margin: 0;
}
.learn-done-score {
  font-size: var(--font-size-lg);
  color: var(--text-primary);
  margin: 0;
}
.learn-done-actions {
  display: flex;
  gap: var(--space-6);
  flex-wrap: wrap;
  justify-content: center;
}
.learn-status {
  color: var(--text-secondary);
  font-size: var(--font-size-md);
  text-align: center;
  padding: var(--space-11) 0;
}
</style>
