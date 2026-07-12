<script setup lang="ts">
import { computed } from 'vue';
import { marked } from 'marked';
import DOMPurify from 'dompurify';

const props = defineProps<{
  content: string;
}>();

const renderedMarkdown = computed(() => {
  const rawHtml = marked.parse(props.content) as string;
  return DOMPurify.sanitize(rawHtml);
});
</script>

<template>
  <div class="prose prose-invert max-w-none text-center" v-html="renderedMarkdown"></div>
</template>

<style scoped>
/* Scoped overrides if needed */
:deep(p) {
  margin-bottom: 0.5em;
}
:deep(code) {
  background-color: rgba(255, 255, 255, 0.1);
  padding: 0.2rem 0.4rem;
  border-radius: 0.25rem;
  font-family: monospace;
}
</style>
