<script setup lang="ts">
import PixelFrame from '@/shared/components/PixelFrame.vue'
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
        <button
          type="button"
          class="btn-arcade font-label"
          :disabled="disabled || !selectedAnswer"
          @click="$emit('submit')"
        >
          {{ isLastQuestion ? 'HOÀN THÀNH BÀI THI' : 'NỘP CÂU TRẢ LỜI' }}
        </button>
      </div>
    </div>
  </PixelFrame>
</template>

<style scoped>
.question-card {
  padding: 26px 24px;
}
.q-label {
  font-size: 9px;
  color: var(--text-label-accent);
  margin-bottom: 14px;
  display: block;
}
.q-passage {
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-secondary);
  background: var(--surface-page);
  padding: 12px 14px;
  margin: 0 0 18px;
  border-left: 3px solid var(--border-info);
}
.q-passage-eyebrow {
  display: block;
  font-size: 11px;
  letter-spacing: 1px;
  color: var(--text-secondary);
  margin-bottom: 6px;
}
.q-text {
  font-size: 18px;
  line-height: 1.55;
  font-weight: 500;
  margin: 0 0 22px;
  color: var(--text-primary);
}
.code-snip {
  font-size: 13px;
  background: var(--surface-page);
  color: var(--text-code);
  padding: 12px 14px;
  margin: 0 0 22px;
  overflow-x: auto;
  border-left: 3px solid var(--color-accent);
  white-space: pre-wrap;
}
.options {
  display: grid;
  gap: 10px;
  margin-bottom: 24px;
}
.submit-row {
  display: flex;
  justify-content: flex-end;
}
.btn-arcade {
  font-weight: 700;
  font-size: 13px;
  letter-spacing: 1.5px;
  text-transform: uppercase;
  background: var(--status-success);
  color: var(--text-on-accent);
  border: none;
  padding: 16px 28px;
  cursor: pointer;
  box-shadow: 0 4px 0 var(--status-success-subtle);
}
.btn-arcade:active:not(:disabled) {
  transform: translateY(4px);
  box-shadow: none;
}
.btn-arcade:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
