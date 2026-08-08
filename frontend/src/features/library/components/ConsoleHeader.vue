<script setup lang="ts">
/**
 * Top bar shared by the deck rack and the card workspace: optional back
 * button, title, optional count badge, and a slot for the screen's actions.
 *
 * Feature-private for now. QuestionBankView's header (its own title + count
 * pair) is the obvious third consumer — fold it in and promote to shared/ the
 * next time that file is touched, not as a drive-by here.
 */
import AppButton from '@/shared/components/AppButton.vue';

defineProps<{
  title: string;
  /** Omit to render no back button. */
  backLabel?: string;
  /** Omit (or pass a negative number) to render no count badge. */
  count?: number;
  countLabel?: string;
}>();

const emit = defineEmits<{ (e: 'back'): void }>();
</script>

<template>
  <header class="console-header">
    <div class="console-header-lead">
      <AppButton v-if="backLabel" variant="secondary" @click="emit('back')">
        {{ backLabel }}
      </AppButton>
      <h1 class="console-title font-body">{{ title }}</h1>
      <span v-if="count !== undefined && count >= 0 && countLabel" class="console-count font-label">
        {{ count }} {{ countLabel }}
      </span>
    </div>

    <div class="console-header-actions">
      <slot name="actions" />
    </div>
  </header>
</template>

<style scoped>
.console-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-6);
  flex-wrap: wrap;
  flex-shrink: 0;
}
.console-header-lead {
  display: flex;
  align-items: center;
  gap: var(--space-6);
  min-width: 0;
  flex-wrap: wrap;
}
.console-title {
  font-size: var(--font-size-xl);
  font-weight: 700;
  color: var(--color-accent);
  margin: 0;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.console-count {
  font-size: var(--font-size-base);
  font-weight: 700;
  letter-spacing: var(--tracking-normal);
  color: var(--color-accent);
  background: var(--surface-page);
  border: var(--space-1) solid var(--color-accent);
  padding: var(--space-2) var(--space-5);
  flex-shrink: 0;
}
.console-header-actions {
  display: flex;
  align-items: center;
  gap: var(--space-5);
  flex-wrap: wrap;
}
</style>
