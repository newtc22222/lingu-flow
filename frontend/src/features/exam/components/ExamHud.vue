<script setup lang="ts">
import PixelFrame from '@/shared/components/PixelFrame.vue'
import { useExamStore } from '../store/examStore'

const store = useExamStore()
</script>

<template>
  <div class="hud">
    <div class="hud-bar">
      <PixelFrame frame-color="cabinet-light" surface="ink" :ring-width="4">
        <div class="hud-bar-track" role="timer" :aria-label="`${store.timeDisplay} remaining`">
          <div
            class="hud-bar-fill"
            :class="{ 'hud-bar-fill--low': store.isLowTime }"
            :style="{ width: `${store.progressPercent}%` }"
          />
        </div>
      </PixelFrame>
    </div>
    <div class="hud-time font-label" :class="{ 'hud-time--low': store.isLowTime }">
      {{ store.timeDisplay }}
    </div>
    <div class="hud-lives font-pixel" :aria-label="`${store.lives} of ${store.maxLives} lives remaining`">
      <span v-for="i in store.maxLives" :key="i">{{ i <= store.lives ? '♥' : '♡' }}</span>
    </div>
  </div>
</template>

<style scoped>
.hud {
  display: flex;
  align-items: center;
  gap: var(--space-8);
  margin-bottom: var(--space-10);
}
.hud-bar {
  flex: 1;
}
.hud-bar-track {
  height: 20px;
  background: var(--surface-page);
  position: relative;
  overflow: hidden;
}
.hud-bar-fill {
  height: 100%;
  background:
    linear-gradient(90deg, var(--color-accent), var(--amber-light)),
    repeating-linear-gradient(90deg, var(--overlay-scan-line) 0 4px, transparent 4px 8px);
  transition: width 0.25s linear, background 0.4s ease;
}
.hud-bar-fill--low {
  background:
    linear-gradient(90deg, var(--status-danger), var(--red-light)),
    repeating-linear-gradient(90deg, var(--overlay-scan-line) 0 4px, transparent 4px 8px);
}
.hud-time {
  font-weight: 700;
  font-size: var(--font-size-xl);
  min-width: 64px;
  text-align: right;
  color: var(--text-primary);
}
.hud-time--low {
  color: var(--status-danger);
}
.hud-lives {
  font-size: 14px;
  color: var(--status-danger);
  letter-spacing: 3px;
}

@media (prefers-reduced-motion: reduce) {
  .hud-bar-fill {
    transition: none;
  }
}
</style>
