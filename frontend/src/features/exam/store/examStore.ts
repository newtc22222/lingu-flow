import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { apiFetch } from '@/utils/api'

export interface ExamQuestion {
  id: string
  domain?: string
  type?: string
  passage?: string
  questionText: string
  codeSnippet?: string
  options: string[]
}

export type ExamPhase = 'idle' | 'loading' | 'in-progress' | 'submitting' | 'finished' | 'error'

/** Answer keys map 1:1 to option index (0 -> A, 1 -> B, ...). */
export const OPTION_KEYS = ['A', 'B', 'C', 'D'] as const

/**
 * Countdown is timestamp-based (`deadlineAt`), not a naive per-tick
 * decrement — `secondsRemaining` is always recomputed from `Date.now()` so
 * it can't drift if the tab is throttled in the background. This store is
 * the single source of truth for exam time; components only ever read
 * `secondsRemaining` / `progressPercent`, they never run their own timer.
 */
export const useExamStore = defineStore('exam', () => {
  const phase = ref<ExamPhase>('idle')
  const sessionId = ref<string | null>(null)
  const examTitle = ref('')
  const domain = ref('')
  const questions = ref<ExamQuestion[]>([])
  const currentIndex = ref(0)
  const answers = ref<Record<string, string>>({})
  const lives = ref(3)
  const maxLives = ref(3)
  const totalSeconds = ref(0)
  const secondsRemaining = ref(0)
  const deadlineAt = ref<number | null>(null)
  const finishedSessionId = ref<string | null>(null)
  const error = ref<string | null>(null)
  let tickHandle: number | null = null

  const currentQuestion = computed(() => questions.value[currentIndex.value] ?? null)
  const answeredCount = computed(() => Object.values(answers.value).filter(Boolean).length)
  const progressPercent = computed(() =>
    totalSeconds.value > 0 ? (secondsRemaining.value / totalSeconds.value) * 100 : 100,
  )
  /** Boss-bar HUD drops into the --red palette once under 20% time remains. */
  const isLowTime = computed(
    () => totalSeconds.value > 0 && secondsRemaining.value / totalSeconds.value < 0.2,
  )
  const timeDisplay = computed(() => {
    const m = Math.floor(secondsRemaining.value / 60)
    const s = secondsRemaining.value % 60
    return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
  })
  /** Once finished/submitting, answers and navigation are frozen — no undo, no continuing. */
  const isLocked = computed(() => phase.value === 'finished' || phase.value === 'submitting')

  function stopClock() {
    if (tickHandle !== null) {
      window.clearInterval(tickHandle)
      tickHandle = null
    }
  }

  function tick() {
    if (deadlineAt.value === null || phase.value !== 'in-progress') return
    const remainingMs = deadlineAt.value - Date.now()
    secondsRemaining.value = Math.max(0, Math.ceil(remainingMs / 1000))
    if (remainingMs <= 0) {
      void finish('timeout')
    }
  }

  function startClock() {
    stopClock()
    tickHandle = window.setInterval(tick, 250)
  }

  async function start(templateId: string) {
    stopClock()
    phase.value = 'loading'
    error.value = null
    questions.value = []
    answers.value = {}
    currentIndex.value = 0
    finishedSessionId.value = null

    try {
      const sessionRes = await apiFetch('/api/exams/sessions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ examTemplateId: templateId }),
      })
      if (!sessionRes.ok) throw new Error('Could not start exam session')
      const sessionData = await sessionRes.json()

      const [questionsRes, templateRes] = await Promise.all([
        apiFetch(`/api/exams/templates/${templateId}/questions`),
        apiFetch(`/api/exams/templates/${templateId}`),
      ])
      if (!questionsRes.ok || !templateRes.ok) throw new Error('Could not load exam content')

      const rawQuestions = await questionsRes.json()
      const template = await templateRes.json()

      questions.value = (rawQuestions as Record<string, unknown>[]).map((q) => ({
        id: (q.id ?? q._id) as string,
        domain: q.domain as string | undefined,
        type: q.type as string | undefined,
        passage: q.passage as string | undefined,
        questionText: q.questionText as string,
        codeSnippet: q.codeSnippet as string | undefined,
        options: (q.options as string[]) ?? [],
      }))

      sessionId.value = (sessionData.id ?? sessionData._id) as string
      examTitle.value = template.name
      domain.value = template.domain ?? ''
      maxLives.value = sessionData.maxLives ?? 3
      lives.value = maxLives.value
      totalSeconds.value = (sessionData.timeLimit ?? template.duration ?? 60) * 60
      secondsRemaining.value = totalSeconds.value
      deadlineAt.value = Date.now() + totalSeconds.value * 1000

      phase.value = 'in-progress'
      startClock()
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to start exam'
      phase.value = 'error'
    }
  }

  function selectAnswer(optionKey: string) {
    if (isLocked.value || !currentQuestion.value || !sessionId.value) return
    const qId = currentQuestion.value.id
    answers.value[qId] = optionKey
    apiFetch(`/api/exams/sessions/${sessionId.value}/answer`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ questionId: qId, userAnswer: optionKey }),
    }).catch((err) => console.error('Failed to save answer', err))
  }

  function goToQuestion(index: number) {
    if (isLocked.value) return
    if (index >= 0 && index < questions.value.length) currentIndex.value = index
  }
  function next() {
    goToQuestion(currentIndex.value + 1)
  }
  function previous() {
    goToQuestion(currentIndex.value - 1)
  }

  async function finish(reason: 'submitted' | 'timeout' = 'submitted') {
    if (!sessionId.value || phase.value === 'submitting' || phase.value === 'finished') return
    phase.value = 'submitting'
    stopClock()
    try {
      await apiFetch(`/api/exams/sessions/${sessionId.value}/finish`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: 'completed', autoSubmitted: reason === 'timeout' }),
      })
      finishedSessionId.value = sessionId.value
      phase.value = 'finished'
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to submit exam'
      phase.value = 'error'
    }
  }

  /** Call from the owning view's onUnmounted so a stale interval never outlives the component. */
  function teardown() {
    stopClock()
  }

  return {
    phase,
    sessionId,
    examTitle,
    domain,
    questions,
    currentIndex,
    answers,
    lives,
    maxLives,
    totalSeconds,
    secondsRemaining,
    finishedSessionId,
    error,
    currentQuestion,
    answeredCount,
    progressPercent,
    isLowTime,
    timeDisplay,
    isLocked,
    start,
    selectAnswer,
    goToQuestion,
    next,
    previous,
    finish,
    teardown,
  }
})
