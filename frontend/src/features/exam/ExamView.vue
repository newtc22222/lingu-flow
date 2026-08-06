<script setup lang="ts">
import { computed, onMounted, onUnmounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import ExamHud from './components/ExamHud.vue'
import QuestionCard from './components/QuestionCard.vue'
import { useExamStore } from './store/examStore'

const props = defineProps<{ templateId: string }>()

const { t } = useI18n()
const router = useRouter()
const store = useExamStore()

const isLastQuestion = computed(() => store.currentIndex === store.questions.length - 1)

function handleSubmit() {
  if (isLastQuestion.value) {
    void store.finish()
  } else {
    store.next()
  }
}

function onKeyDown(e: KeyboardEvent) {
  if (['INPUT', 'TEXTAREA'].includes((e.target as HTMLElement).tagName)) return
  if (store.isLocked) return
  switch (e.key.toUpperCase()) {
    case 'A':
    case 'B':
    case 'C':
    case 'D':
      store.selectAnswer(e.key.toUpperCase())
      break
    case 'ENTER':
      handleSubmit()
      break
    case 'ARROWLEFT':
      store.previous()
      break
    case 'ARROWRIGHT':
      if (store.answers[store.currentQuestion?.id ?? '']) store.next()
      break
  }
}

watch(
  () => store.phase,
  (phase) => {
    if (phase === 'finished' && store.finishedSessionId) {
      void router.replace({
        name: 'exam-results',
        params: { sessionId: store.finishedSessionId },
      })
    }
  },
)

onMounted(() => {
  void store.start(props.templateId)
  window.addEventListener('keydown', onKeyDown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKeyDown)
  store.teardown()
})
</script>

<template>
  <div class="exam-view">
    <template v-if="store.phase === 'loading'">
      <p class="exam-loading font-label">{{ t('exam.loadingExam') }}</p>
    </template>

    <template v-else-if="store.phase === 'error'">
      <p class="exam-error font-label">{{ store.error ?? t('exam.loadFailed') }}</p>
    </template>

    <template v-else-if="store.currentQuestion">
      <!-- font-label, not font-pixel: exam names are user-supplied and may
           carry Vietnamese diacritics Press Start 2P cannot render. -->
      <p class="exam-title font-label">{{ store.examTitle.toUpperCase() }}</p>

      <ExamHud />

      <div class="exam-meta font-label">
        <span>
          {{ t('exam.question', { current: store.currentIndex + 1, total: store.questions.length }) }}
        </span>
      </div>

      <QuestionCard
        :question="store.currentQuestion"
        :selected-answer="store.answers[store.currentQuestion.id]"
        :disabled="store.isLocked"
        :is-last-question="isLastQuestion"
        @select="store.selectAnswer"
        @submit="handleSubmit"
      />
    </template>
  </div>
</template>

<style scoped>
.exam-title {
  font-size: var(--font-size-base);
  color: var(--text-secondary);
  margin: 0 0 var(--space-8);
  letter-spacing: var(--tracking-tight);
}
.exam-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-7);
  font-size: var(--font-size-md);
  color: var(--text-secondary);
}
.exam-loading,
.exam-error {
  color: var(--text-secondary);
  font-size: var(--font-size-md);
}
.exam-error {
  color: var(--status-danger);
}
</style>
