<script setup lang="ts">
defineProps<{
  optionKey: string
  label: string
  selected: boolean
  disabled?: boolean
}>()

defineEmits<{
  (e: 'select'): void
}>()
</script>

<template>
  <button
    type="button"
    class="opt-btn font-body"
    :class="{ 'opt-btn--selected': selected }"
    :disabled="disabled"
    :aria-pressed="selected"
    @click="$emit('select')"
  >
    <span class="opt-key font-pixel" :class="{ 'opt-key--selected': selected }">{{ optionKey }}</span>
    <span class="opt-label">{{ label }}</span>
  </button>
</template>

<style scoped>
.opt-btn {
  display: flex;
  align-items: center;
  gap: var(--space-7);
  width: 100%;
  background: var(--surface-panel-border);
  border: none;
  padding: var(--space-7) var(--space-8);
  color: var(--text-primary);
  font-size: 15px;
  cursor: pointer;
  text-align: left;
  transition: background 0.12s;
}
.opt-btn:hover:not(:disabled):not(.opt-btn--selected) {
  background: var(--state-hover-surface);
}
.opt-btn--selected {
  background: var(--state-selected-surface);
  box-shadow: inset 0 0 0 2px var(--color-focus-ring);
}
.opt-btn:disabled {
  cursor: not-allowed;
}
.opt-key {
  font-size: var(--font-size-xs);
  color: var(--text-on-accent);
  background: var(--muted);
  width: 26px;
  height: 26px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.opt-key--selected {
  background: var(--state-selected-bg);
}
</style>
