<script setup lang="ts">
/**
 * Discoverability strip for keyboard shortcuts. Contains no key values and no
 * translated strings of its own — callers pass literal glyphs and already-
 * translated labels so <kbd> never renders diacritic-bearing copy.
 *
 * Caps use font-label (Press Start 2P has no ↑/↓ glyphs). Labels use font-body.
 *
 * `layout="strip"` is the inline row, hidden below 768px where the affordances
 * it documents are pointer-only. `layout="panel"` is the modal form: always
 * visible (that width gate is exactly why the modal exists) and laid out as a
 * column of rows so long labels don't ragged-wrap mid-item.
 */
export interface KeycapItem {
  keys: string[];
  label: string;
}

withDefaults(
  defineProps<{
    items: KeycapItem[];
    /** Group accessible name (not named `ariaLabel` — Vue treats `aria-*` specially). */
    legendLabel: string;
    layout?: 'strip' | 'panel';
    /** Renders the caps dimmed — used when the group's keys are unavailable here. */
    muted?: boolean;
  }>(),
  { layout: 'strip', muted: false },
);
</script>

<template>
  <div
    class="keycap-legend"
    :class="[`keycap-legend--${layout}`, { 'keycap-legend--muted': muted }]"
    role="group"
    :aria-label="legendLabel"
  >
    <div v-for="(item, i) in items" :key="i" class="keycap-item">
      <span class="keycap-keys">
        <template v-for="(key, ki) in item.keys" :key="ki">
          <span v-if="ki > 0" class="keycap-sep" aria-hidden="true">+</span>
          <kbd class="keycap font-label">{{ key }}</kbd>
        </template>
      </span>
      <span class="keycap-label font-body">{{ item.label }}</span>
    </div>
  </div>
</template>

<style scoped>
.keycap-legend {
  flex-wrap: wrap;
  align-items: center;
}

/* Inline strip — desktop only */
.keycap-legend--strip {
  display: none;
  gap: var(--space-5) var(--space-8);
  margin-bottom: var(--space-7);
}
@media (min-width: 768px) {
  .keycap-legend--strip {
    display: flex;
  }
}

/* Panel — inside the hotkeys modal, always visible at every width */
.keycap-legend--panel {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--space-4) var(--space-8);
}
@media (min-width: 480px) {
  .keycap-legend--panel {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
.keycap-legend--panel .keycap-item {
  justify-content: flex-start;
}

.keycap-item {
  display: inline-flex;
  align-items: center;
  gap: var(--space-3);
}
.keycap-keys {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
}
.keycap {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: var(--space-10);
  padding: var(--space-1) var(--space-3);
  border: var(--space-1) solid var(--surface-panel-border);
  background: var(--surface-page);
  color: var(--text-primary);
  font-size: var(--font-size-2xs);
  letter-spacing: var(--tracking-tight);
  line-height: 1.2;
}
.keycap-sep {
  color: var(--text-secondary);
  font-size: var(--font-size-2xs);
}
.keycap-label {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

.keycap-legend--muted .keycap {
  color: var(--text-disabled);
  border-color: var(--text-disabled);
}
.keycap-legend--muted .keycap-label {
  color: var(--text-disabled);
}
</style>
