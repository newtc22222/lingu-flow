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
  color: var(--phosphor);
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
  background: var(--ink);
  color: var(--muted);
}
.level.done {
  background: var(--green);
  color: var(--ink);
}
.level.current {
  background: var(--amber);
  color: var(--ink);
  box-shadow: 0 0 0 2px var(--phosphor);
}
.level.locked {
  color: var(--locked);
}
.world-progress-track {
  height: 8px;
  background: var(--ink);
  margin-bottom: 8px;
}
.world-progress-fill {
  height: 100%;
  background: var(--amber);
}
.world-sub {
  font-size: 11px;
  color: var(--muted);
}
</style>
