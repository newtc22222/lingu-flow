<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import PixelFrame from '@/shared/components/PixelFrame.vue';
import AppButton from '@/shared/components/AppButton.vue';
import AnswerOption from './AnswerOption.vue';
import type { ExamQuestion } from '../store/examStore';
import { OPTION_KEYS } from '../store/examStore';

const props = defineProps<{
  question: ExamQuestion;
  selectedAnswer?: string;
  disabled?: boolean;
  isLastQuestion: boolean;
  current: number;
  total: number;
}>();

const emit = defineEmits<{
  (e: 'select', optionKey: string): void;
  (e: 'submit'): void;
  (e: 'previous'): void;
  (e: 'next'): void;
}>();

const { t } = useI18n();

const hasPassage = computed(() => Boolean(props.question.passage?.trim()));
const questionLabel = computed(() =>
  props.question.type ? props.question.type.toUpperCase() : 'MULTIPLE CHOICE',
);
</script>

<template>
  <div class="q-layout" :class="{ 'q-layout--split': hasPassage }">
    <PixelFrame
      v-if="hasPassage"
      frame-color="cabinet-light"
      surface="ink"
      :ring-width="3"
      class="q-passage-frame"
    >
      <div class="q-passage-scroll">
        <span class="q-passage-eyebrow font-label">{{ t('results.passage') }}</span>
        <p class="q-passage-text font-body">{{ question.passage }}</p>
      </div>
    </PixelFrame>

    <PixelFrame frame-color="amber" surface="cabinet" :ring-width="3" class="q-stem-frame">
      <div class="question-card">
        <div class="q-meta font-label">
          <span class="q-label">▸ {{ questionLabel }}</span>
          <span class="q-index">{{ t('exam.question', { current, total }) }}</span>
        </div>

        <p class="q-text font-body">{{ question.questionText }}</p>

        <div class="options">
          <AnswerOption
            v-for="(option, i) in question.options"
            :key="OPTION_KEYS[i]"
            :option-key="OPTION_KEYS[i]"
            :label="option"
            :selected="selectedAnswer === OPTION_KEYS[i]"
            :disabled="disabled"
            @select="emit('select', OPTION_KEYS[i])"
          />
        </div>

        <div class="nav-row">
          <AppButton
            variant="secondary"
            :disabled="disabled || current <= 1"
            @click="emit('previous')"
          >
            {{ t('exam.previous') }}
          </AppButton>
          <AppButton :disabled="disabled" @click="isLastQuestion ? emit('submit') : emit('next')">
            {{ isLastQuestion ? t('exam.submit') : t('exam.next') }}
          </AppButton>
        </div>
      </div>
    </PixelFrame>
  </div>
</template>

<style scoped>
.q-layout {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
  min-height: 0;
  flex: 1 1 0;
}
@media (min-width: 768px) {
  .q-layout--split {
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
    align-items: stretch;
  }
}

.q-passage-frame,
.q-stem-frame {
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.q-passage-scroll {
  padding: var(--space-8);
  overflow-y: auto;
  max-height: 40vh;
  min-height: 0;
}
@media (min-width: 768px) {
  .q-passage-scroll {
    max-height: none;
    height: 100%;
  }
}
.q-passage-eyebrow {
  display: block;
  font-size: var(--font-size-2xs);
  letter-spacing: var(--tracking-wide);
  color: var(--text-secondary);
  margin-bottom: var(--space-4);
}
.q-passage-text {
  font-size: var(--font-size-md-plus);
  line-height: 1.6;
  color: var(--text-primary);
  margin: 0;
  white-space: pre-wrap;
}

.question-card {
  padding: var(--space-9) var(--space-8);
  display: flex;
  flex-direction: column;
  gap: var(--space-7);
  min-height: 0;
  overflow-y: auto;
  max-height: 55vh;
}
@media (min-width: 768px) {
  .question-card {
    max-height: none;
    flex: 1;
  }
}
.q-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-5);
  flex-wrap: wrap;
}
.q-label {
  font-size: var(--font-size-2xs);
  letter-spacing: var(--tracking-wide);
  color: var(--text-label-accent);
}
.q-index {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  letter-spacing: var(--tracking-normal);
}
.q-text {
  font-size: var(--font-size-xl);
  line-height: 1.55;
  font-weight: 500;
  margin: 0;
  color: var(--text-primary);
}
.options {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}
.nav-row {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-5);
  margin-top: var(--space-2);
  flex-wrap: wrap;
}
</style>
