<script setup lang="ts">
/**
 * Compose an exam from the question bank.
 *
 * Step 1 collects the template metadata; step 2 composes its questions by
 * attaching existing bank questions, creating new ones inline, reordering, and
 * detaching.
 *
 * Behavioural difference from the wizard this replaces: attaching needs a
 * template id, so step 1 POSTs the template on "Next" rather than deferring
 * creation to a final save. That means abandoning the flow at step 2 would
 * leave an empty draft exam behind, so an explicit discard action deletes it.
 */
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { apiFetch } from '@/utils/api'
import AppButton from '@/shared/components/AppButton.vue'
import PixelFrame from '@/shared/components/PixelFrame.vue'
import QuestionFilters from '@/shared/components/QuestionFilters.vue'
import QuestionForm from '@/features/question-bank/components/QuestionForm.vue'
import { useQuestionBankStore } from '@/features/question-bank/store/questionBankStore'
import { EXAM_TYPES, type TemplateQuestion } from '@/features/question-bank/types'
import ExamQuestionRow from './components/ExamQuestionRow.vue'

const props = defineProps<{ templateId?: string }>()

const { t } = useI18n()
const router = useRouter()
const bank = useQuestionBankStore()

const step = ref<1 | 2>(1)
const isLoading = ref(false)
const isSaving = ref(false)
const error = ref<string | null>(null)

/** Set once the template exists server-side; also what edit mode starts with. */
const templateId = ref<string | null>(props.templateId ?? null)
/** True when we created the template in this session and it has no questions
 *  yet — the only case where leaving should offer to discard it. */
const isFreshDraft = ref(false)

const form = ref({
  name: '',
  examType: 'toeic',
  description: '',
  durationMinutes: 30,
  passingScore: 70,
  level: '',
})

const composition = ref<TemplateQuestion[]>([])
const draggingIndex = ref<number | null>(null)
const savedOrder = ref<string[]>([])
const isSavingOrder = ref(false)
const showInlineForm = ref(false)
const selectedIds = ref<Set<string>>(new Set())

const isEditMode = computed(() => Boolean(props.templateId))
const step1Valid = computed(
  () => form.value.name.trim().length >= 3 && form.value.durationMinutes > 0,
)
const isDirtyOrder = computed(
  () =>
    composition.value.length === savedOrder.value.length &&
    composition.value.some((q, i) => q.id !== savedOrder.value[i]),
)

/** Bank questions not already in this exam. */
const attachable = computed(() => {
  const present = new Set(composition.value.map((q) => q.id))
  return bank.questions.filter((q) => !present.has(q.id))
})

async function describeFailure(res: Response): Promise<string> {
  try {
    const body = await res.json()
    return body?.detail || `Request failed (${res.status})`
  } catch {
    return `Request failed (${res.status})`
  }
}

async function loadComposition() {
  if (!templateId.value) return
  const res = await apiFetch(`/api/exams/templates/${templateId.value}/questions`)
  if (!res.ok) throw new Error(await describeFailure(res))
  composition.value = (await res.json()) as TemplateQuestion[]
  savedOrder.value = composition.value.map((q) => q.id)
}

async function loadTemplate(id: string) {
  isLoading.value = true
  try {
    const res = await apiFetch(`/api/exams/templates/${id}`)
    if (!res.ok) throw new Error(await describeFailure(res))
    const template = await res.json()
    form.value = {
      name: template.name ?? '',
      examType: template.examType ?? 'toeic',
      description: template.description ?? '',
      durationMinutes: template.durationMinutes ?? 30,
      passingScore: template.passingScore ?? 70,
      level: template.level ?? '',
    }
    await loadComposition()
    step.value = 2
  } catch (err) {
    error.value = err instanceof Error ? err.message : t('examCreator.saveFailed')
  } finally {
    isLoading.value = false
  }
}

/** Create (or update) the template, then move to composition. */
async function goToStep2() {
  if (!step1Valid.value) return
  isSaving.value = true
  error.value = null
  try {
    const res = await apiFetch(
      templateId.value ? `/api/exams/templates/${templateId.value}` : '/api/exams/templates',
      {
        method: templateId.value ? 'PUT' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form.value),
      },
    )
    if (!res.ok) throw new Error(await describeFailure(res))
    const template = await res.json()
    if (!templateId.value) isFreshDraft.value = true
    templateId.value = template.id
    await loadComposition()
    step.value = 2
  } catch (err) {
    error.value = err instanceof Error ? err.message : t('examCreator.saveFailed')
  } finally {
    isSaving.value = false
  }
}

function toggleSelected(id: string) {
  const next = new Set(selectedIds.value)
  if (next.has(id)) next.delete(id)
  else next.add(id)
  selectedIds.value = next
}

async function attachSelected() {
  if (!templateId.value || selectedIds.value.size === 0) return
  error.value = null
  try {
    const res = await apiFetch(
      `/api/exams/templates/${templateId.value}/questions/attach`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ questionIds: [...selectedIds.value] }),
      },
    )
    if (!res.ok) throw new Error(await describeFailure(res))
    composition.value = (await res.json()) as TemplateQuestion[]
    savedOrder.value = composition.value.map((q) => q.id)
    selectedIds.value = new Set()
    isFreshDraft.value = false
  } catch (err) {
    error.value = err instanceof Error ? err.message : t('composer.attachFailed')
  }
}

async function detach(questionId: string) {
  if (!templateId.value) return
  error.value = null
  try {
    const res = await apiFetch(
      `/api/exams/templates/${templateId.value}/questions/${questionId}`,
      { method: 'DELETE' },
    )
    if (!res.ok) throw new Error(await describeFailure(res))
    await loadComposition()
  } catch (err) {
    error.value = err instanceof Error ? err.message : t('composer.detachFailed')
  }
}

function onDragStart(index: number) {
  draggingIndex.value = index
}
function onDragEnter(index: number) {
  const from = draggingIndex.value
  if (from === null || from === index) return
  const [moved] = composition.value.splice(from, 1)
  composition.value.splice(index, 0, moved)
  draggingIndex.value = index
}
function onDragEnd() {
  draggingIndex.value = null
}

async function saveOrder() {
  if (!templateId.value) return
  isSavingOrder.value = true
  error.value = null
  try {
    const res = await apiFetch(
      `/api/exams/templates/${templateId.value}/questions/reorder`,
      {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ questionIds: composition.value.map((q) => q.id) }),
      },
    )
    if (!res.ok) throw new Error(await describeFailure(res))
    composition.value = (await res.json()) as TemplateQuestion[]
    savedOrder.value = composition.value.map((q) => q.id)
  } catch (err) {
    error.value = err instanceof Error ? err.message : t('composer.reorderFailed')
  } finally {
    isSavingOrder.value = false
  }
}

/** Create a question inline; the API attaches it to this exam in one call. */
async function createInline(payload: Record<string, unknown>) {
  if (!templateId.value) return
  isSaving.value = true
  error.value = null
  try {
    const res = await apiFetch(`/api/exams/templates/${templateId.value}/questions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    if (!res.ok) throw new Error(await describeFailure(res))
    await loadComposition()
    await bank.fetchQuestions()
    showInlineForm.value = false
    isFreshDraft.value = false
  } catch (err) {
    error.value = err instanceof Error ? err.message : t('examCreator.saveFailed')
  } finally {
    isSaving.value = false
  }
}

async function discardDraft() {
  if (templateId.value) {
    await apiFetch(`/api/exams/templates/${templateId.value}`, { method: 'DELETE' })
  }
  await router.push({ name: 'exams' })
}

async function done() {
  await router.push({ name: 'exams' })
}

onMounted(async () => {
  await Promise.all([bank.fetchQuestions(), bank.fetchFacets()])
  if (props.templateId) await loadTemplate(props.templateId)
})
</script>

<template>
  <div class="composer">
    <div class="composer-header">
      <button type="button" class="composer-back font-label" @click="done">
        {{ t('common.back') }}
      </button>
      <h1 class="composer-title font-body">
        {{ isEditMode ? t('examCreator.editTitle') : t('examCreator.createTitle') }}
      </h1>
      <div class="composer-steps" aria-hidden="true">
        <span
          v-for="s in [1, 2]"
          :key="s"
          class="composer-step font-label"
          :class="{ 'composer-step--current': step === s, 'composer-step--done': step > s }"
        >
          {{ step > s ? '✓' : s }}
        </span>
      </div>
    </div>

    <div class="composer-body">
      <p v-if="isLoading" class="composer-status font-label">{{ t('common.loading') }}</p>
      <p v-if="error" class="composer-error font-label">{{ error }}</p>

      <!-- ── Step 1: exam details ──────────────────────────────────────── -->
      <PixelFrame
        v-if="!isLoading && step === 1"
        frame-color="amber"
        surface="cabinet"
        :ring-width="3"
      >
        <div class="composer-panel">
          <div class="arcade-field">
            <label class="arcade-label" for="composer-name">{{ t('examCreator.name') }} *</label>
            <input id="composer-name" v-model="form.name" type="text" class="arcade-input" />
          </div>

          <div class="arcade-field">
            <label class="arcade-label" for="composer-type">{{ t('examCreator.examType') }}</label>
            <select id="composer-type" v-model="form.examType" class="arcade-input">
              <option v-for="type in EXAM_TYPES" :key="type" :value="type">
                {{ type.toUpperCase() }}
              </option>
            </select>
          </div>

          <div class="arcade-field">
            <label class="arcade-label" for="composer-desc">
              {{ t('examCreator.description') }}
            </label>
            <textarea
              id="composer-desc"
              v-model="form.description"
              rows="2"
              class="arcade-input"
            ></textarea>
          </div>

          <div class="composer-grid">
            <div class="arcade-field">
              <label class="arcade-label" for="composer-duration">
                {{ t('examCreator.duration') }} *
              </label>
              <input
                id="composer-duration"
                v-model.number="form.durationMinutes"
                type="number"
                min="1"
                max="300"
                class="arcade-input"
              />
            </div>
            <div class="arcade-field">
              <label class="arcade-label" for="composer-pass">
                {{ t('examCreator.passingScore') }}
              </label>
              <input
                id="composer-pass"
                v-model.number="form.passingScore"
                type="number"
                min="1"
                max="100"
                class="arcade-input"
              />
            </div>
            <div class="arcade-field">
              <label class="arcade-label" for="composer-level">{{ t('examCreator.level') }}</label>
              <input id="composer-level" v-model="form.level" type="text" class="arcade-input" />
            </div>
          </div>

          <AppButton class="composer-wide" :disabled="!step1Valid || isSaving" @click="goToStep2">
            {{ isSaving ? t('examCreator.saving') : t('composer.next') }}
          </AppButton>
        </div>
      </PixelFrame>

      <!-- ── Step 2: composition ───────────────────────────────────────── -->
      <template v-if="!isLoading && step === 2">
        <div class="composer-columns">
          <section class="composer-col">
            <div class="composer-col-head">
              <h2 class="composer-col-title font-body">
                {{ t('composer.inThisExam') }}
                <span class="composer-count font-label">({{ composition.length }})</span>
              </h2>
              <AppButton :disabled="!isDirtyOrder || isSavingOrder" @click="saveOrder">
                {{ t('deckDetail.saveOrder') }}
              </AppButton>
            </div>

            <p v-if="composition.length === 0" class="composer-status font-label">
              {{ t('composer.emptyComposition') }}
            </p>
            <template v-else>
              <p class="composer-hint font-body">{{ t('deckDetail.reorderHint') }}</p>
              <PixelFrame surface="cabinet" :ring-width="3">
                <ol class="composer-list">
                  <ExamQuestionRow
                    v-for="(question, index) in composition"
                    :key="question.id"
                    :question="question"
                    :index="index"
                    :is-dragging="draggingIndex === index"
                    @dragstart="onDragStart(index)"
                    @dragenter="onDragEnter(index)"
                    @dragend="onDragEnd"
                    @detach="detach(question.id)"
                  />
                </ol>
              </PixelFrame>
            </template>
          </section>

          <section class="composer-col">
            <div class="composer-col-head">
              <h2 class="composer-col-title font-body">{{ t('composer.fromBank') }}</h2>
              <AppButton variant="secondary" @click="showInlineForm = !showInlineForm">
                {{ showInlineForm ? t('common.cancel') : t('examCreator.addQuestion') }}
              </AppButton>
            </div>

            <QuestionForm
              v-if="showInlineForm"
              :is-saving="isSaving"
              @submit="createInline"
              @cancel="showInlineForm = false"
            />

            <QuestionFilters
              v-model="bank.filters"
              :available-tags="bank.availableTags"
              :available-parts="bank.availableParts"
              :has-active-filters="bank.hasActiveFilters"
              @reset="bank.resetFilters"
            />

            <p v-if="attachable.length === 0" class="composer-status font-label">
              {{ t('composer.noBankResults') }}
            </p>
            <template v-else>
              <ul class="composer-bank">
                <li v-for="question in attachable" :key="question.id" class="composer-bank-row">
                  <label class="composer-bank-label">
                    <input
                      type="checkbox"
                      :checked="selectedIds.has(question.id)"
                      @change="toggleSelected(question.id)"
                    />
                    <span class="composer-bank-body">
                      <span class="composer-bank-meta font-label">
                        <span class="composer-chip">{{ question.examType.toUpperCase() }}</span>
                        <span v-if="question.part" class="composer-chip">{{ question.part }}</span>
                        <span v-if="question.passageGroup" class="composer-chip composer-chip--set">
                          {{ t('composer.partOfSet') }}
                        </span>
                      </span>
                      <span class="composer-bank-text font-body">{{ question.questionText }}</span>
                    </span>
                  </label>
                </li>
              </ul>

              <AppButton
                class="composer-wide"
                :disabled="selectedIds.size === 0"
                @click="attachSelected"
              >
                {{ t('composer.attachSelected', { count: selectedIds.size }) }}
              </AppButton>
            </template>
          </section>
        </div>

        <div class="composer-footer">
          <AppButton v-if="isFreshDraft" variant="danger" @click="discardDraft">
            {{ t('composer.discardDraft') }}
          </AppButton>
          <AppButton @click="done">{{ t('composer.finish') }}</AppButton>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.composer {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.composer-header {
  display: flex;
  align-items: center;
  gap: var(--space-8);
  padding: var(--space-8) var(--space-10);
  background: var(--surface-panel);
  border-bottom: var(--space-1) solid var(--surface-panel-border);
  flex-shrink: 0;
}
.composer-back {
  background: none;
  border: none;
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
  letter-spacing: var(--tracking-normal);
  cursor: pointer;
}
.composer-back:hover {
  color: var(--text-primary);
}
.composer-title {
  font-size: var(--font-size-xl);
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}
.composer-steps {
  margin-left: auto;
  display: flex;
  gap: var(--space-3);
}
.composer-step {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--font-size-base);
  font-weight: 700;
  background: var(--surface-page);
  color: var(--text-secondary);
}
.composer-step--current {
  background: var(--state-selected-bg);
  color: var(--text-on-accent);
}
.composer-step--done {
  background: var(--status-success);
  color: var(--text-on-accent);
}
.composer-body {
  flex: 1;
  overflow-y: auto;
  max-width: 1100px;
  margin: 0 auto;
  width: 100%;
  padding: var(--space-10);
}
.composer-panel {
  padding: var(--space-10);
  display: flex;
  flex-direction: column;
  gap: var(--space-8);
}
.composer-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--space-7);
}
@media (min-width: 640px) {
  .composer-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}
.composer-columns {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--space-10);
}
@media (min-width: 900px) {
  .composer-columns {
    grid-template-columns: 1fr 1fr;
  }
}
.composer-col {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-7);
}
.composer-col-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-6);
  flex-wrap: wrap;
}
.composer-col-title {
  font-size: var(--font-size-lg);
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}
.composer-count {
  font-size: var(--font-size-sm);
  font-weight: 400;
  color: var(--text-secondary);
  margin-left: var(--space-3);
}
.composer-hint {
  font-size: var(--font-size-md);
  color: var(--text-secondary);
  margin: 0;
}
.composer-list {
  list-style: none;
  margin: 0;
  padding: 0;
}
.composer-bank {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}
.composer-bank-row {
  background: var(--surface-panel);
  border-left: var(--border-width-accent) solid var(--surface-panel-border);
}
.composer-bank-row:hover {
  border-left-color: var(--color-accent);
  background: var(--state-hover-surface);
}
.composer-bank-label {
  display: flex;
  align-items: flex-start;
  gap: var(--space-6);
  padding: var(--space-6) var(--space-7);
  cursor: pointer;
}
.composer-bank-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}
.composer-bank-meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
}
.composer-chip {
  font-size: var(--font-size-2xs);
  letter-spacing: var(--tracking-normal);
  color: var(--text-label-accent);
  border: var(--space-1) solid var(--surface-panel-border);
  padding: var(--space-1) var(--space-4);
}
.composer-chip--set {
  color: var(--status-caution);
  border-color: var(--status-caution);
}
.composer-bank-text {
  font-size: var(--font-size-md);
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.composer-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-6);
  margin-top: var(--space-11);
}
.composer-wide {
  width: 100%;
}
.composer-status {
  color: var(--text-secondary);
  font-size: var(--font-size-md);
  text-align: center;
  padding: var(--space-11) 0;
}
.composer-error {
  color: var(--status-danger);
  font-size: var(--font-size-base);
  background: var(--surface-page);
  border-left: var(--border-width-accent) solid var(--status-danger);
  padding: var(--space-5) var(--space-6);
  margin: 0 0 var(--space-8);
}
textarea.arcade-input,
select.arcade-input {
  font-family: var(--font-body);
}
.composer-back:focus-visible,
.arcade-input:focus-visible {
  outline: var(--focus-ring-width) solid var(--color-focus-ring);
  outline-offset: 2px;
}
</style>
