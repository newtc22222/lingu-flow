/**
 * Roving-focus list navigation for the library rack and workspace.
 *
 * Feature-private: both consumers are under features/library. Promote to
 * shared/composables/ the first time a second *feature* imports it —
 * ExamComposerView + ExamQuestionRow is the same shape and the obvious
 * second consumer.
 */
import { nextTick, onMounted, onUnmounted, ref, watch, type Ref } from 'vue';

export interface RovingListOptions<T> {
  containerRef: Ref<HTMLElement | null>;
  items: Ref<readonly T[]>;
  canModify?: (item: T) => boolean;
  onActivate?: (item: T, i: number) => void;
  onEdit?: (item: T, i: number) => void;
  onDelete?: (item: T, i: number) => void;
  onNew?: () => void;
  onSearch?: () => void;
  onSave?: () => void;
  /** Alt+arrows; return false if the move was rejected (boundary / disabled). */
  onMove?: (from: number, to: number) => boolean;
  announce: (msg: string) => void;
  /** True while a ConfirmDialog (or similar) is open — shortcuts stay inert. */
  isBlocked?: Ref<boolean>;
  searchQuery?: Ref<string>;
  searchInputRef?: Ref<HTMLElement | null>;
  isEditing?: Ref<boolean>;
  onCancelEdit?: () => void;
}

function isTypingTarget(el: EventTarget | null): boolean {
  if (!(el instanceof HTMLElement)) return false;
  const tag = el.tagName;
  if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return true;
  if (el.isContentEditable) return true;
  return false;
}

function prefersReducedMotion(): boolean {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

function getRows(container: HTMLElement | null): HTMLElement[] {
  if (!container) return [];
  return Array.from(container.querySelectorAll<HTMLElement>('[data-roving-item]'));
}

function getRowFocusables(row: HTMLElement): HTMLElement[] {
  return Array.from(row.querySelectorAll<HTMLElement>('button:not([disabled]), a[href]'));
}

export function useRovingList<T>(o: RovingListOptions<T>): {
  activeIndex: Ref<number>;
  focusIndex: (i: number) => void;
  rowAttrs: (i: number) => Record<string, unknown>;
  onRowFocus: (i: number) => void;
} {
  const activeIndex = ref(o.items.value.length > 0 ? 0 : -1);

  watch(
    () => o.items.value.length,
    (len) => {
      if (len === 0) {
        activeIndex.value = -1;
        return;
      }
      if (activeIndex.value < 0) activeIndex.value = 0;
      if (activeIndex.value >= len) activeIndex.value = len - 1;
    },
  );

  function onRowFocus(i: number) {
    activeIndex.value = i;
  }

  function focusIndex(i: number) {
    if (i < 0 || i >= o.items.value.length) return;
    activeIndex.value = i;
    nextTick(() => {
      const rows = getRows(o.containerRef.value);
      const el = rows[i];
      if (!el) return;
      el.focus({ preventScroll: true });
      el.scrollIntoView({
        block: 'nearest',
        behavior: prefersReducedMotion() ? 'auto' : 'smooth',
      });
    });
  }

  function rowAttrs(i: number): Record<string, unknown> {
    return {
      'data-roving-item': '',
      'aria-rowindex': i + 1,
      role: 'row',
      tabindex: i === activeIndex.value ? 0 : -1,
    };
  }

  function clampIndex(i: number): number {
    const max = o.items.value.length - 1;
    if (max < 0) return -1;
    return Math.max(0, Math.min(max, i));
  }

  function moveFocus(delta: number) {
    const next = clampIndex(activeIndex.value + delta);
    if (next < 0) return;
    focusIndex(next);
  }

  function focusRowOrCell(direction: 1 | -1) {
    const rows = getRows(o.containerRef.value);
    const row = rows[activeIndex.value];
    if (!row) return;

    const focusables = getRowFocusables(row);
    const active = document.activeElement as HTMLElement | null;
    const currentIdx = active ? focusables.indexOf(active) : -1;

    if (direction === 1) {
      // Drill into buttons, or advance within them.
      if (currentIdx < 0) {
        if (focusables[0]) focusables[0].focus();
        return;
      }
      if (currentIdx < focusables.length - 1) {
        focusables[currentIdx + 1].focus();
      }
      return;
    }

    // Left: step back through buttons, then return to the row.
    if (currentIdx > 0) {
      focusables[currentIdx - 1].focus();
      return;
    }
    row.focus({ preventScroll: true });
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.defaultPrevented) return;
    // IME composition — never steal e/n/s mid-composition (Telex/VNI).
    if (e.isComposing || e.keyCode === 229) return;
    if (o.isBlocked?.value) return;

    const typing = isTypingTarget(e.target);
    const key = e.key;

    // Escape ladder — first match wins; may run while typing.
    if (key === 'Escape') {
      // 1. Dialog open → its own handler; we already bailed on isBlocked.
      // 2. Search focused and query non-empty → clear query, keep focus.
      if (
        typing &&
        o.searchInputRef?.value &&
        e.target === o.searchInputRef.value &&
        o.searchQuery &&
        o.searchQuery.value.trim() !== ''
      ) {
        e.preventDefault();
        o.searchQuery.value = '';
        return;
      }
      // 3. Search focused and query empty → return focus to the active row.
      if (typing && o.searchInputRef?.value && e.target === o.searchInputRef.value) {
        e.preventDefault();
        focusIndex(activeIndex.value >= 0 ? activeIndex.value : 0);
        return;
      }
      // 4. Form in edit mode → cancel and refocus the row being edited.
      if (o.isEditing?.value && o.onCancelEdit) {
        e.preventDefault();
        o.onCancelEdit();
        focusIndex(activeIndex.value >= 0 ? activeIndex.value : 0);
        return;
      }
      // 5. Focus inside a row button → return to the row.
      if (!typing) {
        const rows = getRows(o.containerRef.value);
        const row = rows[activeIndex.value];
        if (row && e.target instanceof Node && row.contains(e.target) && e.target !== row) {
          e.preventDefault();
          row.focus({ preventScroll: true });
          return;
        }
      }
      // 6. Otherwise → no-op, do not preventDefault.
      return;
    }

    if (typing) return;

    const bareLetter = !e.ctrlKey && !e.metaKey && !e.altKey;
    const altOnly = e.altKey && !e.ctrlKey && !e.metaKey && !e.shiftKey;
    const items = o.items.value;
    const i = activeIndex.value;
    const item = i >= 0 && i < items.length ? items[i] : undefined;
    const modifiable = item && (o.canModify ? o.canModify(item) : true);

    if (key === 'ArrowDown' && !e.altKey) {
      e.preventDefault();
      moveFocus(1);
      return;
    }
    if (key === 'ArrowUp' && !e.altKey) {
      e.preventDefault();
      moveFocus(-1);
      return;
    }
    if (key === 'Home') {
      e.preventDefault();
      focusIndex(0);
      return;
    }
    if (key === 'End') {
      e.preventDefault();
      focusIndex(items.length - 1);
      return;
    }
    if (key === 'PageDown') {
      e.preventDefault();
      moveFocus(10);
      return;
    }
    if (key === 'PageUp') {
      e.preventDefault();
      moveFocus(-10);
      return;
    }
    if (key === 'ArrowRight') {
      e.preventDefault();
      focusRowOrCell(1);
      return;
    }
    if (key === 'ArrowLeft') {
      e.preventDefault();
      focusRowOrCell(-1);
      return;
    }
    // Enter activates even when canModify is false (e.g. Unfiled row still opens).
    if (key === 'Enter' && bareLetter && item) {
      e.preventDefault();
      o.onActivate?.(item, i);
      return;
    }
    if ((key === 'e' || key === 'E') && bareLetter && item && modifiable) {
      e.preventDefault();
      o.onEdit?.(item, i);
      return;
    }
    if ((key === 'Delete' || key === 'Backspace') && bareLetter && item && modifiable) {
      // Only Delete is listed in the key table; Backspace is common on mac.
      if (key === 'Delete') {
        e.preventDefault();
        o.onDelete?.(item, i);
      }
      return;
    }
    if ((key === 'n' || key === 'N') && bareLetter) {
      e.preventDefault();
      o.onNew?.();
      return;
    }
    if (key === '/' && bareLetter) {
      e.preventDefault();
      o.onSearch?.();
      return;
    }
    if ((key === 's' || key === 'S') && bareLetter) {
      e.preventDefault();
      o.onSave?.();
      return;
    }
    if (altOnly && (key === 'ArrowUp' || key === 'ArrowDown')) {
      e.preventDefault();
      if (i < 0) return;
      const to = i + (key === 'ArrowDown' ? 1 : -1);
      o.onMove?.(i, to);
      return;
    }
  }

  onMounted(() => {
    window.addEventListener('keydown', handleKeydown);
  });
  onUnmounted(() => {
    window.removeEventListener('keydown', handleKeydown);
  });

  return { activeIndex, focusIndex, rowAttrs, onRowFocus };
}
