<script setup lang="ts">
import PixelFrame from '@/shared/components/PixelFrame.vue'

export interface LevelProgress {
  id: string
  index: number
  status: 'done' | 'current' | 'locked'
}

defineProps<{
  title: string
  levels: LevelProgress[]
  progressPercent: number
  subLabel: string
}>()
</script>

<template>
  <PixelFrame frame-color="amber" surface="cabinet" :ring-width="3">
    <div class="world-inner">
      <p class="world-title font-pixel">{{ title }}</p>
      <div class="levels">
        <div v-for="level in levels" :key="level.id" class="level font-label" :class="level.status">
          {{ level.index }}
        </div>
      </div>
      <div class="world-progress-track">
        <div class="world-progress-fill" :style="{ width: `${progressPercent}%` }" />
      </div>
      <span class="world-sub font-label">{{ subLabel }}</span>
    </div>
  </PixelFrame>
</template>

<style scoped>
.world-inner {
  padding: 18px;
  position: relative;
}
.world-title {
  font-size: 11px;
  margin-bottom: 14px;
  color: var(--text-primary);
}
.levels {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 14px;
}
.level {
  width: 34px;
  height: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 13px;
  background: var(--surface-page);
  color: var(--text-secondary);
}
.level.done {
  background: var(--status-success);
  color: var(--text-on-accent);
}
.level.current {
  background: var(--state-selected-bg);
  color: var(--text-on-accent);
  box-shadow: 0 0 0 2px var(--phosphor);
}
.level.locked {
  color: var(--text-disabled);
}
.world-progress-track {
  height: 8px;
  background: var(--surface-page);
  margin-bottom: 8px;
}
.world-progress-fill {
  height: 100%;
  background: var(--color-accent);
}
.world-sub {
  font-size: 11px;
  color: var(--text-secondary);
}
</style>
