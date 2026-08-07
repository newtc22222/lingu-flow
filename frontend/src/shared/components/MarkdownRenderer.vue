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
  /* stylelint-disable-next-line scale-unlimited/declaration-strict-value -- isolated layout value, not part of the spacing scale */
  margin-bottom: 0.5em;
}
:deep(code) {
  background-color: rgba(
    255,
    255,
    255,
    0.1
  ); /* approved Step 5 - MarkdownRenderer rgba exception, see ui-guidelines.md */
  /* stylelint-disable-next-line scale-unlimited/declaration-strict-value -- approved Step 2 - no radius/rem scale exists, see COMPONENTS.md */
  padding: 0.2rem 0.4rem;
  /* stylelint-disable-next-line scale-unlimited/declaration-strict-value -- approved Step 2 - no radius/rem scale exists, see COMPONENTS.md */
  border-radius: 0.25rem;
  font-family: monospace;
}
</style>
