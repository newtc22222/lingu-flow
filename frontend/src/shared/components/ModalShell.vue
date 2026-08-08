<script setup lang="ts">
/**
 * Overlay + cabinet frame shared by every modal in the app.
 *
 * Owns the parts that are easy to get subtly wrong and pointless to write
 * twice: Teleport, backdrop, Escape, body scroll lock, click-outside, and a
 * real focus trap (initial focus in, Tab cycles inside, focus restored to
 * whatever opened it). ConfirmDialog and HotkeysDialog both sit on this.
 *
 * Content padding is the caller's job, same contract as PixelFrame.
 */
import { nextTick, onUnmounted, ref, watch } from 'vue';
import PixelFrame from './PixelFrame.vue';

const props = withDefaults(
  defineProps<{
    isOpen: boolean;
    /** Accessible name for the dialog. */
    title: string;
    /** Drives the frame ring colour. */
    variant?: 'primary' | 'danger';
  }>(),
  { variant: 'primary' },
);

const emit = defineEmits<{
  (e: 'update:isOpen', value: boolean): void;
  (e: 'close'): void;
}>();

const dialogRef = ref<HTMLElement | null>(null);
/** Whatever had focus before we opened, so it can be handed back on close. */
let previouslyFocused: HTMLElement | null = null;

const FOCUSABLE =
  'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

function focusables(): HTMLElement[] {
  if (!dialogRef.value) return [];
  return Array.from(dialogRef.value.querySelectorAll<HTMLElement>(FOCUSABLE));
}

function close() {
  emit('update:isOpen', false);
  emit('close');
}

function handleKeydown(event: KeyboardEvent) {
  if (!props.isOpen) return;

  if (event.key === 'Escape') {
    event.preventDefault();
    close();
    return;
  }

  if (event.key !== 'Tab') return;

  // Trap: cycle within the dialog rather than escaping to the page behind.
  const items = focusables();
  if (items.length === 0) {
    event.preventDefault();
    return;
  }
  const first = items[0];
  const last = items[items.length - 1];
  const active = document.activeElement;

  if (event.shiftKey && (active === first || !dialogRef.value?.contains(active))) {
    event.preventDefault();
    last.focus();
  } else if (!event.shiftKey && active === last) {
    event.preventDefault();
    first.focus();
  }
}

function releaseBody() {
  document.body.style.overflow = '';
}

watch(
  () => props.isOpen,
  async (open) => {
    if (open) {
      previouslyFocused = document.activeElement as HTMLElement | null;
      document.body.style.overflow = 'hidden';
      window.addEventListener('keydown', handleKeydown);
      await nextTick();
      // A dialog can legitimately have no focusable children (the hotkeys
      // legend is all <kbd>). Focus the container itself so Tab is trapped and
      // screen readers land inside rather than behind the overlay.
      const first = focusables()[0];
      if (first) first.focus();
      else dialogRef.value?.focus();
      return;
    }

    releaseBody();
    window.removeEventListener('keydown', handleKeydown);
    // Hand focus back to the trigger so keyboard users don't land on <body>.
    previouslyFocused?.focus?.();
    previouslyFocused = null;
  },
);

onUnmounted(() => {
  releaseBody();
  window.removeEventListener('keydown', handleKeydown);
});
</script>

<template>
  <Teleport to="body">
    <div
      v-if="isOpen"
      class="modal-overlay"
      role="dialog"
      aria-modal="true"
      :aria-label="title"
      @click.self="close"
    >
      <PixelFrame
        :frame-color="variant === 'danger' ? 'red' : 'amber'"
        surface="cabinet"
        :ring-width="3"
        class="modal-card"
      >
        <div ref="dialogRef" class="modal-inner" tabindex="-1">
          <header class="modal-header">
            <h3 class="modal-title font-label">{{ title }}</h3>
          </header>

          <div class="modal-body">
            <slot />
          </div>

          <footer v-if="$slots.footer" class="modal-actions">
            <slot name="footer" />
          </footer>
        </div>
      </PixelFrame>
    </div>
  </Teleport>
</template>

<style scoped>
/* stylelint-disable-next-line function-disallowed-list -- semi-transparent modal backdrop overlay */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(10, 12, 18, 0.82);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-8);
  z-index: 100;
  backdrop-filter: blur(4px);
}

.modal-card {
  width: 100%;
  max-width: 420px;
  max-height: 88vh;
  box-shadow: 0 12px 32px var(--ink);
}

.modal-inner {
  padding: var(--space-8);
  display: flex;
  flex-direction: column;
  gap: var(--space-7);
  max-height: 88vh;
  box-sizing: border-box;
}

.modal-header {
  border-bottom: var(--space-1) solid var(--surface-panel-border);
  padding-bottom: var(--space-4);
  flex-shrink: 0;
}

/*
 * font-label, not font-pixel: titles are translated, and Press Start 2P has no
 * Vietnamese diacritic glyphs (XÓA BỘ THẺ rendered half-pixel, half-fallback).
 */
.modal-title {
  font-size: var(--font-size-md);
  font-weight: 700;
  color: var(--color-accent);
  letter-spacing: var(--tracking-tight);
}

.modal-body {
  min-height: 0;
  overflow-y: auto;
}

/* Focused only as the no-focusable-children fallback — no ring needed. */
.modal-inner:focus {
  outline: none;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-5);
  margin-top: var(--space-3);
  flex-shrink: 0;
}
</style>
