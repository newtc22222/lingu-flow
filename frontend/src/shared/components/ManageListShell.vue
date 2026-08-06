<script setup lang="ts" generic="T extends { id: string }">
/**
 * Shared shell for the "create/edit form + list of rows with edit/delete"
 * pattern duplicated (near byte-for-byte in places) across
 * CardManagementView and DeckManagementView. Owns the header/count badge,
 * loading/empty status text, row shell (border, hover, spacing), and the
 * edit/delete action buttons. The create/edit form area and each row's
 * info content differ enough between consumers (Card's 2-column form with
 * a live markdown preview vs. Deck's single-column form; front/back vs.
 * name/description row content) that those stay slotted rather than baked
 * in here.
 */
import { useI18n } from 'vue-i18n'
import AppButton from './AppButton.vue'

const { t } = useI18n()

defineProps<{
  title: string
  countLabel: string
  count: number
  isLoading: boolean
  loadingText: string
  emptyText: string
  rows: T[]
}>()

const emit = defineEmits<{
  (e: 'edit', item: T): void
  (e: 'delete', id: string): void
}>()
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

    <ul v-else class="manage-list">
      <li v-for="item in rows" :key="item.id" class="manage-row">
        <div class="manage-row-info">
          <slot name="row" :item="item" />
        </div>
        <div class="manage-row-actions">
          <AppButton variant="edit" @click="emit('edit', item)">{{ t('common.edit') }}</AppButton>
          <AppButton variant="delete" @click="emit('delete', item.id)">
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
  transition: border-color 0.12s, background 0.12s;
}
.manage-row:hover {
  border-left-color: var(--color-accent);
  background: var(--state-hover-surface);
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
</style>
