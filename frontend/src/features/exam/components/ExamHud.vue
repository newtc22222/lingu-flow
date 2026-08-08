<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import PixelFrame from '@/shared/components/PixelFrame.vue';
import AppButton from '@/shared/components/AppButton.vue';
import { useExamStore } from '../store/examStore';

defineProps<{
  title: string;
  canSubmit?: boolean;
  isSubmitting?: boolean;
}>();

const emit = defineEmits<{
  (e: 'submit'): void;
}>();

const { t } = useI18n();
const store = useExamStore();
</script>

<template>
  <div class="hud">
    <div class="hud-top">
      <p class="hud-title font-body">{{ title }}</p>
      <div class="hud-actions">
        <span class="hud-progress font-label">
          {{ store.answeredCount }}/{{ store.questions.length }}
        </span>
        <span class="hud-time font-label" :class="{ 'hud-time--low': store.isLowTime }">
          {{ store.timeDisplay }}
        </span>
        <AppButton
          variant="danger"
          :disabled="!canSubmit || isSubmitting || store.isLocked"
          @click="emit('submit')"
        >
          {{ isSubmitting ? t('exam.submitting') : t('exam.submit') }}
        </AppButton>
      </div>
    </div>
    <div class="hud-bar">
      <PixelFrame frame-color="cabinet-light" surface="ink" :ring-width="3">
        <div class="hud-bar-track" role="timer" :aria-label="`${store.timeDisplay} remaining`">
          <div
            class="hud-bar-fill"
            :class="{ 'hud-bar-fill--low': store.isLowTime }"
            :style="{ width: `${store.progressPercent}%` }"
          />
        </div>
      </PixelFrame>
    </div>
  </div>
</template>

<style scoped>
.hud {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
  flex-shrink: 0;
}
.hud-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-6);
  flex-wrap: wrap;
}
.hud-title {
  font-size: var(--font-size-md);
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 50%;
}
.hud-actions {
  display: flex;
  align-items: center;
  gap: var(--space-6);
  flex-wrap: wrap;
}
.hud-bar {
  width: 100%;
}
.hud-bar-track {
  height: var(--space-8);
  background: var(--surface-page);
  position: relative;
  overflow: hidden;
}
.hud-bar-fill {
  height: 100%;
  background:
    linear-gradient(90deg, var(--color-accent), var(--amber-light)),
    repeating-linear-gradient(90deg, var(--overlay-scan-line) 0 4px, transparent 4px 8px);
  transition:
    width 0.25s linear,
    background 0.4s ease;
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
  font-variant-numeric: tabular-nums;
}
.hud-time--low {
  color: var(--status-danger);
}
.hud-progress {
  font-size: var(--font-size-md-plus);
  color: var(--text-secondary);
  letter-spacing: var(--tracking-normal);
  font-variant-numeric: tabular-nums;
}

@media (prefers-reduced-motion: reduce) {
  .hud-bar-fill {
    transition: none;
  }
}
</style>
