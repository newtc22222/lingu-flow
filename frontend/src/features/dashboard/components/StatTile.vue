<script setup lang="ts">
import PixelFrame from '@/shared/components/PixelFrame.vue'

withDefaults(
  defineProps<{
    label: string
    value: string | number
    accent?: 'amber' | 'green'
  }>(),
  { accent: 'amber' },
)
</script>

<template>
  <PixelFrame frame-color="amber" surface="cabinet" :ring-width="3">
    <div class="stat-inner">
      <span class="stat-label font-label">{{ label }}</span>
      <span class="stat-value font-label" :class="{ 'stat-value--green': accent === 'green' }">{{ value }}</span>
    </div>
  </PixelFrame>
</template>

<style scoped>
.stat-inner {
  padding: var(--space-8);
}
.stat-label {
  font-weight: 700;
  font-size: var(--font-size-sm);
  letter-spacing: var(--tracking-wide);
  text-transform: uppercase;
  color: var(--text-secondary);
  margin-bottom: var(--space-4);
  display: block;
}
.stat-value {
  font-size: var(--font-size-2xl);
  font-weight: 700;
  color: var(--color-accent);
}
.stat-value--green {
  color: var(--status-success);
}
</style>
