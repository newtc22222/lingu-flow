<script setup lang="ts" generic="T extends { id: string }">
/**
 * One keyboard-navigable list of rows, and nothing else.
 *
 * Owns the ARIA layout-grid wiring (grid/row/gridcell, roving tabindex),
 * optional drag reorder, the edit/delete actions, loading/empty status, and
 * the row shell (border, hover, focus ring). The list scrolls inside its own
 * container so it can sit in a fixed-height console bay.
 *
 * The header, count badge and create/edit form deliberately live OUTSIDE this
 * component — in the console header and the form bay, where they belong.
 * Re-adding chrome props here recreates the ManageListShell this replaced.
 *
 * Grid, not listbox: a listbox option may not contain interactive children,
 * and every row holds edit/delete buttons.
 */
import { useI18n } from 'vue-i18n';
import AppButton from './AppButton.vue';

const { t } = useI18n();

withDefaults(
  defineProps<{
    rows: T[];
    isLoading: boolean;
    loadingText: string;
    emptyText: string;
    /** aria-label on the grid. */
    listLabel: string;
    /** Which row holds the tab stop (controlled by the parent's roving list). */
    activeIndex?: number;
    /**
     * Optional per-row guard. Return false to disable that row's edit/delete —
     * needed where some rows aren't the viewer's to change (the synthetic
     * Unfiled row can be opened but never renamed or deleted).
     */
    canModify?: (item: T) => boolean;
    /** Makes each <li> draggable and forwards drag events to the parent. */
    draggableRows?: boolean;
  }>(),
  {
    activeIndex: -1,
    draggableRows: false,
  },
);

const emit = defineEmits<{
  (e: 'edit', item: T): void;
  (e: 'delete', id: string): void;
  (e: 'row-activate', item: T, index: number): void;
  (e: 'row-focus', index: number): void;
  (e: 'row-dragstart', index: number): void;
  (e: 'row-dragenter', index: number): void;
  (e: 'row-dragend'): void;
}>();
</script>

<template>
  <div class="grid-list-wrap">
    <div v-if="isLoading" class="grid-list-status font-label">{{ loadingText }}</div>
    <div v-else-if="rows.length === 0" class="grid-list-status font-label">{{ emptyText }}</div>

    <ul v-else class="grid-list" role="grid" :aria-label="listLabel" :aria-rowcount="rows.length">
      <li
        v-for="(item, index) in rows"
        :key="item.id"
        class="grid-row"
        :class="{ 'grid-row--active': index === activeIndex }"
        role="row"
        data-roving-item
        :aria-rowindex="index + 1"
        :tabindex="index === activeIndex ? 0 : -1"
        :draggable="draggableRows ? true : undefined"
        @focus="emit('row-focus', index)"
        @click="emit('row-focus', index)"
        @dblclick="emit('row-activate', item, index)"
        @dragstart="draggableRows && emit('row-dragstart', index)"
        @dragenter.prevent="draggableRows && emit('row-dragenter', index)"
        @dragover.prevent
        @dragend="draggableRows && emit('row-dragend')"
      >
        <div class="grid-row-info" role="gridcell">
          <slot name="row" :item="item" :index="index" />
        </div>
        <div class="grid-row-actions" role="gridcell">
          <AppButton
            variant="edit"
            :disabled="canModify ? !canModify(item) : false"
            :tabindex="-1"
            @click.stop="emit('edit', item)"
          >
            {{ t('common.edit') }}
          </AppButton>
          <AppButton
            variant="delete"
            :disabled="canModify ? !canModify(item) : false"
            :tabindex="-1"
            @click.stop="emit('delete', item.id)"
          >
            {{ t('common.delete') }}
          </AppButton>
        </div>
      </li>
    </ul>
  </div>
</template>

<style scoped>
/*
 * flex-basis auto, not 0: inside a height-constrained console bay this shrinks
 * and scrolls, and in normal document flow (mobile) it just takes its content
 * height instead of collapsing to nothing.
 */
.grid-list-wrap {
  flex: 1 1 auto;
  min-height: 0;
  overflow-x: hidden;
  overflow-y: auto;
}
.grid-list-status {
  color: var(--text-secondary);
  font-size: var(--font-size-base);
  text-align: center;
  padding: var(--space-11) 0;
}
.grid-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}
.grid-row {
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
.grid-row:hover {
  border-left-color: var(--color-accent);
  background: var(--state-hover-surface);
}
.grid-row--active:focus,
.grid-row--active:focus-visible {
  outline: var(--focus-ring-width) solid var(--color-focus-ring);
  outline-offset: -2px;
  border-left-color: var(--color-accent);
}
.grid-row-info {
  min-width: 0;
  flex: 1;
}
.grid-row-actions {
  display: flex;
  gap: var(--space-4);
  flex-shrink: 0;
}
@media (prefers-reduced-motion: reduce) {
  .grid-row {
    transition: none;
  }
}
</style>
