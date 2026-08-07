<script setup lang="ts">
/**
 * Discoverability strip for keyboard shortcuts. Contains no key values and no
 * translated strings of its own — callers pass literal glyphs and already-
 * translated labels so <kbd> never renders diacritic-bearing copy.
 *
 * Caps use font-label (Press Start 2P has no ↑/↓ glyphs). Labels use font-body.
 * Hidden below 768px where the documented affordances are pointer-only.
 */
defineProps<{
  items: { keys: string[]; label: string }[];
  /** Group accessible name (not named `ariaLabel` — Vue treats `aria-*` specially). */
  legendLabel: string;
}>();
</script>

<template>
  <div class="keycap-legend" role="group" :aria-label="legendLabel">
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
  display: none;
  flex-wrap: wrap;
  gap: var(--space-5) var(--space-8);
  margin-bottom: var(--space-7);
  align-items: center;
}
@media (min-width: 768px) {
  .keycap-legend {
    display: flex;
  }
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
</style>
