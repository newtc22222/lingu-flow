<script setup lang="ts">
defineProps<{
  total: number
  currentIndex: number
}>()
</script>

<template>
  <div class="fc-dots" role="list" aria-label="Deck progress">
    <div
      v-for="i in total"
      :key="i"
      class="dot"
      role="listitem"
      :class="{ done: i - 1 < currentIndex, current: i - 1 === currentIndex }"
    />
  </div>
</template>

<style scoped>
.fc-dots {
  display: flex;
  gap: 6px;
}
.dot {
  width: 10px;
  height: 10px;
  background: var(--surface-panel-border);
}
.dot.done {
  background: var(--status-success);
}
.dot.current {
  background: var(--state-selected-bg);
}
</style>
