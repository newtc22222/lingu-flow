import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { apiFetch } from '@/utils/api'
import { emptyFilters, type BankQuestion, type QuestionFilterState } from '../types'

/**
 * The question bank.
 *
 * Every call checks `res.ok` before touching state — silently treating a failed
 * request as success is exactly the bug that made a failed exam submission look
 * like a 0% score (issue #32).
 */
export const useQuestionBankStore = defineStore('questionBank', () => {
  const questions = ref<BankQuestion[]>([])
  const availableTags = ref<string[]>([])
  const availableParts = ref<string[]>([])
  const filters = ref<QuestionFilterState>(emptyFilters())
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  const hasActiveFilters = computed(
    () =>
      Boolean(filters.value.examType) ||
      Boolean(filters.value.part) ||
      Boolean(filters.value.difficulty) ||
      Boolean(filters.value.search) ||
      filters.value.tags.length > 0,
  )

  function buildQuery(overrides: Partial<QuestionFilterState> = {}): string {
    const f = { ...filters.value, ...overrides }
    const params = new URLSearchParams()
    if (f.examType) params.set('examType', f.examType)
    if (f.part) params.set('part', f.part)
    if (f.difficulty) params.set('difficulty', f.difficulty)
    if (f.search) params.set('search', f.search)
    // Repeated key, not CSV — FastAPI reads `tags` as a list of query params.
    for (const tag of f.tags) params.append('tags', tag)
    return params.toString()
  }

  async function fetchQuestions() {
    isLoading.value = true
    error.value = null
    try {
      const query = buildQuery()
      const res = await apiFetch(`/api/questions${query ? `?${query}` : ''}`)
      if (!res.ok) throw new Error(`Request failed (${res.status})`)
      questions.value = (await res.json()) as BankQuestion[]
    } catch (err) {
      console.error('Failed to load questions:', err)
      error.value = err instanceof Error ? err.message : 'Failed to load questions'
      questions.value = []
    } finally {
      isLoading.value = false
    }
  }

  /** Tag and part lists that populate the filter controls. */
  async function fetchFacets() {
    try {
      const scope = filters.value.examType ? `?examType=${filters.value.examType}` : ''
      const [tagsRes, partsRes] = await Promise.all([
        apiFetch(`/api/questions/tags${scope}`),
        apiFetch(`/api/questions/parts${scope}`),
      ])
      if (tagsRes.ok) availableTags.value = (await tagsRes.json()) as string[]
      if (partsRes.ok) availableParts.value = (await partsRes.json()) as string[]
    } catch (err) {
      console.error('Failed to load question facets:', err)
    }
  }

  async function createQuestion(payload: Record<string, unknown>) {
    const res = await apiFetch('/api/questions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    if (!res.ok) throw new Error(await describeFailure(res))
    await fetchQuestions()
  }

  async function updateQuestion(id: string, payload: Record<string, unknown>) {
    const res = await apiFetch(`/api/questions/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    if (!res.ok) throw new Error(await describeFailure(res))
    await fetchQuestions()
  }

  async function deleteQuestion(id: string) {
    const res = await apiFetch(`/api/questions/${id}`, { method: 'DELETE' })
    if (!res.ok) throw new Error(await describeFailure(res))
    await fetchQuestions()
  }

  /** Surface the API's own message — 409s explain why an edit was refused. */
  async function describeFailure(res: Response): Promise<string> {
    try {
      const body = await res.json()
      return body?.detail || `Request failed (${res.status})`
    } catch {
      return `Request failed (${res.status})`
    }
  }

  function resetFilters() {
    filters.value = emptyFilters()
  }

  return {
    questions,
    availableTags,
    availableParts,
    filters,
    isLoading,
    error,
    hasActiveFilters,
    fetchQuestions,
    fetchFacets,
    createQuestion,
    updateQuestion,
    deleteQuestion,
    resetFilters,
  }
})
