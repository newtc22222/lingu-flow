<script setup lang="ts" generic="T extends { id: string }">
/**
 * Shared shell for the "create/edit form + list of rows with edit/delete"
 * pattern. Owns the header/count badge, loading/empty status text, row shell
 * (border, hover, spacing), and the edit/delete action buttons. Form area and
 * row info content stay slotted.
 *
 * Optional `rowNavigation` / `draggableRows` flags turn on keyboard roving and
 * drag reorder without forking the list chrome. Tripwire: a fifth opt-in flag
 * means split into chrome + a thin SortableRows wrapper — do not add a sixth prop.
 */
import { useI18n } from 'vue-i18n';
import AppButton from './AppButton.vue';

const { t } = useI18n();

withDefaults(
  defineProps<{
    title: string;
    countLabel: string;
    count: number;
    isLoading: boolean;
    loadingText: string;
    emptyText: string;
    rows: T[];
    /**
     * Optional per-row guard. Return false to disable that row's edit/delete
     * buttons — needed where some rows aren't the viewer's to change (the
     * question bank shows built-in content nobody owns, and offering actions
     * that can only 404 is worse than not offering them). Omitted means every
     * row is editable, which is what the deck and card lists want.
     */
    canModify?: (item: T) => boolean;
    /** Adds ARIA grid/row/gridcell roles and roving tabindex for keyboard lists. */
    rowNavigation?: boolean;
    /** Which row holds the tab stop when rowNavigation is on (controlled). */
    activeIndex?: number;
    /** aria-label on the grid when rowNavigation is on. */
    listLabel?: string;
    /** Makes each <li> draggable and forwards drag events to the parent. */
    draggableRows?: boolean;
  }>(),
  {
    rowNavigation: false,
    activeIndex: -1,
    listLabel: '',
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
  <div class="manage-shell">
    <div class="manage-header">
      <h2 class="manage-title font-body">{{ title }}</h2>
      <div class="manage-header-right">
        <span v-if="!isLoading" class="count-badge font-label">{{ count }} {{ countLabel }}</span>
        <slot name="header-extra" />
      </div>
    </div>

    <slot name="form" />

    <div class="manage-list-status font-label" v-if="isLoading">{{ loadingText }}</div>
    <div class="manage-list-status font-label" v-else-if="rows.length === 0">{{ emptyText }}</div>

    <ul
      v-else
      class="manage-list"
      :role="rowNavigation ? 'grid' : undefined"
      :aria-label="rowNavigation && listLabel ? listLabel : undefined"
      :aria-rowcount="rowNavigation ? rows.length : undefined"
    >
      <li
        v-for="(item, index) in rows"
        :key="item.id"
        class="manage-row"
        :class="{ 'manage-row--active': rowNavigation && index === activeIndex }"
        :role="rowNavigation ? 'row' : undefined"
        :data-roving-item="rowNavigation ? '' : undefined"
        :aria-rowindex="rowNavigation ? index + 1 : undefined"
        :tabindex="rowNavigation ? (index === activeIndex ? 0 : -1) : undefined"
        :draggable="draggableRows ? true : undefined"
        @focus="rowNavigation ? emit('row-focus', index) : undefined"
        @click="rowNavigation ? emit('row-focus', index) : undefined"
        @dblclick="rowNavigation ? emit('row-activate', item, index) : undefined"
        @dragstart="draggableRows && emit('row-dragstart', index)"
        @dragenter.prevent="draggableRows && emit('row-dragenter', index)"
        @dragover.prevent
        @dragend="draggableRows && emit('row-dragend')"
      >
        <div class="manage-row-info" :role="rowNavigation ? 'gridcell' : undefined">
          <slot name="row" :item="item" :index="index" />
        </div>
        <div class="manage-row-actions" :role="rowNavigation ? 'gridcell' : undefined">
          <AppButton
            variant="edit"
            :disabled="canModify ? !canModify(item) : false"
            :tabindex="rowNavigation ? -1 : undefined"
            @click.stop="emit('edit', item)"
          >
            {{ t('common.edit') }}
          </AppButton>
          <AppButton
            variant="delete"
            :disabled="canModify ? !canModify(item) : false"
            :tabindex="rowNavigation ? -1 : undefined"
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
.manage-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-9);
  gap: var(--space-6);
  flex-wrap: wrap;
}
.manage-title {
  font-size: var(--font-size-xl);
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}
.manage-header-right {
  display: flex;
  align-items: center;
  gap: var(--space-6);
}
.count-badge {
  font-size: var(--font-size-base);
  font-weight: 700;
  letter-spacing: var(--tracking-normal);
  color: var(--color-accent);
  background: var(--surface-page);
  border: var(--space-1) solid var(--color-accent);
  padding: var(--space-2) var(--space-5);
}
.manage-list-status {
  color: var(--text-secondary);
  font-size: var(--font-size-base);
  text-align: center;
  /* stylelint-disable-next-line scale-unlimited/declaration-strict-value -- approved Step 2 - layout one-off, see design-tokens.json notes */
  padding: 30px 0;
}
.manage-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}
.manage-row {
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
.manage-row:hover {
  border-left-color: var(--color-accent);
  background: var(--state-hover-surface);
}
.manage-row--active:focus,
.manage-row--active:focus-visible {
  outline: var(--focus-ring-width) solid var(--color-focus-ring);
  outline-offset: 2px;
  border-left-color: var(--color-accent);
}
.manage-row-info {
  min-width: 0;
  flex: 1;
}
.manage-row-actions {
  display: flex;
  gap: var(--space-4);
  flex-shrink: 0;
}
@media (prefers-reduced-motion: reduce) {
  .manage-row {
    transition: none;
  }
}
</style>
