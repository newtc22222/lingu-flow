<script setup lang="ts">
/**
 * The console's legend plate. Not a static cheat sheet — the caller builds
 * `groups` from the current screen's state, so the ORDER group can arrive
 * muted with the reason attached (Unfiled cards can't be reordered) instead of
 * silently disappearing and leaving the user wondering where the keys went.
 */
import ModalShell from '@/shared/components/ModalShell.vue';
import KeycapLegend, { type KeycapItem } from './KeycapLegend.vue';

export interface HotkeyGroup {
  label: string;
  items: KeycapItem[];
  /** When set, the group renders dimmed and this explains why. */
  note?: string;
}

defineProps<{
  isOpen: boolean;
  title: string;
  groups: HotkeyGroup[];
}>();

const emit = defineEmits<{
  (e: 'update:isOpen', value: boolean): void;
}>();
</script>

<template>
  <ModalShell
    :is-open="isOpen"
    :title="title"
    variant="primary"
    @update:is-open="emit('update:isOpen', $event)"
  >
    <div class="hotkeys-groups">
      <section v-for="group in groups" :key="group.label" class="hotkeys-group">
        <h4 class="hotkeys-group-label font-label">{{ group.label }}</h4>
        <KeycapLegend
          :items="group.items"
          :legend-label="group.label"
          layout="panel"
          :muted="Boolean(group.note)"
        />
        <p v-if="group.note" class="hotkeys-note font-body">{{ group.note }}</p>
      </section>
    </div>
  </ModalShell>
</template>

<style scoped>
.hotkeys-groups {
  display: flex;
  flex-direction: column;
  gap: var(--space-9);
}
.hotkeys-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}
.hotkeys-group-label {
  font-size: var(--font-size-2xs);
  letter-spacing: var(--tracking-wide);
  color: var(--text-label-accent);
  border-bottom: var(--space-1) solid var(--surface-panel-border);
  padding-bottom: var(--space-3);
  margin: 0;
}
.hotkeys-note {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  margin: 0;
}
</style>
