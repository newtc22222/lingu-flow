<script setup lang="ts">
import { ref } from 'vue';
import { apiFetch } from '../utils/api';

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
const OPTION_COLORS = ['text-blue-400', 'text-orange-400', 'text-rose-400', 'text-emerald-400'];

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
  <div class="flex flex-col h-full bg-slate-900 text-slate-100 overflow-y-auto">

    <!-- Header -->
    <div class="shrink-0 bg-slate-800 border-b border-slate-700 px-6 py-4 flex items-center gap-4">
      <button
        @click="emit('back')"
        class="text-slate-400 hover:text-slate-200 transition-colors cursor-pointer"
      >
        ← Back
      </button>
      <h1 class="text-xl font-bold text-slate-100">Create Custom Exam</h1>
      <!-- Step indicator -->
      <div class="ml-auto flex items-center gap-2 text-sm">
        <span
          v-for="s in [1, 2, 3]" :key="s"
          :class="[
            'w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition-all',
            step === s
              ? 'bg-indigo-600 text-white'
              : step > s
                ? 'bg-emerald-600 text-white'
                : 'bg-slate-700 text-slate-400',
          ]"
        >
          {{ step > s ? '✓' : s }}
        </span>
      </div>
    </div>

    <div class="flex-1 max-w-3xl mx-auto w-full px-6 py-6">

      <!-- ── Step 1: Exam Info ──────────────────────────────────────────────── -->
      <div v-if="step === 1">
        <h2 class="text-lg font-semibold text-slate-200 mb-5">Step 1 — Exam Details</h2>

        <div class="bg-slate-800 rounded-2xl border border-slate-700 p-6 space-y-5">

          <!-- Exam Type Picker -->
          <div>
            <label class="block text-sm text-slate-400 mb-2">Exam Type</label>
            <div class="grid grid-cols-5 gap-2">
              <button
                v-for="et in EXAM_TYPES" :key="et.value"
                @click="templateForm.examType = et.value"
                :class="[
                  'flex flex-col items-center gap-1 p-3 rounded-xl border transition-all text-xs font-semibold cursor-pointer',
                  templateForm.examType === et.value
                    ? 'bg-indigo-600/20 border-indigo-500 text-indigo-300'
                    : 'bg-slate-700/50 border-slate-600 text-slate-400 hover:bg-slate-700',
                ]"
              >
                <span class="text-xl">{{ et.icon }}</span>
                {{ et.label }}
              </button>
            </div>
          </div>

          <!-- Name -->
          <div>
            <label class="block text-sm text-slate-400 mb-1">Exam Name <span class="text-rose-400">*</span></label>
            <input
              v-model="templateForm.name"
              type="text"
              placeholder="e.g. My TOEIC Practice Set 1"
              class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2.5 text-slate-100 focus:border-indigo-500 focus:outline-none transition-colors"
            />
          </div>

          <!-- Description -->
          <div>
            <label class="block text-sm text-slate-400 mb-1">Description (optional)</label>
            <textarea
              v-model="templateForm.description"
              rows="2"
              placeholder="Brief description of this exam..."
              class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2.5 text-slate-100 focus:border-indigo-500 focus:outline-none transition-colors resize-none"
            ></textarea>
          </div>

          <!-- Duration & Passing Score & Level -->
          <div class="grid grid-cols-3 gap-4">
            <div>
              <label class="block text-sm text-slate-400 mb-1">Duration (min) <span class="text-rose-400">*</span></label>
              <input
                v-model.number="templateForm.duration"
                type="number"
                min="1"
                max="300"
                class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2.5 text-slate-100 focus:border-indigo-500 focus:outline-none transition-colors"
              />
            </div>
            <div>
              <label class="block text-sm text-slate-400 mb-1">Pass Score (%)</label>
              <input
                v-model.number="templateForm.passingScore"
                type="number"
                min="1"
                max="100"
                class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2.5 text-slate-100 focus:border-indigo-500 focus:outline-none transition-colors"
              />
            </div>
            <div>
              <label class="block text-sm text-slate-400 mb-1">Level / Part</label>
              <input
                v-model="templateForm.level"
                type="text"
                placeholder="e.g. N4, HSK 3"
                class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2.5 text-slate-100 focus:border-indigo-500 focus:outline-none transition-colors"
              />
            </div>
          </div>

          <button
            @click="goToStep2"
            :disabled="!step1Valid()"
            class="w-full py-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl font-semibold transition-colors cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Next: Add Questions →
          </button>
        </div>
      </div>

      <!-- ── Step 2: Questions ──────────────────────────────────────────────── -->
      <div v-else-if="step === 2">
        <div class="flex items-center justify-between mb-5">
          <h2 class="text-lg font-semibold text-slate-200">
            Step 2 — Add Questions
            <span class="text-sm font-normal text-slate-400 ml-2">({{ questions.length }} so far)</span>
          </h2>
          <button
            @click="step = 1"
            class="text-sm text-slate-400 hover:text-slate-200 cursor-pointer"
          >
            ← Back
          </button>
        </div>

        <div class="space-y-4 mb-4">
          <div
            v-for="(q, qi) in questions"
            :key="qi"
            class="bg-slate-800 rounded-2xl border border-slate-700 p-5"
          >
            <div class="flex items-center justify-between mb-4">
              <span class="text-sm font-semibold text-indigo-400">Question {{ qi + 1 }}</span>
              <button
                @click="removeQuestion(qi)"
                class="text-xs text-rose-400 hover:text-rose-300 cursor-pointer"
              >
                Remove
              </button>
            </div>

            <!-- Question text -->
            <div class="mb-3">
              <label class="block text-xs text-slate-400 mb-1">Question Text <span class="text-rose-400">*</span></label>
              <textarea
                v-model="q.questionText"
                rows="2"
                placeholder="e.g. The meeting has been _____ until next Monday."
                class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2.5 text-slate-100 focus:border-indigo-500 focus:outline-none transition-colors resize-none text-sm"
              ></textarea>
            </div>

            <!-- Options -->
            <div class="grid grid-cols-2 gap-2 mb-3">
              <div v-for="(_, oi) in q.options" :key="oi">
                <label :class="['block text-xs mb-1 font-semibold', OPTION_COLORS[oi]]">
                  Option {{ OPTION_KEYS[oi] }}
                  <span v-if="q.correctAnswer === OPTION_KEYS[oi]" class="text-emerald-400 font-normal ml-1">(correct)</span>
                </label>
                <input
                  v-model="q.options[oi]"
                  type="text"
                  :placeholder="`Answer ${OPTION_KEYS[oi]}...`"
                  class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-100 focus:border-indigo-500 focus:outline-none transition-colors text-sm"
                />
              </div>
            </div>

            <!-- Correct Answer + Difficulty -->
            <div class="grid grid-cols-2 gap-4 mb-3">
              <div>
                <label class="block text-xs text-slate-400 mb-1">Correct Answer</label>
                <div class="flex gap-2">
                  <button
                    v-for="k in OPTION_KEYS" :key="k"
                    @click="q.correctAnswer = k"
                    :class="[
                      'w-9 h-9 rounded-lg font-bold text-sm transition-all cursor-pointer',
                      q.correctAnswer === k
                        ? 'bg-emerald-600 text-white'
                        : 'bg-slate-700 text-slate-400 hover:bg-slate-600',
                    ]"
                  >
                    {{ k }}
                  </button>
                </div>
              </div>
              <div>
                <label class="block text-xs text-slate-400 mb-1">Difficulty</label>
                <select
                  v-model="q.difficulty"
                  class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-100 focus:border-indigo-500 focus:outline-none transition-colors text-sm"
                >
                  <option value="easy">Easy</option>
                  <option value="medium">Medium</option>
                  <option value="hard">Hard</option>
                </select>
              </div>
            </div>

            <!-- Explanation -->
            <div>
              <label class="block text-xs text-slate-400 mb-1">Explanation (optional)</label>
              <input
                v-model="q.explanation"
                type="text"
                placeholder="Why is this answer correct?"
                class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-100 focus:border-indigo-500 focus:outline-none transition-colors text-sm"
              />
            </div>
          </div>
        </div>

        <!-- Add Question Button -->
        <button
          @click="addQuestion"
          class="w-full py-3 border-2 border-dashed border-slate-700 hover:border-indigo-500 text-slate-400 hover:text-indigo-400 rounded-xl transition-all cursor-pointer text-sm"
        >
          + Add Question
        </button>

        <!-- Save Button -->
        <div class="mt-6">
          <p v-if="saveError" class="text-rose-400 text-sm mb-2">{{ saveError }}</p>
          <button
            @click="saveExam"
            :disabled="!step2Valid() || isSaving"
            class="w-full py-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl font-semibold transition-colors cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {{ isSaving ? 'Saving...' : `Create Exam (${questions.length} questions)` }}
          </button>
        </div>
      </div>

      <!-- ── Step 3: Done ───────────────────────────────────────────────────── -->
      <div v-else class="flex flex-col items-center justify-center py-20 text-center">
        <div class="text-6xl mb-4 animate-bounce">🎉</div>
        <h2 class="text-2xl font-bold text-emerald-400 mb-2">Exam Created!</h2>
        <p class="text-slate-400">Redirecting you to the exam room...</p>
      </div>
    </div>
  </div>
</template>
