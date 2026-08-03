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
  padding: 16px;
}
.stat-label {
  font-weight: 700;
  font-size: 11px;
  letter-spacing: 1.5px;
  text-transform: uppercase;
  color: var(--muted);
  margin-bottom: 8px;
  display: block;
}
.stat-value {
  font-size: 22px;
  font-weight: 700;
  color: var(--amber);
}
.stat-value--green {
  color: var(--green);
}
</style>
