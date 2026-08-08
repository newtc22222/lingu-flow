<script setup lang="ts">
/**
 * Question Bank operator console (full width).
 *
 * Left: COMPOSE form. Right: SCAN filters + RESULTS list stacked.
 * Full-bleed route — height stays inside the web chrome; form and list
 * scroll independently.
 */
import { onMounted, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import AppButton from '@/shared/components/AppButton.vue';
import ConfirmDialog from '@/shared/components/ConfirmDialog.vue';
import PixelFrame from '@/shared/components/PixelFrame.vue';
import QuestionFilters from '@/shared/components/QuestionFilters.vue';
import QuestionForm from './components/QuestionForm.vue';
import { useQuestionBankStore } from './store/questionBankStore';
import type { BankQuestion } from './types';

const { t } = useI18n();
const store = useQuestionBankStore();

const editing = ref<BankQuestion | null>(null);
const isSaving = ref(false);
const formError = ref<string | null>(null);
const showDeleteConfirm = ref(false);
const pendingDeleteId = ref<string | null>(null);

async function refresh() {
  await Promise.all([store.fetchQuestions(), store.fetchFacets()]);
}

watch(
  () => store.filters,
  () => {
    void store.fetchQuestions();
  },
  { deep: true },
);
watch(
  () => store.filters.examType,
  () => {
    void store.fetchFacets();
  },
);

function startEdit(question: BankQuestion) {
  if (!question.isOwned) return;
  editing.value = question;
  formError.value = null;
}

function cancelEdit() {
  editing.value = null;
  formError.value = null;
}

async function save(payload: Record<string, unknown>) {
  isSaving.value = true;
  formError.value = null;
  try {
    if (editing.value) {
      await store.updateQuestion(editing.value.id, payload);
      editing.value = null;
    } else {
      await store.createQuestion(payload);
    }
  } catch (err) {
    formError.value = err instanceof Error ? err.message : t('questionBank.saveFailed');
  } finally {
    isSaving.value = false;
  }
}

function requestDelete(id: string) {
  pendingDeleteId.value = id;
  showDeleteConfirm.value = true;
}

async function confirmDelete() {
  const id = pendingDeleteId.value;
  if (!id) return;
  try {
    await store.deleteQuestion(id);
    if (editing.value?.id === id) cancelEdit();
  } catch (err) {
    formError.value = err instanceof Error ? err.message : t('questionBank.deleteFailed');
  } finally {
    pendingDeleteId.value = null;
  }
}

function cancelDelete() {
  pendingDeleteId.value = null;
}

onMounted(refresh);
</script>

<template>
  <div class="qb-page">
    <header class="qb-header">
      <h1 class="qb-title font-body">{{ t('questionBank.title') }}</h1>
      <span v-if="!store.isLoading" class="qb-count font-label">
        {{ store.questions.length }} {{ t('questionBank.countLabel') }}
      </span>
    </header>

    <p v-if="store.error" class="qb-error font-body" role="alert">{{ store.error }}</p>

    <div class="qb-body">
      <!-- Left: compose form -->
      <section class="qb-compose" :aria-label="t('questionBank.composeBay')">
        <div class="qb-section-label font-label">{{ t('questionBank.composeBay') }}</div>
        <PixelFrame frame-color="amber" surface="cabinet" :ring-width="3" class="qb-compose-frame">
          <div class="qb-compose-scroll">
            <QuestionForm
              :question="editing"
              :is-saving="isSaving"
              :error="formError"
              :framed="false"
              @submit="save"
              @cancel="cancelEdit"
            />
          </div>
        </PixelFrame>
      </section>

      <!-- Right: filters + question list -->
      <div class="qb-right">
        <section class="qb-scan" :aria-label="t('questionBank.scanBay')">
          <div class="qb-section-label font-label">{{ t('questionBank.scanBay') }}</div>
          <PixelFrame
            frame-color="cabinet-light"
            surface="cabinet"
            :ring-width="3"
            class="qb-scan-frame"
          >
            <div class="qb-scan-body">
              <QuestionFilters
                v-model="store.filters"
                :available-tags="store.availableTags"
                :available-parts="store.availableParts"
                :has-active-filters="store.hasActiveFilters"
                @reset="store.resetFilters"
              />
            </div>
          </PixelFrame>
        </section>

        <section class="qb-results" :aria-label="t('questionBank.resultsLabel')">
          <div class="qb-results-head">
            <h2 class="qb-section-label font-label">{{ t('questionBank.resultsLabel') }}</h2>
          </div>

          <div class="qb-results-scroll">
            <p v-if="store.isLoading" class="qb-status font-label">
              {{ t('questionBank.loading') }}
            </p>
            <p v-else-if="store.questions.length === 0" class="qb-status font-label">
              {{
                store.hasActiveFilters ? t('questionBank.emptyFiltered') : t('questionBank.empty')
              }}
            </p>

            <ul v-else class="qb-list">
              <li v-for="item in store.questions" :key="item.id" class="qb-row">
                <div class="qb-row-info">
                  <div class="qb-meta font-label">
                    <span class="qb-chip">{{ item.examType.toUpperCase() }}</span>
                    <span v-if="item.part" class="qb-chip">{{ item.part }}</span>
                    <span class="qb-chip qb-chip--muted">{{
                      t(`questionBank.difficulties.${item.difficulty}`)
                    }}</span>
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
                </div>
                <div class="qb-row-actions">
                  <AppButton variant="edit" :disabled="!item.isOwned" @click="startEdit(item)">
                    {{ t('common.edit') }}
                  </AppButton>
                  <AppButton
                    variant="delete"
                    :disabled="!item.isOwned"
                    @click="requestDelete(item.id)"
                  >
                    {{ t('common.delete') }}
                  </AppButton>
                </div>
              </li>
            </ul>
          </div>
        </section>
      </div>
    </div>

    <ConfirmDialog
      v-model:is-open="showDeleteConfirm"
      :title="t('questionBank.confirmDeleteTitle')"
      :message="t('questionBank.confirmDelete')"
      :confirm-text="t('common.delete')"
      variant="danger"
      @confirm="confirmDelete"
      @cancel="cancelDelete"
    />
  </div>
</template>

<style scoped>
.qb-page {
  flex: 1 1 0;
  min-height: 0;
  width: 100%;
  box-sizing: border-box;
  /* stylelint-disable-next-line scale-unlimited/declaration-strict-value -- full-width console padding */
  padding: 20px var(--space-9) var(--space-8);
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
  overflow: hidden;
}

.qb-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-6);
  flex-shrink: 0;
  flex-wrap: wrap;
}
.qb-title {
  font-size: var(--font-size-xl);
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}
.qb-count {
  font-size: var(--font-size-base);
  font-weight: 700;
  letter-spacing: var(--tracking-normal);
  color: var(--color-accent);
  background: var(--surface-page);
  border: var(--space-1) solid var(--color-accent);
  padding: var(--space-2) var(--space-5);
}

.qb-error {
  color: var(--status-danger);
  font-size: var(--font-size-md);
  margin: 0;
  flex-shrink: 0;
}

/* Main split: form left | filters+list right */
.qb-body {
  flex: 1 1 0;
  min-height: 0;
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--space-7);
  overflow: hidden;
}
@media (min-width: 768px) {
  .qb-body {
    grid-template-columns: minmax(0, 2fr) minmax(0, 3fr);
    align-items: stretch;
  }
}

.qb-section-label {
  font-size: var(--font-size-2xs);
  letter-spacing: var(--tracking-wide);
  color: var(--text-secondary);
  margin: 0 0 var(--space-3);
  flex-shrink: 0;
}

/* Left column — compose */
.qb-compose {
  display: flex;
  flex-direction: column;
  min-height: 0;
  min-width: 0;
  /* Cap height on stacked mobile so right column still gets space */
  max-height: 50vh;
}
@media (min-width: 768px) {
  .qb-compose {
    max-height: none;
    height: 100%;
  }
}
.qb-compose .qb-section-label {
  color: var(--text-label-accent);
}
.qb-compose-frame {
  flex: 1 1 auto;
  min-height: 0;
  overflow: hidden;
}
.qb-compose-scroll {
  height: 100%;
  max-height: 46vh;
  overflow-x: hidden;
  overflow-y: auto;
}
@media (min-width: 768px) {
  .qb-compose-scroll {
    max-height: none;
    /* Fill remaining column under the section label */
    height: calc(100% - var(--space-8));
  }
}

/* Right column — scan + results */
.qb-right {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
  min-height: 0;
  min-width: 0;
  overflow: hidden;
}

.qb-scan {
  flex-shrink: 0;
  min-width: 0;
}
.qb-scan-frame {
  overflow: hidden;
}
.qb-scan-body {
  padding: var(--space-7);
}
/* Horizontal filter row on the wide right pane (not compact vertical) */
.qb-scan-body :deep(.qf) {
  margin-bottom: 0;
}

.qb-results {
  flex: 1 1 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.qb-results-head {
  flex-shrink: 0;
}
.qb-results-scroll {
  flex: 1 1 0;
  min-height: 0;
  overflow-x: hidden;
  overflow-y: auto;
}

.qb-status {
  color: var(--text-secondary);
  font-size: var(--font-size-base);
  text-align: center;
  padding: var(--space-11) 0;
  margin: 0;
}

.qb-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}
.qb-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-8);
  background: var(--surface-panel);
  border-left: var(--border-width-accent) solid var(--surface-panel-border);
  padding: var(--space-7) var(--space-8);
  transition:
    border-color 0.12s,
    background 0.12s;
}
.qb-row:hover {
  border-left-color: var(--color-accent);
  background: var(--state-hover-surface);
}
@media (prefers-reduced-motion: reduce) {
  .qb-row {
    transition: none;
  }
}
.qb-row-info {
  min-width: 0;
  flex: 1;
}
.qb-row-actions {
  display: flex;
  gap: var(--space-4);
  flex-shrink: 0;
}

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
</style>
