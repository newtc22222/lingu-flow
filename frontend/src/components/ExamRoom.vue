<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch } from 'vue';
import { apiFetch } from '../utils/api';

interface Question {
  _id: string;
  type?: string;
  questionText: string;
  passage?: string;
  options: string[]; // ['A. ...', 'B. ...', 'C. ...', 'D. ...']
  orderIndex: number;
}

interface AnswerRecord {
  questionId: string;
  userAnswer: string;
  isCorrect: boolean;
  timeTaken: number;
}

interface ExamSession {
  _id: string;
  examTemplateId: string | { _id: string; name: string; duration: number };
  timeLimit: number;
  answers: AnswerRecord[];
  status: string;
}

const props = defineProps<{ templateId: string }>();
const emit = defineEmits<{
  (e: 'done', sessionId: string): void;
  (e: 'back'): void;
}>();

// ── State ────────────────────────────────────────────────────────────────────
const session = ref<ExamSession | null>(null);
const questions = ref<Question[]>([]);
const currentIdx = ref(0);
const userAnswers = ref<Record<string, string>>({}); // questionId → answer
const questionStartTime = ref<number>(Date.now());
const isLoading = ref(true);
const isSubmitting = ref(false);
const showConfirmFinish = ref(false);
const examName = ref('');
const totalSeconds = ref(0);
const secondsLeft = ref(0);
let timerInterval: ReturnType<typeof setInterval> | null = null;

// ── Computed ─────────────────────────────────────────────────────────────────
const currentQuestion = computed(() => questions.value[currentIdx.value] || null);

const answeredCount = computed(() =>
  Object.values(userAnswers.value).filter((a) => a !== '').length,
);

const timeDisplay = computed(() => {
  const m = Math.floor(secondsLeft.value / 60);
  const s = secondsLeft.value % 60;
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
});

const timerPercent = computed(() =>
  totalSeconds.value > 0 ? (secondsLeft.value / totalSeconds.value) * 100 : 100,
);

const timerColor = computed(() => {
  if (timerPercent.value > 50) return 'text-emerald-400';
  if (timerPercent.value > 20) return 'text-yellow-400';
  return 'text-rose-400 animate-pulse';
});

const timerBarColor = computed(() => {
  if (timerPercent.value > 50) return 'bg-emerald-500';
  if (timerPercent.value > 20) return 'bg-yellow-500';
  return 'bg-rose-500';
});

const OPTION_KEYS = ['A', 'B', 'C', 'D'];

// ── Methods ──────────────────────────────────────────────────────────────────
const startExam = async () => {
  isLoading.value = true;
  try {
    // 1. Create session
    const sessionRes = await apiFetch('/api/exams/sessions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ examTemplateId: props.templateId }),
    });
    const sessionData = await sessionRes.json();
    session.value = sessionData;

    // 2. Load questions
    const questionsRes = await apiFetch(`/api/exams/templates/${props.templateId}/questions`);
    questions.value = await questionsRes.json();

    // 3. Load template name
    const templateRes = await apiFetch(`/api/exams/templates/${props.templateId}`);
    const templateData = await templateRes.json();
    examName.value = templateData.name;

    // 4. Init answers map
    questions.value.forEach((q) => { userAnswers.value[q._id] = ''; });

    // 5. Start timer
    totalSeconds.value = sessionData.timeLimit * 60;
    secondsLeft.value = totalSeconds.value;
    startTimer();
  } catch (err) {
    console.error('Failed to start exam:', err);
  } finally {
    isLoading.value = false;
  }
};

const startTimer = () => {
  timerInterval = setInterval(() => {
    if (secondsLeft.value <= 0) {
      clearInterval(timerInterval!);
      finishExam('completed'); // auto-submit when time runs out
    } else {
      secondsLeft.value--;
    }
  }, 1000);
};

const selectAnswer = async (optionKey: string) => {
  if (!currentQuestion.value || !session.value) return;
  const qId = currentQuestion.value._id;
  userAnswers.value[qId] = optionKey;

  const timeTaken = Math.round((Date.now() - questionStartTime.value) / 1000);

  // Optimistically save to backend (fire-and-forget)
  apiFetch(`/api/exams/sessions/${session.value._id}/answer`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ questionId: qId, userAnswer: optionKey, timeTaken }),
  }).catch(console.error);

  // Auto-advance to next unanswered question
  if (currentIdx.value < questions.value.length - 1) {
    setTimeout(() => {
      goToNextUnanswered();
    }, 300);
  }
};

const goToNextUnanswered = () => {
  const nextUnanswered = questions.value.findIndex(
    (q, i) => i > currentIdx.value && !userAnswers.value[q._id],
  );
  if (nextUnanswered !== -1) {
    goToQuestion(nextUnanswered);
  } else {
    // Wrap-around: find any unanswered
    const anyUnanswered = questions.value.findIndex((q) => !userAnswers.value[q._id]);
    if (anyUnanswered !== -1) goToQuestion(anyUnanswered);
  }
};

const goToQuestion = (idx: number) => {
  currentIdx.value = idx;
  questionStartTime.value = Date.now();
};

const finishExam = async (status: 'completed' | 'abandoned' = 'completed') => {
  if (!session.value || isSubmitting.value) return;
  isSubmitting.value = true;
  showConfirmFinish.value = false;
  if (timerInterval) clearInterval(timerInterval);

  try {
    await apiFetch(`/api/exams/sessions/${session.value._id}/finish`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status }),
    });
    emit('done', session.value._id);
  } catch (err) {
    console.error('Failed to finish exam:', err);
    isSubmitting.value = false;
  }
};

// ── Keyboard Shortcuts ────────────────────────────────────────────────────────
const onKeyDown = (e: KeyboardEvent) => {
  if (['INPUT', 'TEXTAREA'].includes((e.target as HTMLElement).tagName)) return;
  if (showConfirmFinish.value) {
    if (e.key === 'Escape') showConfirmFinish.value = false;
    return;
  }
  switch (e.key.toUpperCase()) {
    case 'A': selectAnswer('A'); break;
    case 'B': selectAnswer('B'); break;
    case 'C': selectAnswer('C'); break;
    case 'D': selectAnswer('D'); break;
    case 'ARROWLEFT':
    case 'ARROWUP':
      if (currentIdx.value > 0) goToQuestion(currentIdx.value - 1);
      break;
    case 'ARROWRIGHT':
    case 'ARROWDOWN':
      if (currentIdx.value < questions.value.length - 1) goToQuestion(currentIdx.value + 1);
      break;
  }
};

watch(currentIdx, () => { questionStartTime.value = Date.now(); });

onMounted(() => {
  startExam();
  window.addEventListener('keydown', onKeyDown);
});

onUnmounted(() => {
  window.removeEventListener('keydown', onKeyDown);
  if (timerInterval) clearInterval(timerInterval);
});
</script>

<template>
  <div class="flex flex-col h-full bg-slate-950 text-slate-100 select-none overflow-hidden">

    <!-- Loading Overlay -->
    <div v-if="isLoading" class="flex-1 flex items-center justify-center">
      <div class="text-center">
        <div class="text-5xl mb-4 animate-bounce">📝</div>
        <p class="text-slate-400 animate-pulse">Preparing your exam...</p>
      </div>
    </div>

    <template v-else-if="session && questions.length">
      <!-- ── Top Bar ─────────────────────────────────────────────────────────── -->
      <div class="shrink-0 bg-slate-900 border-b border-slate-800 px-6 py-3 flex items-center justify-between gap-4">
        <div class="flex items-center gap-3 min-w-0">
          <button
            @click="showConfirmFinish = true"
            class="text-slate-500 hover:text-slate-300 transition-colors p-1 cursor-pointer"
            title="Exit Exam"
          >
            ✕
          </button>
          <div class="min-w-0">
            <h2 class="text-sm font-semibold text-slate-200 truncate">{{ examName }}</h2>
            <div class="text-xs text-slate-500">
              {{ answeredCount }} / {{ questions.length }} answered
            </div>
          </div>
        </div>

        <!-- Timer -->
        <div class="flex flex-col items-center">
          <div :class="['text-2xl font-mono font-bold tabular-nums', timerColor]">
            {{ timeDisplay }}
          </div>
          <div class="w-32 h-1.5 bg-slate-800 rounded-full mt-1 overflow-hidden">
            <div
              :class="['h-full rounded-full transition-all duration-1000', timerBarColor]"
              :style="{ width: `${timerPercent}%` }"
            ></div>
          </div>
        </div>

        <!-- Finish Button -->
        <button
          @click="showConfirmFinish = true"
          :disabled="isSubmitting"
          class="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-medium transition-colors cursor-pointer disabled:opacity-50 shrink-0"
        >
          {{ isSubmitting ? 'Submitting…' : 'Submit Exam' }}
        </button>
      </div>

      <!-- Progress Bar -->
      <div class="h-1 bg-slate-800 shrink-0">
        <div
          class="h-full bg-indigo-600 transition-all duration-300"
          :style="{ width: `${(answeredCount / questions.length) * 100}%` }"
        ></div>
      </div>

      <!-- ── Main Content ────────────────────────────────────────────────────── -->
      <div class="flex-1 flex overflow-hidden">

        <!-- Question Navigator Sidebar -->
        <aside class="w-[180px] shrink-0 bg-slate-900 border-r border-slate-800 p-3 overflow-y-auto hidden md:block">
          <div class="text-xs uppercase tracking-widest text-slate-500 font-semibold mb-3">Questions</div>
          <div class="grid grid-cols-5 gap-1.5">
            <button
              v-for="(q, i) in questions"
              :key="q._id"
              @click="goToQuestion(i)"
              :class="[
                'w-8 h-8 rounded-lg text-xs font-bold transition-all duration-150 cursor-pointer',
                i === currentIdx
                  ? 'bg-indigo-600 text-white ring-2 ring-indigo-400 ring-offset-1 ring-offset-slate-900'
                  : userAnswers[q._id]
                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                    : 'bg-slate-800 text-slate-400 hover:bg-slate-700 border border-slate-700',
              ]"
            >
              {{ i + 1 }}
            </button>
          </div>
          <div class="mt-4 space-y-1.5">
            <div class="flex items-center gap-2 text-xs text-slate-500">
              <span class="w-3 h-3 rounded-sm bg-emerald-500/20 border border-emerald-500/40 inline-block"></span>
              Answered
            </div>
            <div class="flex items-center gap-2 text-xs text-slate-500">
              <span class="w-3 h-3 rounded-sm bg-slate-800 border border-slate-700 inline-block"></span>
              Unanswered
            </div>
            <div class="flex items-center gap-2 text-xs text-slate-500">
              <span class="w-3 h-3 rounded-sm bg-indigo-600 inline-block"></span>
              Current
            </div>
          </div>
        </aside>

        <!-- Question Area -->
        <main class="flex-1 overflow-y-auto p-4 md:p-8">
          <div class="max-w-3xl mx-auto">

            <!-- Question Number Badge -->
            <div class="flex items-center gap-2 mb-4">
              <span class="text-xs uppercase tracking-widest text-indigo-400 font-semibold">
                Question {{ currentIdx + 1 }} of {{ questions.length }}
              </span>
              <span class="text-xs text-slate-600">·</span>
              <span class="text-xs text-slate-500 capitalize">{{ currentQuestion?.type?.replace('-', ' ') }}</span>
            </div>

            <!-- Reading Passage (if present) -->
            <div
              v-if="currentQuestion?.passage"
              class="mb-5 bg-slate-800/60 border border-slate-700 rounded-xl p-5 text-slate-300 text-sm leading-relaxed"
            >
              <div class="text-xs text-slate-500 uppercase tracking-wider mb-2 font-semibold">Reading Passage</div>
              {{ currentQuestion.passage }}
            </div>

            <!-- Question Text -->
            <div class="text-lg md:text-xl font-medium text-slate-100 mb-6 leading-relaxed">
              {{ currentQuestion?.questionText }}
            </div>

            <!-- Options -->
            <div class="space-y-3">
              <button
                v-for="(option, oi) in currentQuestion?.options"
                :key="oi"
                @click="selectAnswer(OPTION_KEYS[oi])"
                :class="[
                  'w-full text-left flex items-start gap-4 p-4 rounded-xl border transition-all duration-150 cursor-pointer group',
                  userAnswers[currentQuestion?._id || ''] === OPTION_KEYS[oi]
                    ? 'bg-indigo-600/20 border-indigo-500 text-indigo-100 shadow-lg shadow-indigo-500/10'
                    : 'bg-slate-800/50 border-slate-700 text-slate-300 hover:bg-slate-700 hover:border-slate-500 hover:text-slate-100',
                ]"
              >
                <span
                  :class="[
                    'shrink-0 w-7 h-7 rounded-lg flex items-center justify-center text-sm font-bold transition-colors',
                    userAnswers[currentQuestion?._id || ''] === OPTION_KEYS[oi]
                      ? 'bg-indigo-500 text-white'
                      : 'bg-slate-700 text-slate-400 group-hover:bg-slate-600',
                  ]"
                >
                  {{ OPTION_KEYS[oi] }}
                </span>
                <span class="text-sm md:text-base leading-relaxed pt-0.5">{{ option }}</span>
              </button>
            </div>

            <!-- Navigation Buttons -->
            <div class="flex justify-between mt-8 pt-4 border-t border-slate-800">
              <button
                v-if="currentIdx > 0"
                @click="goToQuestion(currentIdx - 1)"
                class="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-sm transition-colors cursor-pointer flex items-center gap-2"
              >
                ← Previous
              </button>
              <div v-else></div>
              <button
                v-if="currentIdx < questions.length - 1"
                @click="goToQuestion(currentIdx + 1)"
                class="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-sm transition-colors cursor-pointer flex items-center gap-2"
              >
                Next →
              </button>
              <button
                v-else
                @click="showConfirmFinish = true"
                class="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-medium transition-colors cursor-pointer"
              >
                Finish Exam →
              </button>
            </div>

            <!-- Keyboard Hint -->
            <div class="mt-6 text-center text-xs text-slate-600">
              Press <kbd class="px-1.5 py-0.5 bg-slate-800 rounded text-slate-500 font-mono">A</kbd>
              <kbd class="px-1.5 py-0.5 bg-slate-800 rounded text-slate-500 font-mono ml-1">B</kbd>
              <kbd class="px-1.5 py-0.5 bg-slate-800 rounded text-slate-500 font-mono ml-1">C</kbd>
              <kbd class="px-1.5 py-0.5 bg-slate-800 rounded text-slate-500 font-mono ml-1">D</kbd>
              to answer &middot;
              <kbd class="px-1.5 py-0.5 bg-slate-800 rounded text-slate-500 font-mono ml-1">← →</kbd> to navigate
            </div>
          </div>
        </main>
      </div>
    </template>

    <!-- ── Confirm Finish Dialog ─────────────────────────────────────────────── -->
    <Transition name="fade">
      <div
        v-if="showConfirmFinish"
        class="absolute inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4"
        @click.self="showConfirmFinish = false"
      >
        <div class="bg-slate-800 border border-slate-700 rounded-2xl p-6 max-w-sm w-full shadow-2xl">
          <div class="text-3xl text-center mb-3">🏁</div>
          <h3 class="text-xl font-bold text-center mb-1">Submit Exam?</h3>
          <p class="text-slate-400 text-sm text-center mb-2">
            You've answered <strong class="text-slate-200">{{ answeredCount }}</strong> of
            <strong class="text-slate-200">{{ questions.length }}</strong> questions.
          </p>
          <p v-if="answeredCount < questions.length" class="text-yellow-400 text-xs text-center mb-4">
            ⚠️ {{ questions.length - answeredCount }} question(s) left unanswered.
          </p>
          <div class="flex gap-3 mt-4">
            <button
              @click="showConfirmFinish = false"
              class="flex-1 px-4 py-2.5 bg-slate-700 hover:bg-slate-600 rounded-xl transition-colors cursor-pointer text-sm"
            >
              Keep Going
            </button>
            <button
              @click="finishExam('completed')"
              :disabled="isSubmitting"
              class="flex-1 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl font-semibold transition-colors cursor-pointer text-sm disabled:opacity-50"
            >
              {{ isSubmitting ? 'Submitting…' : 'Yes, Submit' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
