<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import AppButton from '@/shared/components/AppButton.vue'
import ManageListShell from '@/shared/components/ManageListShell.vue'
import QuestionFilters from '@/shared/components/QuestionFilters.vue'
import QuestionForm from './components/QuestionForm.vue'
import { useQuestionBankStore } from './store/questionBankStore'
import type { BankQuestion } from './types'

const { t } = useI18n()
const store = useQuestionBankStore()

const editing = ref<BankQuestion | null>(null)
const isSaving = ref(false)
const formError = ref<string | null>(null)

/**
 * Two-step inline delete rather than a third native `confirm()`.
 * `.context/ui-guidelines.md` calls the two existing confirm() sites a known
 * gap not to be extended, and asks that a third be flagged rather than added.
 * A real ConfirmDialog is filed as its own follow-up.
 */
const pendingDeleteId = ref<string | null>(null)

async function refresh() {
  await Promise.all([store.fetchQuestions(), store.fetchFacets()])
}

// Re-query whenever a filter changes; the facet lists are scoped to exam type.
watch(
  () => store.filters,
  () => {
    void store.fetchQuestions()
  },
  { deep: true },
)
watch(
  () => store.filters.examType,
  () => {
    void store.fetchFacets()
  },
)

function startEdit(question: BankQuestion) {
  if (!question.isOwned) return
  editing.value = question
  formError.value = null
  pendingDeleteId.value = null
}

function cancelEdit() {
  editing.value = null
  formError.value = null
}

async function save(payload: Record<string, unknown>) {
  isSaving.value = true
  formError.value = null
  try {
    if (editing.value) {
      await store.updateQuestion(editing.value.id, payload)
      editing.value = null
    } else {
      await store.createQuestion(payload)
    }
  } catch (err) {
    // Surfaces the API's own 409 wording, e.g. why an answered question's key
    // is frozen — a generic message would leave the user stuck.
    formError.value = err instanceof Error ? err.message : t('questionBank.saveFailed')
  } finally {
    isSaving.value = false
  }
}

async function confirmDelete(id: string) {
  try {
    await store.deleteQuestion(id)
  } catch (err) {
    formError.value = err instanceof Error ? err.message : t('questionBank.deleteFailed')
  } finally {
    pendingDeleteId.value = null
  }
}

onMounted(refresh)
</script>

<template>
  <ManageListShell
    :title="t('questionBank.title')"
    :count-label="t('questionBank.countLabel')"
    :count="store.questions.length"
    :is-loading="store.isLoading"
    :loading-text="t('questionBank.loading')"
    :empty-text="store.hasActiveFilters ? t('questionBank.emptyFiltered') : t('questionBank.empty')"
    :rows="store.questions"
    :can-modify="(q: BankQuestion) => q.isOwned"
    @edit="startEdit"
    @delete="(id: string) => (pendingDeleteId = id)"
  >
    <template #form>
      <QuestionForm
        :question="editing"
        :is-saving="isSaving"
        :error="formError"
        @submit="save"
        @cancel="cancelEdit"
      />

      <QuestionFilters
        v-model="store.filters"
        :available-tags="store.availableTags"
        :available-parts="store.availableParts"
        :has-active-filters="store.hasActiveFilters"
        @reset="store.resetFilters"
      />

      <p v-if="store.error" class="qb-error font-label">{{ store.error }}</p>
    </template>

    <template #row="{ item }">
      <div class="qb-meta font-label">
        <span class="qb-chip">{{ item.examType.toUpperCase() }}</span>
        <span v-if="item.part" class="qb-chip">{{ item.part }}</span>
        <span class="qb-chip qb-chip--muted">{{ t(`questionBank.difficulties.${item.difficulty}`) }}</span>
        <span v-if="item.passageGroup" class="qb-chip qb-chip--muted">
          {{ t('questionBank.inSet') }}
        </span>
        <span v-if="!item.isOwned" class="qb-chip qb-chip--locked">
          {{ t('questionBank.builtIn') }}
        </span>
      </div>

      <div class="qb-text font-body">{{ item.questionText }}</div>

      <div v-if="item.tags?.length" class="qb-tags font-label">
        <span v-for="tag in item.tags" :key="tag" class="qb-tag">{{ tag }}</span>
      </div>

      <div v-if="pendingDeleteId === item.id" class="qb-confirm">
        <span class="qb-confirm-text font-body">{{ t('questionBank.confirmDelete') }}</span>
        <AppButton variant="secondary" @click="pendingDeleteId = null">
          {{ t('common.cancel') }}
        </AppButton>
        <AppButton variant="danger" @click="confirmDelete(item.id)">
          {{ t('common.delete') }}
        </AppButton>
      </div>
    </template>
  </ManageListShell>
</template>

<style scoped>
.qb-meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
  margin-bottom: var(--space-4);
}
.qb-chip {
  font-size: var(--font-size-2xs);
  letter-spacing: var(--tracking-normal);
  color: var(--text-label-accent);
  border: var(--space-1) solid var(--surface-panel-border);
  padding: var(--space-1) var(--space-4);
}
.qb-chip--muted {
  color: var(--text-secondary);
}
.qb-chip--locked {
  color: var(--text-disabled);
  border-color: var(--text-disabled);
}
.qb-text {
  font-size: var(--font-size-md-plus);
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.qb-tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
  margin-top: var(--space-4);
}
.qb-tag {
  font-size: var(--font-size-2xs);
  letter-spacing: var(--tracking-tight);
  color: var(--text-secondary);
}
.qb-confirm {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-5);
  margin-top: var(--space-6);
  padding-top: var(--space-5);
  border-top: var(--space-1) solid var(--status-danger-subtle);
}
.qb-confirm-text {
  font-size: var(--font-size-md);
  color: var(--status-danger);
}
.qb-error {
  color: var(--status-danger);
  font-size: var(--font-size-md);
  margin: 0 0 var(--space-7);
}
</style>
