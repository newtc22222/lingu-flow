<script setup lang="ts">
/**
 * Renders a world's levels as a stage-select path: numbered nodes joined by
 * a connector, colored by how far the learner has traveled. Locked
 * nodes are non-interactive (aria-disabled) and show a lock glyph instead
 * of their number.
 */
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';
import AppButton from '@/shared/components/AppButton.vue';

const { t } = useI18n();
const router = useRouter();

export interface LevelProgress {
  id: string;
  index: number;
  status: 'done' | 'current' | 'locked';
}

defineProps<{
  levels: LevelProgress[];
}>();

function connectorStatus(levels: LevelProgress[], i: number): 'done' | 'current' | 'locked' {
  const left = levels[i];
  const right = levels[i + 1];
  if (left.status === 'done' && right.status !== 'locked') return 'done';
  if (left.status === 'done' || left.status === 'current') return 'current';
  return 'locked';
}

function handleContinue() {
  void router.push({ name: 'flashcards' });
}
</script>

<template>
  <div class="level-path" role="list">
    <template v-for="(level, i) in levels" :key="level.id">
      <div class="node-wrapper">
        <div
          class="node font-label"
          :class="`node--${level.status}`"
          role="listitem"
          :aria-label="
            level.status === 'locked'
              ? t('dashboard.levelLocked', { index: level.index })
              : t('dashboard.level', { index: level.index })
          "
          :aria-disabled="level.status === 'locked'"
        >
          <span v-if="level.status === 'locked'" aria-hidden="true">🔒</span>
          <span v-else-if="level.status === 'done'" aria-hidden="true">✓</span>
          <span v-else aria-hidden="true">L{{ level.index }}</span>
        </div>

        <AppButton
          v-if="level.status === 'current'"
          variant="primary"
          class="node-continue-btn"
          @click="handleContinue"
        >
          {{ t('dashboard.continue', { level: level.index }) }}
        </AppButton>
      </div>

      <div
        v-if="i < levels.length - 1"
        class="connector"
        :class="`connector--${connectorStatus(levels, i)}`"
        aria-hidden="true"
      />
    </template>
  </div>
</template>

<style scoped>
.level-path {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  row-gap: var(--space-6);
}

.node-wrapper {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.node {
  width: 44px;
  height: 44px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: var(--font-size-md);
  background: var(--surface-page);
  color: var(--text-secondary);
  border: var(--space-1) solid var(--surface-panel-border);
}

.node--done {
  background: var(--surface-panel-border);
  border-color: var(--status-success);
  color: var(--status-success);
}

.node--current {
  background: var(--state-selected-bg);
  color: var(--text-on-accent);
  border-color: var(--color-accent);
  width: 52px;
  height: 52px;
  font-size: var(--font-size-lg);
  box-shadow: 0 0 12px var(--amber-dim);
  animation: pulse-node 1.6s ease-in-out infinite;
}

.node--locked {
  background: var(--surface-page);
  border-color: var(--surface-panel-border);
  color: var(--text-disabled);
  opacity: 0.6;
}

.node-continue-btn {
  padding: var(--space-4) var(--space-6);
  font-size: var(--font-size-xs);
}

.connector {
  flex: 1 1 20px;
  min-width: 20px;
  height: 3px;
  margin: 0 var(--space-3);
  background: var(--surface-panel-border);
}

.connector--done {
  background: var(--status-success);
}

.connector--current {
  background: var(--color-accent);
}

.connector--locked {
  background: var(--surface-panel-border);
  opacity: 0.5;
}

@keyframes pulse-node {
  0%,
  100% {
    box-shadow: 0 0 4px var(--amber-dim);
  }
  50% {
    box-shadow: 0 0 16px var(--amber);
  }
}

@media (prefers-reduced-motion: reduce) {
  .node--current {
    animation: none;
  }
}
</style>
