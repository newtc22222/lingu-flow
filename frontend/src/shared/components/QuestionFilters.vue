<script setup lang="ts">
/**
 * Filter bar for the question bank.
 *
 * Lives in `shared/` rather than `features/question-bank/` because the exam
 * composer consumes it too, and cross-feature imports are forbidden by
 * `.context/ui-guidelines.md`.
 */
import { useI18n } from 'vue-i18n'
import AppButton from './AppButton.vue'
import {
  DIFFICULTIES,
  EXAM_TYPES,
  type QuestionFilterState,
} from '@/features/question-bank/types'

const props = defineProps<{
  modelValue: QuestionFilterState
  availableTags: string[]
  availableParts: string[]
  hasActiveFilters: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: QuestionFilterState): void
  (e: 'reset'): void
}>()

const { t } = useI18n()

function patch(changes: Partial<QuestionFilterState>) {
  emit('update:modelValue', { ...props.modelValue, ...changes })
}

function toggleTag(tag: string) {
  const tags = props.modelValue.tags.includes(tag)
    ? props.modelValue.tags.filter((existing) => existing !== tag)
    : [...props.modelValue.tags, tag]
  patch({ tags })
}
</script>

<template>
  <div class="qf">
    <div class="qf-row">
      <div class="arcade-field qf-field">
        <label class="arcade-label" for="qf-exam-type">{{ t('questionBank.examType') }}</label>
        <select
          id="qf-exam-type"
          class="arcade-input"
          :value="modelValue.examType"
          @change="patch({ examType: ($event.target as HTMLSelectElement).value, part: '' })"
        >
          <option value="">{{ t('questionBank.anyExamType') }}</option>
          <option v-for="type in EXAM_TYPES" :key="type" :value="type">
            {{ type.toUpperCase() }}
          </option>
        </select>
      </div>

      <div class="arcade-field qf-field">
        <label class="arcade-label" for="qf-part">{{ t('questionBank.part') }}</label>
        <select
          id="qf-part"
          class="arcade-input"
          :value="modelValue.part"
          @change="patch({ part: ($event.target as HTMLSelectElement).value })"
        >
          <option value="">{{ t('questionBank.anyPart') }}</option>
          <option v-for="part in availableParts" :key="part" :value="part">{{ part }}</option>
        </select>
      </div>

      <div class="arcade-field qf-field">
        <label class="arcade-label" for="qf-difficulty">{{ t('questionBank.difficulty') }}</label>
        <select
          id="qf-difficulty"
          class="arcade-input"
          :value="modelValue.difficulty"
          @change="patch({ difficulty: ($event.target as HTMLSelectElement).value })"
        >
          <option value="">{{ t('questionBank.anyDifficulty') }}</option>
          <option v-for="level in DIFFICULTIES" :key="level" :value="level">
            {{ t(`questionBank.difficulties.${level}`) }}
          </option>
        </select>
      </div>

      <div class="arcade-field qf-field qf-field--wide">
        <label class="arcade-label" for="qf-search">{{ t('questionBank.search') }}</label>
        <input
          id="qf-search"
          type="search"
          class="arcade-input"
          :value="modelValue.search"
          @input="patch({ search: ($event.target as HTMLInputElement).value })"
        />
      </div>
    </div>

    <div v-if="availableTags.length" class="qf-tags">
      <span class="qf-tags-label font-label">{{ t('questionBank.tags') }}</span>
      <button
        v-for="tag in availableTags"
        :key="tag"
        type="button"
        class="qf-tag font-label"
        :class="{ 'qf-tag--active': modelValue.tags.includes(tag) }"
        :aria-pressed="modelValue.tags.includes(tag)"
        @click="toggleTag(tag)"
      >
        {{ tag }}
      </button>
    </div>

    <div v-if="hasActiveFilters" class="qf-actions">
      <AppButton variant="secondary" @click="emit('reset')">
        {{ t('questionBank.clearFilters') }}
      </AppButton>
    </div>
  </div>
</template>

<style scoped>
.qf {
  display: flex;
  flex-direction: column;
  gap: var(--space-7);
  margin-bottom: var(--space-9);
}
.qf-row {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-6);
}
.qf-field {
  flex: 1;
  min-width: 140px;
}
.qf-field--wide {
  min-width: 200px;
}
.qf-tags {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-4);
}
.qf-tags-label {
  font-size: var(--font-size-2xs);
  letter-spacing: var(--tracking-normal);
  color: var(--text-secondary);
}
.qf-tag {
  background: var(--surface-panel-border);
  border: var(--space-1) solid var(--surface-panel-border);
  color: var(--text-secondary);
  font-size: var(--font-size-2xs);
  letter-spacing: var(--tracking-tight);
  padding: var(--space-2) var(--space-5);
  cursor: pointer;
}
.qf-tag:hover:not(.qf-tag--active) {
  color: var(--text-primary);
  border-color: var(--muted);
}
.qf-tag--active {
  background: var(--state-selected-bg);
  border-color: var(--state-selected-bg);
  color: var(--text-on-accent);
}
.qf-actions {
  display: flex;
  justify-content: flex-end;
}
.qf-tag:focus-visible,
.arcade-input:focus-visible {
  outline: var(--focus-ring-width) solid var(--color-focus-ring);
  outline-offset: 2px;
}
select.arcade-input {
  font-family: var(--font-body);
}
</style>
