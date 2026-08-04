<script setup lang="ts">
/**
 * Renders a world's levels as a stage-select path: numbered nodes joined by
 * a dotted connector, colored by how far the learner has traveled. Locked
 * nodes are non-interactive (aria-disabled) and show a lock glyph instead
 * of their number.
 */
export interface LevelProgress {
  id: string
  index: number
  status: 'done' | 'current' | 'locked'
}

defineProps<{
  levels: LevelProgress[]
}>()

/** A connector is "traveled" only once both nodes it joins are done. */
function connectorStatus(levels: LevelProgress[], i: number): 'done' | 'current' | 'locked' {
  const left = levels[i]
  const right = levels[i + 1]
  if (left.status === 'done' && right.status !== 'locked') return 'done'
  if (left.status === 'done' || left.status === 'current') return 'current'
  return 'locked'
}
</script>

<template>
  <div class="level-path" role="list">
    <template v-for="(level, i) in levels" :key="level.id">
      <div
        class="node font-label"
        :class="`node--${level.status}`"
        role="listitem"
        :aria-label="level.status === 'locked' ? `Cấp độ ${level.index}, chưa mở khóa` : `Cấp độ ${level.index}`"
        :aria-disabled="level.status === 'locked'"
      >
        <span v-if="level.status === 'locked'" aria-hidden="true">&#128274;</span>
        <span v-else-if="level.status === 'done'" aria-hidden="true">&#10003;</span>
        <span v-else aria-hidden="true">{{ level.index }}</span>
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
.node {
  width: 34px;
  height: 34px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: var(--font-size-md);
  background: var(--surface-page);
  color: var(--text-secondary);
}
.node--done {
  background: var(--status-success);
  color: var(--text-on-accent);
}
.node--current {
  background: var(--state-selected-bg);
  color: var(--text-on-accent);
  box-shadow: 0 0 0 2px var(--phosphor);
  animation: pulse 1.6s ease-in-out infinite;
}
.node--locked {
  color: var(--text-disabled);
  font-size: var(--font-size-sm);
}
.connector {
  flex: 1 1 16px;
  min-width: 16px;
  height: 2px;
  margin: 0 var(--space-2);
  background-image: repeating-linear-gradient(
    to right,
    var(--connector-color) 0,
    var(--connector-color) 4px,
    transparent 4px,
    transparent 8px
  );
}
.connector--done {
  --connector-color: var(--status-success);
}
.connector--current {
  --connector-color: var(--color-accent);
}
.connector--locked {
  --connector-color: var(--locked);
}

@keyframes pulse {
  0%,
  100% {
    box-shadow: 0 0 0 2px var(--phosphor);
  }
  50% {
    box-shadow: 0 0 0 4px var(--phosphor);
  }
}
@media (prefers-reduced-motion: reduce) {
  .node--current {
    animation: none;
  }
}
</style>
