<script setup lang="ts">
/**
 * Row *content* for a card inside KeyboardGridList (or a plain list).
 *
 * The shell owns the <li>, drag listeners, and focus ring. This component
 * only renders the handle, index, term/definition cells, and optional
 * reorder controls. Parent owns the card array and is the only place that
 * can reorder it.
 */
import { useI18n } from 'vue-i18n';
import type { DeckCard } from '../types';

withDefaults(
  defineProps<{
    card: DeckCard;
    index: number;
    isDragging?: boolean;
    /** When false, hide the grab handle and drop grab cursor (Unfiled / filtered). */
    isReorderable?: boolean;
  }>(),
  {
    isDragging: false,
    isReorderable: true,
  },
);

const emit = defineEmits<{
  (e: 'move-up'): void;
  (e: 'move-down'): void;
}>();

const { t } = useI18n();
</script>

<template>
  <div
    class="card-row"
    :class="{
      'card-row--dragging': isDragging,
      'card-row--static': !isReorderable,
    }"
  >
    <span v-if="isReorderable" class="card-row-handle font-label" aria-hidden="true">⠿</span>
    <span class="card-row-index font-label">{{ String(index + 1).padStart(2, '0') }}</span>

    <div v-if="isReorderable" class="card-row-controls">
      <button
        type="button"
        class="card-row-control font-label"
        :aria-label="t('common.moveUp')"
        tabindex="-1"
        @click.stop="emit('move-up')"
      >
        ▲
      </button>
      <button
        type="button"
        class="card-row-control font-label"
        :aria-label="t('common.moveDown')"
        tabindex="-1"
        @click.stop="emit('move-down')"
      >
        ▼
      </button>
    </div>

    <div class="card-row-body">
      <div class="card-row-cell">
        <span class="card-row-eyebrow font-label">{{ t('deckDetail.term') }}</span>
        <span class="card-row-text font-body">{{ card.front }}</span>
      </div>
      <div class="card-row-cell">
        <span class="card-row-eyebrow card-row-eyebrow--back font-label">
          {{ t('deckDetail.definition') }}
        </span>
        <span class="card-row-text font-body">{{ card.back }}</span>
      </div>
    </div>

    <img v-if="card.imageUrl" :src="card.imageUrl" alt="" class="card-row-image" />
  </div>
</template>

<style scoped>
.card-row {
  display: flex;
  align-items: center;
  gap: var(--space-6);
  min-width: 0;
}
.card-row--static {
  cursor: default;
}
.card-row--dragging {
  opacity: 0.5;
}
.card-row-handle {
  color: var(--text-secondary);
  font-size: var(--font-size-lg);
  flex-shrink: 0;
}
.card-row-index {
  min-width: 24px;
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  flex-shrink: 0;
}
.card-row-controls {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  flex-shrink: 0;
}
.card-row-control {
  background: transparent;
  border: var(--space-1) solid var(--surface-panel-border);
  color: var(--text-secondary);
  font-size: var(--font-size-2xs);
  line-height: 1;
  padding: var(--space-1) var(--space-2);
  cursor: pointer;
}
.card-row-control:hover {
  border-color: var(--color-accent);
  color: var(--color-accent);
}
.card-row-control:focus-visible {
  outline: var(--focus-ring-width) solid var(--color-focus-ring);
  outline-offset: 2px;
}
.card-row-body {
  flex: 1;
  min-width: 0;
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--space-5);
}
@media (min-width: 640px) {
  .card-row-body {
    grid-template-columns: 1fr 1fr;
  }
}
.card-row-cell {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}
.card-row-eyebrow {
  font-size: var(--font-size-2xs);
  letter-spacing: var(--tracking-normal);
  color: var(--text-label-accent);
}
.card-row-eyebrow--back {
  color: var(--status-success);
}
.card-row-text {
  font-size: var(--font-size-md-plus);
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.card-row-image {
  width: 44px;
  height: 44px;
  object-fit: cover;
  flex-shrink: 0;
}
</style>
