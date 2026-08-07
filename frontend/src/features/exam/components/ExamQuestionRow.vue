<script setup lang="ts">
/**
 * One draggable question in an exam's composition.
 *
 * Drag events are forwarded to the parent, which owns the array and is the
 * only place that can reorder it — same split as CardRow in the deck detail
 * view.
 *
 * The action here is DETACH, not delete: the question stays in the bank and in
 * any other exam using it. The wording has to make that unambiguous, because
 * the bank's own delete sits one screen away and means something else.
 */
import { useI18n } from 'vue-i18n';
import AppButton from '@/shared/components/AppButton.vue';
import type { TemplateQuestion } from '@/features/question-bank/types';

defineProps<{
  question: TemplateQuestion;
  index: number;
  isDragging: boolean;
}>();

defineEmits<{
  (e: 'dragstart'): void;
  (e: 'dragenter'): void;
  (e: 'dragend'): void;
  (e: 'detach'): void;
  (e: 'move-up'): void;
  (e: 'move-down'): void;
}>();

const { t } = useI18n();
</script>

<template>
  <li
    class="eq-row"
    :class="{ 'eq-row--dragging': isDragging }"
    draggable="true"
    @dragstart="$emit('dragstart')"
    @dragenter.prevent="$emit('dragenter')"
    @dragover.prevent
    @dragend="$emit('dragend')"
  >
    <span class="eq-handle font-label" aria-hidden="true">⠿</span>
    <span class="eq-index font-label">{{ index + 1 }}</span>

    <div class="eq-controls">
      <button
        class="eq-control font-label"
        :aria-label="t('common.moveUp')"
        @click.stop="$emit('move-up')"
      >
        ▲
      </button>
      <button
        class="eq-control font-label"
        :aria-label="t('common.moveDown')"
        @click.stop="$emit('move-down')"
      >
        ▼
      </button>
    </div>

    <div class="eq-body">
      <div class="eq-meta font-label">
        <span class="eq-chip">{{ question.examType.toUpperCase() }}</span>
        <span v-if="question.part" class="eq-chip">{{ question.part }}</span>
        <span v-if="question.passageGroup" class="eq-chip eq-chip--set">
          {{ t('composer.partOfSet') }}
        </span>
      </div>
      <span class="eq-text font-body">{{ question.questionText }}</span>
    </div>

    <AppButton variant="delete" @click="$emit('detach')">
      {{ t('composer.removeFromExam') }}
    </AppButton>
  </li>
</template>

<style scoped>
.eq-row {
  display: flex;
  align-items: center;
  gap: var(--space-6);
  padding: var(--space-6) var(--space-8);
  border-left: var(--border-width-accent) solid var(--surface-panel-border);
  border-bottom: var(--space-1) solid var(--surface-page);
  cursor: grab;
}
.eq-row:hover {
  background: var(--state-hover-surface);
  border-left-color: var(--color-accent);
}
.eq-row--dragging {
  opacity: 0.5;
  cursor: grabbing;
}
.eq-handle {
  color: var(--text-secondary);
  font-size: var(--font-size-lg);
}
.eq-index {
  min-width: 24px;
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}
.eq-controls {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.eq-control {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 2px;
  font-size: var(--font-size-2xs);
}
.eq-control:hover {
  color: var(--color-accent);
}
.eq-control:focus-visible {
  outline: var(--focus-ring-width) solid var(--color-focus-ring);
  outline-offset: 1px;
}
.eq-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}
.eq-meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
}
.eq-chip {
  font-size: var(--font-size-2xs);
  letter-spacing: var(--tracking-normal);
  color: var(--text-label-accent);
  border: var(--space-1) solid var(--surface-panel-border);
  padding: var(--space-1) var(--space-4);
}
.eq-chip--set {
  color: var(--status-caution);
  border-color: var(--status-caution);
}
.eq-text {
  font-size: var(--font-size-md-plus);
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.eq-row:focus-visible {
  outline: var(--focus-ring-width) solid var(--color-focus-ring);
  outline-offset: 2px;
}
</style>
