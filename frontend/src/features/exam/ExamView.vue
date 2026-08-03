<script setup lang="ts">
import { computed, onMounted, onUnmounted, watch } from 'vue'
import ExamHud from './components/ExamHud.vue'
import QuestionCard from './components/QuestionCard.vue'
import { useExamStore } from './store/examStore'

const props = defineProps<{ templateId: string }>()
const emit = defineEmits<{
  (e: 'done', sessionId: string): void
}>()

const store = useExamStore()

const domainLabel = computed(() => (store.currentQuestion?.domain ?? store.domain ?? '').toUpperCase())
const isLastQuestion = computed(() => store.currentIndex === store.questions.length - 1)

function handleSubmit() {
  if (isLastQuestion.value) {
    void store.finish('submitted')
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
    if (phase === 'finished' && store.finishedSessionId) emit('done', store.finishedSessionId)
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
      <p class="exam-loading font-label">▸ ĐANG TẢI ĐỀ THI…</p>
    </template>

    <template v-else-if="store.phase === 'error'">
      <p class="exam-error font-label">{{ store.error ?? 'Không thể tải bài thi.' }}</p>
    </template>

    <template v-else-if="store.currentQuestion">
      <p class="exam-title font-pixel">{{ store.examTitle.toUpperCase() }}</p>

      <ExamHud />

      <div class="exam-meta font-label">
        <span>QUESTION {{ store.currentIndex + 1 }} / {{ store.questions.length }}</span>
        <span v-if="domainLabel">DOMAIN: {{ domainLabel }}</span>
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
  letter-spacing: 0.5px;
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
