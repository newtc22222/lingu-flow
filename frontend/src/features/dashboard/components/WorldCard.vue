<script setup lang="ts">
import LevelPath, { type LevelProgress } from './LevelPath.vue'

export type { LevelProgress }

defineProps<{
  title: string
  levels: LevelProgress[]
  progressPercent: number
  subLabel: string
}>()
</script>

<template>
  <section class="world-zone">
    <div class="zone-banner">
      <h3 class="zone-title font-label">{{ title }}</h3>
      <div class="zone-progress-track">
        <div class="zone-progress-fill" :style="{ width: `${progressPercent}%` }" />
      </div>
      <span class="zone-percent font-label">{{ progressPercent }}%</span>
    </div>
    <LevelPath :levels="levels" />
    <span class="zone-sub font-label">{{ subLabel }}</span>
  </section>
</template>

<style scoped>
.world-zone {
  margin-bottom: var(--space-11);
}
.zone-banner {
  display: flex;
  align-items: center;
  gap: var(--space-7);
  margin-bottom: var(--space-7);
}
.zone-title {
  font-size: var(--font-size-md);
  font-weight: 700;
  letter-spacing: var(--tracking-normal);
  text-transform: uppercase;
  color: var(--text-primary);
  white-space: nowrap;
}
.zone-progress-track {
  flex: 1;
  height: 4px;
  background: var(--surface-panel-border);
}
.zone-progress-fill {
  height: 100%;
  background: var(--color-accent);
}
.zone-percent {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  min-width: 32px;
  text-align: right;
}
.zone-sub {
  display: block;
  margin-top: var(--space-6);
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}
</style>
