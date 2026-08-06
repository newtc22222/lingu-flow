<script setup lang="ts">
/**
 * A single HUD scoreboard readout (e.g. streak, XP). Value is always a
 * plain number/digit string, so it's safe to set in font-pixel (no
 * Vietnamese diacritics ever appear here) — labels use font-label instead.
 */
defineProps<{
  label: string
  value: string | number
  icon?: string
  accentColor?: string
}>()
</script>

<template>
  <div class="stat-recessed-well">
    <span v-if="icon" class="stat-icon" aria-hidden="true">{{ icon }}</span>
    <span class="stat-label font-label">{{ label }}</span>
    <span class="stat-value font-pixel" :style="accentColor ? { color: accentColor } : {}">
      {{ value }}
    </span>
  </div>
</template>

<style scoped>
.stat-recessed-well {
  background: var(--surface-page);
  border: var(--space-1) solid var(--surface-panel-border);
  padding: var(--space-6) var(--space-7);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  flex: 1;
  min-width: 140px;
}
.stat-icon {
  font-size: var(--font-size-2xl);
  line-height: 1;
}
.stat-label {
  font-weight: 700;
  font-size: var(--font-size-xs);
  letter-spacing: var(--tracking-wide);
  text-transform: uppercase;
  color: var(--text-secondary);
}
.stat-value {
  font-size: var(--font-size-lg);
  color: var(--color-accent);
  text-align: center;
}
</style>
