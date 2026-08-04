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
}>()
</script>

<template>
  <div class="stat">
    <span class="stat-label font-label">{{ label }}</span>
    <span class="stat-value font-pixel">
      <span v-if="icon" class="stat-icon" aria-hidden="true">{{ icon }}</span>
      {{ value }}
    </span>
  </div>
</template>

<style scoped>
.stat {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
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
  display: flex;
  align-items: center;
  gap: var(--space-4);
}
.stat-icon {
  font-size: var(--font-size-md);
}
</style>
