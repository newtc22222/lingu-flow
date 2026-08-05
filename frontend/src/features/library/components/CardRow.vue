<script setup lang="ts">
/**
 * One draggable term/definition row in the deck detail list.
 *
 * Drag events are forwarded to the parent rather than handled here: the parent
 * owns the card array, so it is the only place that can reorder it.
 */
import { useI18n } from 'vue-i18n'
import type { DeckCard } from '../types'

defineProps<{
  card: DeckCard
  index: number
  isDragging: boolean
}>()

defineEmits<{
  (e: 'dragstart'): void
  (e: 'dragenter'): void
  (e: 'dragend'): void
}>()

const { t } = useI18n()
</script>

<template>
  <li
    class="card-row"
    :class="{ 'card-row--dragging': isDragging }"
    draggable="true"
    @dragstart="$emit('dragstart')"
    @dragenter.prevent="$emit('dragenter')"
    @dragover.prevent
    @dragend="$emit('dragend')"
  >
    <span class="card-row-handle font-label" aria-hidden="true">⠿</span>
    <span class="card-row-index font-label">{{ index + 1 }}</span>

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
  </li>
</template>

<style scoped>
.card-row {
  display: flex;
  align-items: center;
  gap: var(--space-6);
  padding: var(--space-6) var(--space-8);
  border-left: var(--border-width-accent) solid var(--surface-panel-border);
  border-bottom: var(--space-1) solid var(--surface-page);
  cursor: grab;
}
.card-row:hover {
  background: var(--state-hover-surface);
  border-left-color: var(--color-accent);
}
.card-row--dragging {
  opacity: 0.5;
  cursor: grabbing;
}
.card-row-handle {
  color: var(--text-secondary);
  font-size: var(--font-size-lg);
}
.card-row-index {
  min-width: 24px;
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
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
.card-row:focus-visible {
  outline: var(--focus-ring-width) solid var(--color-focus-ring);
  outline-offset: 2px;
}
</style>
