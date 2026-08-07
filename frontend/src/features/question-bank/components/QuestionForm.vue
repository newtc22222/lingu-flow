<script setup lang="ts">
/**
 * Create/edit form for a bank question.
 *
 * The four option inputs hold BARE text; the positional "A. " prefix is applied
 * on submit (see `@/utils/options`), so the user never edits a letter they
 * can't meaningfully change.
 *
 * `framed` (default true): wraps in PixelFrame for ExamComposer / standalone.
 * Pass `framed={false}` when a parent bay already provides the frame.
 */
import { computed, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import AppButton from '@/shared/components/AppButton.vue';
import PixelFrame from '@/shared/components/PixelFrame.vue';
import { OPTION_KEYS, toFormOptions, toStoredOptions } from '@/utils/options';
import { DIFFICULTIES, EXAM_TYPES, type BankQuestion } from '../types';

const props = withDefaults(
  defineProps<{
    question?: BankQuestion | null;
    isSaving?: boolean;
    error?: string | null;
    framed?: boolean;
  }>(),
  { framed: true, isSaving: false, error: null, question: null },
);

const emit = defineEmits<{
  (e: 'submit', payload: Record<string, unknown>): void;
  (e: 'cancel'): void;
}>();

const { t } = useI18n();

const isEditing = computed(() => Boolean(props.question));

function blankForm() {
  return {
    examType: 'toeic',
    part: '',
    passageGroup: '',
    questionText: '',
    passage: '',
    options: ['', '', '', ''],
    correctAnswer: 'A',
    explanation: '',
    difficulty: 'medium',
    tags: '',
  };
}

const form = ref(blankForm());

watch(
  () => props.question,
  (question) => {
    form.value = question
      ? {
          examType: question.examType,
          part: question.part ?? '',
          passageGroup: question.passageGroup ?? '',
          questionText: question.questionText,
          passage: question.passage ?? '',
          options: toFormOptions(question.options),
          correctAnswer: question.correctAnswer,
          explanation: question.explanation ?? '',
          difficulty: question.difficulty,
          tags: (question.tags ?? []).join(', '),
        }
      : blankForm();
  },
  { immediate: true },
);

const isValid = computed(
  () =>
    form.value.questionText.trim().length > 0 &&
    form.value.options.every((option) => option.trim().length > 0),
);

function submit() {
  if (!isValid.value) return;
  emit('submit', {
    examType: form.value.examType,
    part: form.value.part.trim() || null,
    passageGroup: form.value.passageGroup.trim() || null,
    questionText: form.value.questionText,
    passage: form.value.passage.trim() || null,
    type: 'multiple-choice',
    options: toStoredOptions(form.value.options),
    correctAnswer: form.value.correctAnswer,
    explanation: form.value.explanation.trim() || null,
    difficulty: form.value.difficulty,
    tags: form.value.tags
      .split(',')
      .map((tag) => tag.trim())
      .filter(Boolean),
  });
}
</script>

<template>
  <component
    :is="framed ? PixelFrame : 'div'"
    v-bind="framed ? { frameColor: 'amber', surface: 'cabinet', ringWidth: 3 } : {}"
    :class="framed ? 'qform-frame' : 'qform-embedded-wrap'"
  >
    <form class="qform" :class="{ 'qform--embedded': !framed }" @submit.prevent="submit">
      <h3 class="qform-title font-label">
        {{ isEditing ? t('questionBank.editTitle') : t('questionBank.createTitle') }}
      </h3>

      <p v-if="error" class="qform-error font-label">{{ error }}</p>

      <div class="qform-row">
        <div class="arcade-field">
          <label class="arcade-label" for="qform-exam-type">{{ t('questionBank.examType') }}</label>
          <select id="qform-exam-type" v-model="form.examType" class="arcade-input">
            <option v-for="type in EXAM_TYPES" :key="type" :value="type">
              {{ type.toUpperCase() }}
            </option>
          </select>
        </div>

        <div class="arcade-field">
          <label class="arcade-label" for="qform-part">{{ t('questionBank.partOptional') }}</label>
          <input
            id="qform-part"
            v-model="form.part"
            type="text"
            class="arcade-input"
            :placeholder="t('questionBank.partPlaceholder')"
          />
        </div>

        <div class="arcade-field">
          <label class="arcade-label" for="qform-difficulty">
            {{ t('questionBank.difficulty') }}
          </label>
          <select id="qform-difficulty" v-model="form.difficulty" class="arcade-input">
            <option v-for="level in DIFFICULTIES" :key="level" :value="level">
              {{ t(`questionBank.difficulties.${level}`) }}
            </option>
          </select>
        </div>
      </div>

      <div class="arcade-field">
        <label class="arcade-label" for="qform-text">{{ t('questionBank.questionText') }}</label>
        <textarea
          id="qform-text"
          v-model="form.questionText"
          rows="2"
          required
          class="arcade-input"
        ></textarea>
      </div>

      <div class="arcade-field">
        <label class="arcade-label" for="qform-passage">{{ t('questionBank.passage') }}</label>
        <textarea
          id="qform-passage"
          v-model="form.passage"
          rows="3"
          class="arcade-input"
        ></textarea>
      </div>

      <div class="arcade-field">
        <label class="arcade-label" for="qform-passage-group">
          {{ t('questionBank.passageGroup') }}
        </label>
        <input
          id="qform-passage-group"
          v-model="form.passageGroup"
          type="text"
          class="arcade-input"
          :placeholder="t('questionBank.passageGroupPlaceholder')"
        />
        <span class="qform-hint font-body">{{ t('questionBank.passageGroupHint') }}</span>
      </div>

      <div class="qform-options">
        <div v-for="(_, index) in form.options" :key="index" class="arcade-field">
          <label class="arcade-label" :for="`qform-option-${index}`">
            {{ t('examCreator.option', { key: OPTION_KEYS[index] }) }}
          </label>
          <input
            :id="`qform-option-${index}`"
            v-model="form.options[index]"
            type="text"
            class="arcade-input"
          />
        </div>
      </div>

      <div class="arcade-field">
        <span class="arcade-label">{{ t('questionBank.correctAnswer') }}</span>
        <div class="qform-keys">
          <button
            v-for="key in OPTION_KEYS"
            :key="key"
            type="button"
            class="qform-key font-label"
            :class="{ 'qform-key--selected': form.correctAnswer === key }"
            :aria-pressed="form.correctAnswer === key"
            @click="form.correctAnswer = key"
          >
            {{ key }}
          </button>
        </div>
      </div>

      <div class="arcade-field">
        <label class="arcade-label" for="qform-explanation">
          {{ t('questionBank.explanation') }}
        </label>
        <input id="qform-explanation" v-model="form.explanation" type="text" class="arcade-input" />
      </div>

      <div class="arcade-field">
        <label class="arcade-label" for="qform-tags">{{ t('questionBank.tagsField') }}</label>
        <input
          id="qform-tags"
          v-model="form.tags"
          type="text"
          class="arcade-input"
          :placeholder="t('questionBank.tagsPlaceholder')"
        />
      </div>

      <div class="qform-actions">
        <AppButton v-if="isEditing" variant="secondary" type="button" @click="emit('cancel')">
          {{ t('common.cancel') }}
        </AppButton>
        <AppButton type="submit" :disabled="!isValid || isSaving">
          {{
            isSaving ? t('examCreator.saving') : isEditing ? t('common.update') : t('common.save')
          }}
        </AppButton>
      </div>
    </form>
  </component>
</template>

<style scoped>
.qform-frame {
  margin-bottom: var(--space-11);
}
.qform-embedded-wrap {
  min-width: 0;
}
.qform {
  padding: var(--space-10);
  display: flex;
  flex-direction: column;
  gap: var(--space-7);
}
.qform--embedded {
  padding: var(--space-7);
  gap: var(--space-6);
}
.qform-title {
  font-size: var(--font-size-base);
  letter-spacing: var(--tracking-normal);
  color: var(--text-label-accent);
  margin: 0;
}
.qform-error {
  color: var(--status-danger);
  font-size: var(--font-size-base);
  background: var(--surface-page);
  border-left: var(--border-width-accent) solid var(--status-danger);
  padding: var(--space-5) var(--space-6);
  margin: 0;
}
.qform-row {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--space-6);
}
@media (min-width: 640px) {
  .qform-row {
    grid-template-columns: repeat(3, 1fr);
  }
}
.qform-options {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--space-5);
}
@media (min-width: 640px) {
  .qform-options {
    grid-template-columns: 1fr 1fr;
  }
}
.qform-hint {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}
.qform-keys {
  display: flex;
  gap: var(--space-4);
}
.qform-key {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--font-size-base);
  background: var(--surface-page);
  color: var(--text-secondary);
  border: none;
  cursor: pointer;
}
.qform-key:hover:not(.qform-key--selected) {
  color: var(--text-primary);
  background: var(--state-hover-surface);
}
.qform-key--selected {
  background: var(--status-success);
  color: var(--text-on-accent);
}
.qform-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-5);
}
textarea.arcade-input,
select.arcade-input {
  font-family: var(--font-body);
}
textarea.arcade-input {
  resize: vertical;
}
.qform-key:focus-visible,
.arcade-input:focus-visible {
  outline: var(--focus-ring-width) solid var(--color-focus-ring);
  outline-offset: 2px;
}
</style>
