<script setup lang="ts">
import PixelFrame from '@/shared/components/PixelFrame.vue'
import AppButton from '@/shared/components/AppButton.vue'
import AnswerOption from './AnswerOption.vue'
import type { ExamQuestion } from '../store/examStore'
import { OPTION_KEYS } from '../store/examStore'

const props = defineProps<{
  question: ExamQuestion
  selectedAnswer?: string
  disabled?: boolean
  isLastQuestion: boolean
}>()

defineEmits<{
  (e: 'select', optionKey: string): void
  (e: 'submit'): void
}>()

const questionLabel = () => (props.question.type ? props.question.type.toUpperCase() : 'MULTIPLE CHOICE')
</script>

<template>
  <PixelFrame frame-color="amber" surface="cabinet" :ring-width="3">
    <div class="question-card">
      <span class="q-label">
        <!-- Press Start 2P's subset lacks the ▸ glyph (renders as a stray dot), so the bullet stays in font-label. -->
        <span class="font-label">▸</span> <span class="font-pixel">{{ questionLabel() }}</span>
      </span>

      <div v-if="question.passage" class="q-passage font-body">
        <span class="q-passage-eyebrow font-label">▸ ĐOẠN VĂN</span>
        {{ question.passage }}
      </div>

      <p class="q-text font-body">{{ question.questionText }}</p>

      <pre v-if="question.codeSnippet" class="code-snip font-label"><code>{{ question.codeSnippet }}</code></pre>

      <div class="options">
        <AnswerOption
          v-for="(option, i) in question.options"
          :key="OPTION_KEYS[i]"
          :option-key="OPTION_KEYS[i]"
          :label="option"
          :selected="selectedAnswer === OPTION_KEYS[i]"
          :disabled="disabled"
          @select="$emit('select', OPTION_KEYS[i])"
        />
      </div>

      <div class="submit-row">
        <AppButton :disabled="disabled || !selectedAnswer" @click="$emit('submit')">
          {{ isLastQuestion ? 'HOÀN THÀNH BÀI THI' : 'NỘP CÂU TRẢ LỜI' }}
        </AppButton>
      </div>
    </div>
  </PixelFrame>
</template>

<style scoped>
.question-card {
  padding: var(--space-11) var(--space-10);
}
.q-label {
  font-size: var(--font-size-2xs);
  color: var(--text-label-accent);
  margin-bottom: var(--space-7);
  display: block;
}
.q-passage {
  font-size: var(--font-size-md-plus);
  line-height: 1.6;
  color: var(--text-secondary);
  background: var(--surface-page);
  padding: var(--space-6) var(--space-7);
  margin: 0 0 var(--space-8);
  border-left: var(--border-width-accent) solid var(--border-info);
}
.q-passage-eyebrow {
  display: block;
  font-size: var(--font-size-sm);
  letter-spacing: var(--tracking-normal);
  color: var(--text-secondary);
  margin-bottom: var(--space-3);
}
.q-text {
  font-size: var(--font-size-xl);
  line-height: 1.55;
  font-weight: 500;
  margin: 0 0 var(--space-10);
  color: var(--text-primary);
}
.code-snip {
  font-size: var(--font-size-md);
  background: var(--surface-page);
  color: var(--text-code);
  padding: var(--space-6) var(--space-7);
  margin: 0 0 var(--space-10);
  overflow-x: auto;
  border-left: var(--border-width-accent) solid var(--color-accent);
  white-space: pre-wrap;
}
.options {
  display: grid;
  gap: var(--space-5);
  margin-bottom: var(--space-10);
}
.submit-row {
  display: flex;
  justify-content: flex-end;
}
</style>
