<script setup lang="ts">
import { ref } from 'vue';
import { apiFetch } from '../utils/api';
import PixelFrame from '../shared/components/PixelFrame.vue';
import AppButton from '../shared/components/AppButton.vue';

const emit = defineEmits<{
  (e: 'back'): void;
  (e: 'created', templateId: string): void;
}>();

type ExamType = 'toeic' | 'ielts' | 'hsk' | 'jlpt' | 'custom';

interface QuestionDraft {
  questionText: string;
  options: [string, string, string, string]; // exactly 4
  correctAnswer: 'A' | 'B' | 'C' | 'D';
  explanation: string;
  difficulty: 'easy' | 'medium' | 'hard';
}

const step = ref<1 | 2 | 3>(1);

// Step 1: Template info
const templateForm = ref({
  name: '',
  examType: 'custom' as ExamType,
  description: '',
  duration: 30,
  passingScore: 70,
  level: '',
});

// Step 2: Questions
const questions = ref<QuestionDraft[]>([]);

const blankQuestion = (): QuestionDraft => ({
  questionText: '',
  options: ['', '', '', ''],
  correctAnswer: 'A',
  explanation: '',
  difficulty: 'medium',
});

const addQuestion = () => { questions.value.push(blankQuestion()); };
const removeQuestion = (i: number) => { questions.value.splice(i, 1); };

// Step 3: Saving
const isSaving = ref(false);
const saveError = ref('');

const EXAM_TYPES: { value: ExamType; label: string; icon: string }[] = [
  { value: 'toeic', label: 'TOEIC', icon: '🇺🇸' },
  { value: 'ielts', label: 'IELTS', icon: '🇬🇧' },
  { value: 'hsk', label: 'HSK', icon: '🇨🇳' },
  { value: 'jlpt', label: 'JLPT', icon: '🇯🇵' },
  { value: 'custom', label: 'Custom', icon: '⚙️' },
];

const OPTION_KEYS = ['A', 'B', 'C', 'D'] as const;

const step1Valid = () => {
  return templateForm.value.name.trim().length >= 3 && templateForm.value.duration > 0;
};

const step2Valid = () => {
  return questions.value.length >= 1 && questions.value.every(
    (q) => q.questionText.trim() && q.options.every((o) => o.trim()),
  );
};

const goToStep2 = () => {
  if (!step1Valid()) return;
  if (questions.value.length === 0) addQuestion();
  step.value = 2;
};

const saveExam = async () => {
  if (!step2Valid()) return;
  isSaving.value = true;
  saveError.value = '';

  try {
    // 1. Create template
    const templateRes = await apiFetch('/api/exams/templates', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...templateForm.value,
        totalQuestions: questions.value.length,
      }),
    });
    if (!templateRes.ok) throw new Error('Failed to create template');
    const template = await templateRes.json();

    // 2. Create questions
    for (const q of questions.value) {
      const res = await apiFetch(`/api/exams/templates/${template._id}/questions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...q,
          options: q.options.map((o, i) => `${OPTION_KEYS[i]}. ${o}`),
          type: 'multiple-choice',
        }),
      });
      if (!res.ok) throw new Error('Failed to create question');
    }

    step.value = 3;
    setTimeout(() => emit('created', template._id), 1500);
  } catch (err: any) {
    saveError.value = err.message || 'Something went wrong.';
  } finally {
    isSaving.value = false;
  }
};
</script>

<template>
  <div class="creator-screen">
    <!-- Header -->
    <div class="creator-header">
      <button type="button" class="header-back font-label" @click="emit('back')">← BACK</button>
      <h1 class="creator-title font-body">Create Custom Exam</h1>
      <!-- Step indicator -->
      <div class="step-indicator" aria-hidden="true">
        <span
          v-for="s in [1, 2, 3]" :key="s"
          class="step-cell font-label"
          :class="{ 'step-cell--current': step === s, 'step-cell--done': step > s }"
        >
          {{ step > s ? '✓' : s }}
        </span>
      </div>
    </div>

    <div class="creator-body">

      <!-- ── Step 1: Exam Info ──────────────────────────────────────────────── -->
      <div v-if="step === 1">
        <h2 class="section-title font-body">Step 1 — Exam Details</h2>

        <PixelFrame frame-color="amber" surface="cabinet" :ring-width="3">
          <div class="step-panel">

            <!-- Exam Type Picker -->
            <div class="arcade-field">
              <span class="arcade-label">EXAM TYPE</span>
              <div class="type-grid">
                <button
                  v-for="et in EXAM_TYPES" :key="et.value"
                  type="button"
                  class="type-btn font-label"
                  :class="{ 'type-btn--active': templateForm.examType === et.value }"
                  @click="templateForm.examType = et.value"
                >
                  <span class="type-btn-icon" aria-hidden="true">{{ et.icon }}</span>
                  {{ et.label }}
                </button>
              </div>
            </div>

            <!-- Name -->
            <div class="arcade-field">
              <label class="arcade-label" for="exam-name">EXAM NAME *</label>
              <input
                id="exam-name"
                v-model="templateForm.name"
                type="text"
                placeholder="e.g. My TOEIC Practice Set 1"
                class="arcade-input"
              />
            </div>

            <!-- Description -->
            <div class="arcade-field">
              <label class="arcade-label" for="exam-desc">DESCRIPTION (OPTIONAL)</label>
              <textarea
                id="exam-desc"
                v-model="templateForm.description"
                rows="2"
                placeholder="Brief description of this exam..."
                class="arcade-input"
              ></textarea>
            </div>

            <!-- Duration & Passing Score & Level -->
            <div class="step1-grid">
              <div class="arcade-field">
                <label class="arcade-label" for="exam-duration">DURATION (MIN) *</label>
                <input
                  id="exam-duration"
                  v-model.number="templateForm.duration"
                  type="number"
                  min="1"
                  max="300"
                  class="arcade-input"
                />
              </div>
              <div class="arcade-field">
                <label class="arcade-label" for="exam-pass">PASS SCORE (%)</label>
                <input
                  id="exam-pass"
                  v-model.number="templateForm.passingScore"
                  type="number"
                  min="1"
                  max="100"
                  class="arcade-input"
                />
              </div>
              <div class="arcade-field">
                <label class="arcade-label" for="exam-level">LEVEL / PART</label>
                <input
                  id="exam-level"
                  v-model="templateForm.level"
                  type="text"
                  placeholder="e.g. N4, HSK 3"
                  class="arcade-input"
                />
              </div>
            </div>

            <AppButton class="full-width" :disabled="!step1Valid()" @click="goToStep2">
              NEXT: ADD QUESTIONS →
            </AppButton>
          </div>
        </PixelFrame>
      </div>

      <!-- ── Step 2: Questions ──────────────────────────────────────────────── -->
      <div v-else-if="step === 2">
        <div class="step2-header">
          <h2 class="section-title font-body">
            Step 2 — Add Questions
            <span class="section-count font-label">({{ questions.length }} SO FAR)</span>
          </h2>
          <button type="button" class="header-back font-label" @click="step = 1">← BACK</button>
        </div>

        <div class="question-list">
          <div v-for="(q, qi) in questions" :key="qi" class="question-card">
            <div class="question-card-top">
              <span class="question-num font-label">QUESTION {{ qi + 1 }}</span>
              <button type="button" class="btn-remove font-label" @click="removeQuestion(qi)">REMOVE</button>
            </div>

            <!-- Question text -->
            <div class="arcade-field">
              <label class="arcade-label">QUESTION TEXT *</label>
              <textarea
                v-model="q.questionText"
                rows="2"
                placeholder="e.g. The meeting has been _____ until next Monday."
                class="arcade-input"
              ></textarea>
            </div>

            <!-- Options -->
            <div class="options-grid">
              <div v-for="(_, oi) in q.options" :key="oi" class="arcade-field">
                <label class="arcade-label">
                  OPTION {{ OPTION_KEYS[oi] }}
                  <span v-if="q.correctAnswer === OPTION_KEYS[oi]" class="correct-tag">(CORRECT)</span>
                </label>
                <input
                  v-model="q.options[oi]"
                  type="text"
                  :placeholder="`Answer ${OPTION_KEYS[oi]}...`"
                  class="arcade-input"
                />
              </div>
            </div>

            <!-- Correct Answer + Difficulty -->
            <div class="question-row2">
              <div class="arcade-field">
                <span class="arcade-label">CORRECT ANSWER</span>
                <div class="answer-keys">
                  <button
                    v-for="k in OPTION_KEYS" :key="k"
                    type="button"
                    class="answer-key font-pixel"
                    :class="{ 'answer-key--selected': q.correctAnswer === k }"
                    @click="q.correctAnswer = k"
                  >
                    {{ k }}
                  </button>
                </div>
              </div>
              <div class="arcade-field">
                <label class="arcade-label">DIFFICULTY</label>
                <select v-model="q.difficulty" class="arcade-input">
                  <option value="easy">Easy</option>
                  <option value="medium">Medium</option>
                  <option value="hard">Hard</option>
                </select>
              </div>
            </div>

            <!-- Explanation -->
            <div class="arcade-field">
              <label class="arcade-label">EXPLANATION (OPTIONAL)</label>
              <input
                v-model="q.explanation"
                type="text"
                placeholder="Why is this answer correct?"
                class="arcade-input"
              />
            </div>
          </div>
        </div>

        <!-- Add Question Button -->
        <button type="button" class="btn-add-question font-label" @click="addQuestion">
          + ADD QUESTION
        </button>

        <!-- Save Button -->
        <div class="save-block">
          <p v-if="saveError" class="save-error font-label">{{ saveError }}</p>
          <AppButton class="full-width" :disabled="!step2Valid() || isSaving" @click="saveExam">
            {{ isSaving ? 'SAVING…' : `CREATE EXAM (${questions.length} QUESTIONS)` }}
          </AppButton>
        </div>
      </div>

      <!-- ── Step 3: Done ───────────────────────────────────────────────────── -->
      <div v-else class="done-screen">
        <div class="done-icon" aria-hidden="true">🎉</div>
        <h2 class="done-title font-body">Exam Created!</h2>
        <p class="done-sub font-label">REDIRECTING YOU TO THE EXAM ROOM…</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.creator-screen {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.creator-header {
  display: flex;
  align-items: center;
  gap: var(--space-8);
  padding: var(--space-8) var(--space-10);
  background: var(--cabinet);
  border-bottom: var(--space-1) solid var(--cabinet-light);
  flex-shrink: 0;
}
.header-back {
  background: none;
  border: none;
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
  letter-spacing: var(--tracking-normal);
  cursor: pointer;
}
.header-back:hover {
  color: var(--text-primary);
}
.creator-title {
  font-size: var(--font-size-xl);
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}
.step-indicator {
  margin-left: auto;
  display: flex;
  gap: var(--space-3);
}
.step-cell {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--font-size-base);
  font-weight: 700;
  background: var(--surface-page);
  color: var(--text-secondary);
}
.step-cell--current {
  background: var(--state-selected-bg);
  color: var(--text-on-accent);
}
.step-cell--done {
  background: var(--status-success);
  color: var(--text-on-accent);
}

.creator-body {
  flex: 1;
  overflow-y: auto;
  max-width: 760px;
  margin: 0 auto;
  width: 100%;
  padding: var(--space-10);
}

.section-title {
  font-size: var(--font-size-lg);
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 var(--space-8);
}
.section-count {
  font-size: var(--font-size-sm);
  font-weight: 400;
  color: var(--text-secondary);
  margin-left: var(--space-3);
}

.step-panel {
  padding: var(--space-10);
  display: flex;
  flex-direction: column;
  gap: var(--space-8);
}
.type-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: var(--space-4);
}
.type-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-5) var(--space-3);
  background: var(--surface-panel-border);
  border: var(--space-1) solid var(--surface-panel-border);
  color: var(--text-secondary);
  font-size: var(--font-size-xs);
  font-weight: 700;
  cursor: pointer;
}
.type-btn:hover:not(.type-btn--active) {
  border-color: var(--muted);
  color: var(--text-primary);
}
.type-btn--active {
  background: var(--state-selected-bg);
  border-color: var(--state-selected-bg);
  color: var(--text-on-accent);
}
.type-btn-icon {
  font-size: var(--font-size-xl);
}

.step1-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-7);
}

.full-width {
  width: 100%;
}

.step2-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-8);
}

.question-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-7);
  margin-bottom: var(--space-7);
}
.question-card {
  background: var(--surface-panel);
  border: var(--space-1) solid var(--surface-panel-border);
  padding: var(--space-9);
  display: flex;
  flex-direction: column;
  gap: var(--space-7);
}
.question-card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.question-num {
  font-size: var(--font-size-sm);
  font-weight: 700;
  letter-spacing: var(--tracking-normal);
  color: var(--text-label-accent);
}
.btn-remove {
  background: none;
  border: none;
  color: var(--status-danger);
  font-size: var(--font-size-xs);
  letter-spacing: var(--tracking-normal);
  cursor: pointer;
  padding: var(--space-2) var(--space-4);
}
.btn-remove:hover {
  background: var(--status-danger-subtle);
  color: var(--text-primary);
}

.options-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-5);
}
.correct-tag {
  color: var(--status-success);
  font-weight: 400;
  margin-left: var(--space-2);
  text-transform: none;
  letter-spacing: 0;
}

.question-row2 {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-8);
}
.answer-keys {
  display: flex;
  gap: var(--space-4);
}
.answer-key {
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
.answer-key:hover:not(.answer-key--selected) {
  color: var(--text-primary);
  background: var(--state-hover-surface);
}
.answer-key--selected {
  background: var(--status-success);
  color: var(--text-on-accent);
}

.btn-add-question {
  width: 100%;
  padding: var(--space-7);
  background: transparent;
  border: var(--space-1) dashed var(--surface-panel-border);
  color: var(--text-secondary);
  font-size: var(--font-size-base);
  letter-spacing: var(--tracking-normal);
  cursor: pointer;
}
.btn-add-question:hover {
  border-color: var(--color-accent);
  color: var(--color-accent);
}

.save-block {
  margin-top: var(--space-10);
}
.save-error {
  color: var(--status-danger);
  font-size: var(--font-size-base);
  background: var(--surface-page);
  border-left: var(--border-width-accent) solid var(--status-danger);
  padding: var(--space-5) var(--space-6);
  margin: 0 0 var(--space-6);
}

.done-screen {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  /* stylelint-disable-next-line scale-unlimited/declaration-strict-value -- approved Step 2 - layout one-off, see design-tokens.json notes */
  padding: 100px 0;
  text-align: center;
}
.done-icon {
  /* stylelint-disable-next-line scale-unlimited/declaration-strict-value -- approved Step 2 - font-size one-off, see design-tokens.json notes */
  font-size: 56px;
  margin-bottom: var(--space-7);
  animation: done-bounce 0.6s ease infinite alternate;
}
@keyframes done-bounce {
  to {
    transform: translateY(-10px);
  }
}
@media (prefers-reduced-motion: reduce) {
  .done-icon {
    animation: none;
  }
}
.done-title {
  font-size: var(--font-size-2xl);
  font-weight: 700;
  color: var(--status-success);
  margin: 0 0 var(--space-4);
}
.done-sub {
  color: var(--text-secondary);
  font-size: var(--font-size-base);
}

.header-back:focus-visible,
.type-btn:focus-visible,
.arcade-input:focus-visible,
.btn-remove:focus-visible,
.answer-key:focus-visible,
.btn-add-question:focus-visible {
  outline: var(--focus-ring-width) solid var(--color-focus-ring);
  outline-offset: 2px;
}
</style>
