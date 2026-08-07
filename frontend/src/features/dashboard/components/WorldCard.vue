<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import LevelPath, { type LevelProgress } from './LevelPath.vue';

export type { LevelProgress };

const { t } = useI18n();

defineProps<{
  title: string;
  levels: LevelProgress[];
  progressPercent: number;
  subLabel: string;
}>();
</script>

<template>
  <section class="world-card">
    <div class="world-card-accent" />
    <div class="world-card-body">
      <header class="world-card-header">
        <div>
          <h3 class="world-title font-pixel">{{ title }}</h3>
          <p class="world-sublabel font-label">{{ subLabel }}</p>
        </div>
        <div class="world-percent font-label">
          {{ t('dashboard.complete', { percent: progressPercent }) }}
        </div>
      </header>

      <div class="world-path-container">
        <LevelPath :levels="levels" />
      </div>
    </div>
  </section>
</template>

<style scoped>
.world-card {
  background: var(--surface-panel);
  border: var(--space-1) solid var(--surface-panel-border);
  position: relative;
  margin-bottom: var(--space-9);
  box-shadow: 0 4px 12px var(--ink);
}

.world-card-accent {
  height: 4px;
  background: var(--color-accent);
  width: 100%;
}

.world-card-body {
  padding: var(--space-8);
  display: flex;
  flex-direction: column;
  gap: var(--space-7);
}

.world-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--space-6);
  flex-wrap: wrap;
}

.world-title {
  font-size: var(--font-size-md);
  color: var(--text-primary);
  letter-spacing: var(--tracking-tight);
}

.world-sublabel {
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
  letter-spacing: var(--tracking-normal);
  margin-top: var(--space-2);
  text-transform: uppercase;
}

.world-percent {
  font-size: var(--font-size-sm);
  color: var(--color-accent);
  font-weight: 700;
  letter-spacing: var(--tracking-wide);
}

.world-path-container {
  padding-top: var(--space-4);
}
</style>
