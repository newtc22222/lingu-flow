<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { apiFetch } from '../utils/api';

interface QuestionData {
  _id: string;
  questionText: string;
  passage?: string;
  options: string[];
  correctAnswer: string;
  explanation?: string;
  difficulty: string;
}

interface AnswerRecord {
  questionId: string;
  userAnswer: string;
  isCorrect: boolean;
  timeTaken: number;
}

interface SessionDetails {
  _id: string;
  score: number;
  correctCount: number;
  totalCount: number;
  timeLimit: number;
  startedAt: string;
  finishedAt?: string;
  status: string;
  answers: AnswerRecord[];
  questionsMap: Record<string, QuestionData>;
  examTemplateId: {
    name: string;
    examType: string;
    passingScore: number;
  };
}

const props = defineProps<{ sessionId: string }>();
const emit = defineEmits<{
  (e: 'back'): void;
  (e: 'retake', templateId: string): void;
}>();

const session = ref<SessionDetails | null>(null);
const isLoading = ref(true);
const expandedIdx = ref<number | null>(null);

const EXAM_CONFIG: Record<string, { gradient: string; flag: string }> = {
  toeic: { gradient: 'from-blue-600 to-cyan-500', flag: '🇺🇸' },
  ielts: { gradient: 'from-red-600 to-orange-500', flag: '🇬🇧' },
  hsk: { gradient: 'from-rose-600 to-pink-500', flag: '🇨🇳' },
  jlpt: { gradient: 'from-purple-600 to-violet-500', flag: '🇯🇵' },
  custom: { gradient: 'from-emerald-600 to-teal-500', flag: '⚙️' },
};

const OPTION_KEYS = ['A', 'B', 'C', 'D'];

const passed = computed(() =>
  session.value ? session.value.score >= (session.value.examTemplateId?.passingScore ?? 60) : false,
);

const timeTaken = computed(() => {
  if (!session.value?.startedAt || !session.value?.finishedAt) return '—';
  const ms = new Date(session.value.finishedAt).getTime() - new Date(session.value.startedAt).getTime();
  const m = Math.floor(ms / 60000);
  const s = Math.floor((ms % 60000) / 1000);
  return `${m}m ${s}s`;
});

const scoreColor = computed(() => {
  if (!session.value) return 'text-slate-400';
  const s = session.value.score;
  if (s >= 80) return 'text-emerald-400';
  if (s >= 60) return 'text-yellow-400';
  return 'text-rose-400';
});

const circumference = 2 * Math.PI * 52; // radius 52 SVG circle

const strokeDashoffset = computed(() => {
  const score = session.value?.score ?? 0;
  return circumference - (score / 100) * circumference;
});

const fetchResults = async () => {
  isLoading.value = true;
  try {
    const res = await apiFetch(`/api/exams/sessions/${props.sessionId}/details`);
    session.value = await res.json();
  } catch (err) {
    console.error('Failed to load results:', err);
  } finally {
    isLoading.value = false;
  }
};

onMounted(fetchResults);
</script>

<template>
  <div class="flex flex-col h-full bg-slate-900 text-slate-100 overflow-y-auto">

    <!-- Loading -->
    <div v-if="isLoading" class="flex-1 flex items-center justify-center">
      <div class="text-center">
        <div class="text-5xl mb-4 animate-spin">⏳</div>
        <p class="text-slate-400 animate-pulse">Loading results...</p>
      </div>
    </div>

    <template v-else-if="session">
      <!-- ── Hero Score Section ──────────────────────────────────────────────── -->
      <div
        class="relative overflow-hidden bg-gradient-to-br from-slate-800 to-slate-900 border-b border-slate-700/60 px-6 py-10"
      >
        <div
          :class="[
            'absolute inset-0 opacity-10 bg-gradient-to-br',
            passed ? 'from-emerald-500 to-teal-500' : 'from-rose-500 to-orange-500',
          ]"
        ></div>
        <div class="relative max-w-4xl mx-auto flex flex-col md:flex-row items-center gap-8">

          <!-- Circular Score Gauge -->
          <div class="relative shrink-0">
            <svg width="140" height="140" class="-rotate-90">
              <circle cx="70" cy="70" r="52" fill="none" stroke="rgba(255,255,255,0.08)" stroke-width="10" />
              <circle
                cx="70" cy="70" r="52" fill="none"
                :stroke="passed ? '#10b981' : '#f43f5e'"
                stroke-width="10"
                stroke-linecap="round"
                :stroke-dasharray="circumference"
                :stroke-dashoffset="strokeDashoffset"
                class="transition-all duration-1000 ease-out"
              />
            </svg>
            <div class="absolute inset-0 flex flex-col items-center justify-center">
              <span :class="['text-3xl font-bold', scoreColor]">{{ session.score }}%</span>
              <span class="text-xs text-slate-400 mt-0.5">Score</span>
            </div>
          </div>

          <!-- Summary Text -->
          <div class="flex-1 text-center md:text-left">
            <div class="flex items-center gap-2 justify-center md:justify-start mb-1">
              <span class="text-2xl">{{ EXAM_CONFIG[session.examTemplateId?.examType]?.flag || '📝' }}</span>
              <h1 class="text-2xl font-bold text-slate-100">{{ session.examTemplateId?.name }}</h1>
            </div>
            <div
              :class="[
                'inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-sm font-semibold mt-1 mb-4',
                passed
                  ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                  : 'bg-rose-500/20 text-rose-400 border border-rose-500/30',
              ]"
            >
              {{ passed ? '🎉 PASSED' : '❌ NOT PASSED' }}
              <span class="text-xs opacity-70">(Pass: {{ session.examTemplateId?.passingScore }}%)</span>
            </div>
            <div class="grid grid-cols-3 gap-4 mt-2">
              <div class="bg-slate-700/40 rounded-xl p-3 text-center border border-slate-600/30">
                <div class="text-xl font-bold text-slate-100">{{ session.correctCount }}/{{ session.totalCount }}</div>
                <div class="text-xs text-slate-400">Correct</div>
              </div>
              <div class="bg-slate-700/40 rounded-xl p-3 text-center border border-slate-600/30">
                <div class="text-xl font-bold text-slate-100">{{ timeTaken }}</div>
                <div class="text-xs text-slate-400">Time Taken</div>
              </div>
              <div class="bg-slate-700/40 rounded-xl p-3 text-center border border-slate-600/30">
                <div class="text-xl font-bold text-slate-100">{{ session.timeLimit }} min</div>
                <div class="text-xs text-slate-400">Time Limit</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ── Action Buttons ─────────────────────────────────────────────────── -->
      <div class="px-6 py-4 flex gap-3 justify-end border-b border-slate-800 max-w-4xl mx-auto w-full">
        <button
          @click="emit('back')"
          class="px-5 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 rounded-xl transition-colors cursor-pointer text-sm font-medium"
        >
          ← Back to Exams
        </button>
      </div>

      <!-- ── Question Review ─────────────────────────────────────────────────── -->
      <div class="flex-1 max-w-4xl mx-auto w-full px-6 py-6">
        <h2 class="text-lg font-semibold text-slate-200 mb-4 flex items-center gap-2">
          <span>🔍</span> Question Review
        </h2>

        <div class="space-y-3">
          <div
            v-for="(record, idx) in session.answers"
            :key="record.questionId"
            class="bg-slate-800 rounded-xl border overflow-hidden transition-all duration-200"
            :class="record.isCorrect ? 'border-emerald-500/30' : 'border-rose-500/30'"
          >
            <!-- Question Header (always visible) -->
            <div
              class="flex items-start gap-3 p-4 cursor-pointer hover:bg-slate-700/30 transition-colors"
              @click="expandedIdx = expandedIdx === idx ? null : idx"
            >
              <div
                :class="[
                  'shrink-0 w-7 h-7 rounded-full flex items-center justify-center text-sm font-bold mt-0.5',
                  record.isCorrect
                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                    : 'bg-rose-500/20 text-rose-400 border border-rose-500/40',
                ]"
              >
                {{ record.isCorrect ? '✓' : '✗' }}
              </div>
              <div class="flex-1 min-w-0">
                <div class="text-sm font-medium text-slate-300 line-clamp-2">
                  Q{{ idx + 1 }}. {{ session.questionsMap[record.questionId]?.questionText || 'Question not found' }}
                </div>
                <div class="flex items-center gap-3 mt-1 text-xs text-slate-500">
                  <span>Your answer: <strong :class="record.isCorrect ? 'text-emerald-400' : 'text-rose-400'">{{ record.userAnswer || '—' }}</strong></span>
                  <span v-if="!record.isCorrect">Correct: <strong class="text-emerald-400">{{ session.questionsMap[record.questionId]?.correctAnswer }}</strong></span>
                  <span>⏱ {{ record.timeTaken }}s</span>
                </div>
              </div>
              <span class="text-slate-500 text-xs mt-1 shrink-0">{{ expandedIdx === idx ? '▲' : '▼' }}</span>
            </div>

            <!-- Expanded Detail -->
            <Transition name="slide">
              <div
                v-if="expandedIdx === idx"
                class="border-t border-slate-700/50 px-5 py-4 bg-slate-900/50 text-sm space-y-3"
              >
                <!-- Passage if present -->
                <div
                  v-if="session.questionsMap[record.questionId]?.passage"
                  class="bg-slate-800 border border-slate-700 rounded-lg p-3 text-slate-400 text-xs leading-relaxed"
                >
                  <div class="text-xs text-slate-500 uppercase tracking-wider mb-1">Passage</div>
                  {{ session.questionsMap[record.questionId].passage }}
                </div>

                <!-- Options -->
                <div class="space-y-2">
                  <div
                    v-for="(option, oi) in session.questionsMap[record.questionId]?.options"
                    :key="oi"
                    :class="[
                      'flex items-center gap-3 px-3 py-2 rounded-lg border text-sm',
                      OPTION_KEYS[oi] === session.questionsMap[record.questionId]?.correctAnswer
                        ? 'bg-emerald-500/10 border-emerald-500/40 text-emerald-300'
                        : OPTION_KEYS[oi] === record.userAnswer && !record.isCorrect
                          ? 'bg-rose-500/10 border-rose-500/40 text-rose-300'
                          : 'border-slate-700 text-slate-400',
                    ]"
                  >
                    <span class="font-bold w-5 shrink-0">{{ OPTION_KEYS[oi] }}</span>
                    <span>{{ option }}</span>
                    <span
                      v-if="OPTION_KEYS[oi] === session.questionsMap[record.questionId]?.correctAnswer"
                      class="ml-auto text-emerald-400 text-xs font-semibold"
                    >✓ Correct</span>
                    <span
                      v-else-if="OPTION_KEYS[oi] === record.userAnswer && !record.isCorrect"
                      class="ml-auto text-rose-400 text-xs font-semibold"
                    >Your answer</span>
                  </div>
                </div>

                <!-- Explanation -->
                <div
                  v-if="session.questionsMap[record.questionId]?.explanation"
                  class="bg-indigo-500/10 border border-indigo-500/30 rounded-lg p-3"
                >
                  <div class="text-xs text-indigo-400 uppercase tracking-wider font-semibold mb-1">💡 Explanation</div>
                  <p class="text-slate-300 text-sm leading-relaxed">
                    {{ session.questionsMap[record.questionId].explanation }}
                  </p>
                </div>
              </div>
            </Transition>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.slide-enter-active, .slide-leave-active {
  transition: max-height 0.25s ease, opacity 0.2s ease;
  max-height: 800px;
  overflow: hidden;
}
.slide-enter-from, .slide-leave-to {
  max-height: 0;
  opacity: 0;
}
</style>
