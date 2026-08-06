<script setup lang="ts">
/**
 * Shared arcade-styled button. Consolidates what were previously 6+
 * independent copies of `.btn-arcade`/`.btn-guest`/`.btn-edit`/`.btn-delete`
 * (plus FlashcardsView's `.btn-fc`) into one component. `type`/`disabled`
 * and any listener (e.g. `@click`) fall through to the root `<button>`
 * automatically — no need to declare them as props/emits here.
 *
 * Note: the `primary`/`danger` variants normalize FlashcardsView's former
 * `.btn-fc` sizing (padding/font-size) onto `.btn-arcade`'s dimensions —
 * a deliberate ~1-2px visual shift, not a regression. See COMPONENTS.md.
 */
withDefaults(
  defineProps<{
    variant?: 'primary' | 'danger' | 'secondary' | 'edit' | 'delete';
    type?: 'button' | 'submit' | 'reset';
    disabled?: boolean;
  }>(),
  {
    variant: 'primary',
    type: 'button',
    disabled: false,
  },
);
</script>

<template>
  <button
    :type="type"
    :disabled="disabled"
    class="app-btn font-label"
    :class="`app-btn--${variant}`"
  >
    <slot />
  </button>
</template>

<style scoped>
.app-btn {
  cursor: pointer;
  font-family: var(--font-label);
}

.app-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  pointer-events: none;
}

.app-btn:focus-visible {
  outline: var(--focus-ring-width) solid var(--color-focus-ring);
  outline-offset: 2px;
}

.app-btn--primary,
.app-btn--danger {
  font-weight: 700;
  font-size: var(--font-size-md);
  letter-spacing: var(--tracking-wide);
  text-transform: uppercase;
  border: none;
  padding: var(--space-6) var(--space-10);
}

.app-btn--primary {
  background: var(--status-success);
  color: var(--text-on-accent);
  box-shadow: 0 4px 0 var(--status-success-subtle);
}

.app-btn--danger {
  background: var(--status-danger);
  color: var(--text-on-accent);
  box-shadow: 0 4px 0 var(--status-danger-subtle);
}

.app-btn--primary:active:not(:disabled),
.app-btn--danger:active:not(:disabled) {
  transform: translateY(4px);
  box-shadow: none;
}

.app-btn--secondary {
  background: transparent;
  border: var(--space-1) solid var(--surface-panel-border);
  color: var(--text-secondary);
  padding: var(--space-5) var(--space-8);
  font-size: var(--font-size-sm);
  letter-spacing: var(--tracking-normal);
}

.app-btn--secondary:hover:not(:disabled) {
  border-color: var(--color-accent);
  color: var(--text-primary);
}

.app-btn--edit,
.app-btn--delete {
  font-size: var(--font-size-sm);
  letter-spacing: var(--tracking-normal);
  padding: var(--space-3) var(--space-6);
  border: none;
  background: var(--surface-panel-border);
}

.app-btn--edit {
  color: var(--color-accent);
}

.app-btn--edit:hover:not(:disabled) {
  background: var(--state-selected-surface);
}

.app-btn--delete {
  color: var(--status-danger);
}

.app-btn--delete:hover:not(:disabled) {
  background: var(--status-danger-subtle);
  color: var(--text-primary);
}
</style>
