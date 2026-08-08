<script setup lang="ts">
/**
 * Signature answer-sheet map for the live exam booth.
 * Numbered cells encode real question order; filled cells show saved answers.
 */
import { useI18n } from 'vue-i18n';

defineProps<{
  total: number;
  currentIndex: number;
  answers: Record<string, string>;
  questionIds: string[];
  disabled?: boolean;
}>();

const emit = defineEmits<{
  (e: 'select', index: number): void;
}>();

const { t } = useI18n();

function cellLabel(i: number) {
  return String(i + 1).padStart(2, '0');
}
</script>

<template>
  <div class="sheet" role="navigation" :aria-label="t('exam.answerSheet')">
    <div class="sheet-label font-label">{{ t('exam.answerSheet') }}</div>
    <div class="sheet-grid">
      <button
        v-for="i in total"
        :key="i - 1"
        type="button"
        class="sheet-cell font-label"
        :class="{
          'sheet-cell--current': currentIndex === i - 1,
          'sheet-cell--filled': Boolean(answers[questionIds[i - 1]]),
        }"
        :disabled="disabled"
        :aria-current="currentIndex === i - 1 ? 'step' : undefined"
        :aria-label="
          t('exam.question', { current: i, total }) +
          (answers[questionIds[i - 1]] ? ` · ${answers[questionIds[i - 1]]}` : '')
        "
        @click="emit('select', i - 1)"
      >
        {{ cellLabel(i - 1) }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.sheet {
  flex-shrink: 0;
  border-top: var(--space-1) solid var(--surface-panel-border);
  padding-top: var(--space-5);
}
.sheet-label {
  font-size: var(--font-size-2xs);
  letter-spacing: var(--tracking-wide);
  color: var(--text-secondary);
  margin-bottom: var(--space-4);
}
.sheet-grid {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
}
.sheet-cell {
  min-width: var(--space-10);
  height: var(--space-10);
  padding: 0 var(--space-3);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: var(--font-size-2xs);
  letter-spacing: var(--tracking-tight);
  color: var(--text-secondary);
  background: var(--surface-page);
  border: var(--space-1) solid var(--surface-panel-border);
  cursor: pointer;
  line-height: 1;
}
.sheet-cell:hover:not(:disabled):not(.sheet-cell--current) {
  border-color: var(--color-accent);
  color: var(--text-primary);
}
.sheet-cell--filled {
  color: var(--status-success);
  border-color: var(--status-success-subtle);
  background: var(--surface-panel);
}
.sheet-cell--current {
  color: var(--text-on-accent);
  background: var(--state-selected-bg);
  border-color: var(--state-selected-bg);
  font-weight: 700;
}
.sheet-cell:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.sheet-cell:focus-visible {
  outline: var(--focus-ring-width) solid var(--color-focus-ring);
  outline-offset: 2px;
}
</style>
