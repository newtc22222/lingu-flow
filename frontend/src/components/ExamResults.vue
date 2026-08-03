<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { apiFetch } from '../utils/api';
import PixelFrame from '../shared/components/PixelFrame.vue';

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

const EXAM_CONFIG: Record<string, { flag: string }> = {
  toeic: { flag: '🇺🇸' },
  ielts: { flag: '🇬🇧' },
  hsk: { flag: '🇨🇳' },
  jlpt: { flag: '🇯🇵' },
  custom: { flag: '⚙️' },
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

const scoreTier = computed(() => {
  const s = session.value?.score ?? 0;
  if (s >= 80) return 'good';
  if (s >= 60) return 'mid';
  return 'bad';
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
  <div class="results-screen">

    <!-- Loading -->
    <div v-if="isLoading" class="results-loading">
      <div class="loading-icon" aria-hidden="true">⏳</div>
      <p class="font-label">LOADING RESULTS…</p>
    </div>

    <template v-else-if="session">
      <!-- ── Hero Score Section ──────────────────────────────────────────────── -->
      <div class="hero">
        <!-- Circular Score Gauge -->
        <div class="hero-gauge">
          <svg width="140" height="140" class="gauge-svg">
            <circle cx="70" cy="70" r="52" fill="none" stroke-width="10" class="gauge-track" />
            <circle
              cx="70" cy="70" r="52" fill="none"
              stroke-width="10"
              stroke-linecap="round"
              :stroke-dasharray="circumference"
              :stroke-dashoffset="strokeDashoffset"
              :class="['gauge-fill', passed ? 'gauge-fill--pass' : 'gauge-fill--fail']"
            />
          </svg>
          <div class="gauge-center">
            <span class="gauge-score font-label" :class="`gauge-score--${scoreTier}`">{{ session.score }}%</span>
            <span class="gauge-label font-label">SCORE</span>
          </div>
        </div>

        <!-- Summary Text -->
        <div class="hero-summary">
          <div class="hero-title-row">
            <span class="hero-flag" aria-hidden="true">{{ EXAM_CONFIG[session.examTemplateId?.examType]?.flag || '📝' }}</span>
            <h1 class="hero-title font-body">{{ session.examTemplateId?.name }}</h1>
          </div>
          <div class="pass-badge font-label" :class="passed ? 'pass-badge--pass' : 'pass-badge--fail'">
            {{ passed ? '🎉 PASSED' : '❌ NOT PASSED' }}
            <span class="pass-badge-sub">(PASS: {{ session.examTemplateId?.passingScore }}%)</span>
          </div>
          <div class="hero-stats">
            <PixelFrame frame-color="amber" surface="cabinet" :ring-width="3">
              <div class="hero-stat">
                <span class="hero-stat-value font-label">{{ session.correctCount }}/{{ session.totalCount }}</span>
                <span class="hero-stat-label font-label">CORRECT</span>
              </div>
            </PixelFrame>
            <PixelFrame frame-color="amber" surface="cabinet" :ring-width="3">
              <div class="hero-stat">
                <span class="hero-stat-value font-label">{{ timeTaken }}</span>
                <span class="hero-stat-label font-label">TIME TAKEN</span>
              </div>
            </PixelFrame>
            <PixelFrame frame-color="amber" surface="cabinet" :ring-width="3">
              <div class="hero-stat">
                <span class="hero-stat-value font-label">{{ session.timeLimit }} MIN</span>
                <span class="hero-stat-label font-label">TIME LIMIT</span>
              </div>
            </PixelFrame>
          </div>
        </div>
      </div>

      <!-- ── Action Buttons ─────────────────────────────────────────────────── -->
      <div class="actions-row">
        <button type="button" class="btn-guest font-label" @click="emit('back')">← BACK TO EXAMS</button>
      </div>

      <!-- ── Question Review ─────────────────────────────────────────────────── -->
      <div class="review">
        <h2 class="review-title font-body">🔍 Question Review</h2>

        <div class="review-list">
          <div
            v-for="(record, idx) in session.answers"
            :key="record.questionId"
            class="review-row"
            :class="record.isCorrect ? 'review-row--correct' : 'review-row--incorrect'"
          >
            <!-- Question Header (always visible) -->
            <button type="button" class="review-header" @click="expandedIdx = expandedIdx === idx ? null : idx">
              <span class="review-mark font-pixel" :class="record.isCorrect ? 'review-mark--correct' : 'review-mark--incorrect'">
                {{ record.isCorrect ? '✓' : '✗' }}
              </span>
              <span class="review-body">
                <span class="review-question font-body">
                  Q{{ idx + 1 }}. {{ session.questionsMap[record.questionId]?.questionText || 'Question not found' }}
                </span>
                <span class="review-meta font-label">
                  <span>YOUR ANSWER: <strong :class="record.isCorrect ? 'text-correct' : 'text-incorrect'">{{ record.userAnswer || '—' }}</strong></span>
                  <span v-if="!record.isCorrect">CORRECT: <strong class="text-correct">{{ session.questionsMap[record.questionId]?.correctAnswer }}</strong></span>
                  <span>⏱ {{ record.timeTaken }}S</span>
                </span>
              </span>
              <span class="review-chevron font-label" aria-hidden="true">{{ expandedIdx === idx ? '▲' : '▼' }}</span>
            </button>

            <!-- Expanded Detail -->
            <Transition name="slide">
              <div v-if="expandedIdx === idx" class="review-detail">
                <!-- Passage if present -->
                <div v-if="session.questionsMap[record.questionId]?.passage" class="review-passage font-body">
                  <div class="review-passage-label font-label">PASSAGE</div>
                  {{ session.questionsMap[record.questionId].passage }}
                </div>

                <!-- Options -->
                <div class="review-options">
                  <div
                    v-for="(option, oi) in session.questionsMap[record.questionId]?.options"
                    :key="oi"
                    class="review-option font-body"
                    :class="{
                      'review-option--correct': OPTION_KEYS[oi] === session.questionsMap[record.questionId]?.correctAnswer,
                      'review-option--wrong': OPTION_KEYS[oi] === record.userAnswer && !record.isCorrect,
                    }"
                  >
                    <span class="review-option-key font-label">{{ OPTION_KEYS[oi] }}</span>
                    <span class="review-option-text">{{ option }}</span>
                    <span
                      v-if="OPTION_KEYS[oi] === session.questionsMap[record.questionId]?.correctAnswer"
                      class="review-option-tag text-correct font-label"
                    >✓ CORRECT</span>
                    <span
                      v-else-if="OPTION_KEYS[oi] === record.userAnswer && !record.isCorrect"
                      class="review-option-tag text-incorrect font-label"
                    >YOUR ANSWER</span>
                  </div>
                </div>

                <!-- Explanation -->
                <div v-if="session.questionsMap[record.questionId]?.explanation" class="review-explanation">
                  <div class="review-explanation-label font-label">💡 EXPLANATION</div>
                  <p class="review-explanation-text font-body">
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
.results-screen {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}
.results-loading {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--text-secondary);
}
.loading-icon {
  font-size: 44px;
  animation: results-spin 1.2s linear infinite;
}
@keyframes results-spin {
  to {
    transform: rotate(360deg);
  }
}
@media (prefers-reduced-motion: reduce) {
  .loading-icon {
    animation: none;
  }
}

.hero {
  background: var(--surface-panel);
  border-bottom: 2px solid var(--surface-panel-border);
  padding: 36px 24px;
  display: flex;
  flex-wrap: wrap;
  gap: 32px;
  align-items: center;
  justify-content: center;
  max-width: 900px;
  margin: 0 auto;
  width: 100%;
}
.hero-gauge {
  position: relative;
  flex-shrink: 0;
}
.gauge-svg {
  transform: rotate(-90deg);
}
.gauge-track {
  stroke: var(--surface-panel-border);
}
.gauge-fill {
  transition: stroke-dashoffset 1s ease-out;
}
@media (prefers-reduced-motion: reduce) {
  .gauge-fill {
    transition: none;
  }
}
.gauge-fill--pass {
  stroke: var(--status-success);
}
.gauge-fill--fail {
  stroke: var(--status-danger);
}
.gauge-center {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.gauge-score {
  font-size: 26px;
  font-weight: 700;
  color: var(--text-primary);
}
.gauge-score--good {
  color: var(--status-success);
}
.gauge-score--mid {
  color: var(--status-caution);
}
.gauge-score--bad {
  color: var(--status-danger);
}
.gauge-label {
  font-size: 10px;
  color: var(--text-secondary);
  margin-top: 2px;
}

.hero-summary {
  flex: 1;
  min-width: 260px;
}
.hero-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.hero-flag {
  font-size: 22px;
}
.hero-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}
.pass-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 700;
  padding: 6px 14px;
  border: 2px solid;
  margin-bottom: 16px;
}
.pass-badge--pass {
  color: var(--status-success);
  border-color: var(--status-success);
  background: var(--status-success-subtle);
}
.pass-badge--fail {
  color: var(--status-danger);
  border-color: var(--status-danger);
  background: var(--status-danger-subtle);
}
.pass-badge-sub {
  font-size: 10px;
  font-weight: 400;
  opacity: 0.8;
}

.hero-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}
.hero-stat {
  padding: 12px;
  text-align: center;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.hero-stat-value {
  font-size: 15px;
  font-weight: 700;
  color: var(--text-primary);
}
.hero-stat-label {
  font-size: 9px;
  color: var(--text-secondary);
  letter-spacing: 1px;
}

.actions-row {
  display: flex;
  justify-content: flex-end;
  padding: 16px 24px;
  border-bottom: 2px solid var(--surface-panel-border);
  max-width: 900px;
  margin: 0 auto;
  width: 100%;
}
.btn-guest {
  background: transparent;
  border: 2px solid var(--surface-panel-border);
  color: var(--text-secondary);
  padding: 10px 18px;
  font-size: 11px;
  letter-spacing: 1px;
  cursor: pointer;
}
.btn-guest:hover {
  border-color: var(--color-accent);
  color: var(--text-primary);
}

.review {
  max-width: 900px;
  margin: 0 auto;
  width: 100%;
  padding: 24px;
  flex: 1;
}
.review-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 16px;
}
.review-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.review-row {
  background: var(--surface-panel);
  border-left: 3px solid var(--surface-panel-border);
}
.review-row--correct {
  border-left-color: var(--status-success);
}
.review-row--incorrect {
  border-left-color: var(--status-danger);
}
.review-header {
  width: 100%;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px 16px;
  background: none;
  border: none;
  text-align: left;
  color: inherit;
  cursor: pointer;
}
.review-header:hover {
  background: var(--state-hover-surface);
}
.review-mark {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
}
.review-mark--correct {
  background: var(--status-success);
  color: var(--text-on-accent);
}
.review-mark--incorrect {
  background: var(--status-danger);
  color: var(--text-on-accent);
}
.review-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.review-question {
  font-size: 13px;
  color: var(--text-primary);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.review-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 10px;
  color: var(--text-secondary);
}
.text-correct {
  color: var(--status-success);
}
.text-incorrect {
  color: var(--status-danger);
}
.review-chevron {
  flex-shrink: 0;
  color: var(--text-secondary);
  font-size: 10px;
  margin-top: 2px;
}

.review-detail {
  border-top: 2px solid var(--surface-panel-border);
  padding: 16px 20px;
  background: var(--surface-page);
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.review-passage {
  background: var(--surface-panel);
  border: 2px solid var(--surface-panel-border);
  padding: 12px;
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 1.6;
}
.review-passage-label {
  font-size: 10px;
  color: var(--text-secondary);
  letter-spacing: 1px;
  margin-bottom: 6px;
}
.review-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.review-option {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  border: 2px solid var(--surface-panel-border);
  color: var(--text-secondary);
  font-size: 13px;
}
.review-option--correct {
  border-color: var(--status-success);
  background: var(--status-success-subtle);
  color: var(--text-primary);
}
.review-option--wrong {
  border-color: var(--status-danger);
  background: var(--status-danger-subtle);
  color: var(--text-primary);
}
.review-option-key {
  font-weight: 700;
  width: 18px;
  flex-shrink: 0;
}
.review-option-text {
  flex: 1;
}
.review-option-tag {
  margin-left: auto;
  font-size: 10px;
  font-weight: 700;
  flex-shrink: 0;
}

.review-explanation {
  background: var(--amber-dim);
  border: 2px solid var(--amber);
  padding: 12px;
}
.review-explanation-label {
  font-size: 10px;
  font-weight: 700;
  color: var(--text-label-accent);
  letter-spacing: 1px;
  margin-bottom: 6px;
}
.review-explanation-text {
  color: var(--text-primary);
  font-size: 13px;
  line-height: 1.6;
  margin: 0;
}

.slide-enter-active,
.slide-leave-active {
  transition: max-height 0.25s ease, opacity 0.2s ease;
  max-height: 800px;
  overflow: hidden;
}
.slide-enter-from,
.slide-leave-to {
  max-height: 0;
  opacity: 0;
}
@media (prefers-reduced-motion: reduce) {
  .slide-enter-active,
  .slide-leave-active {
    transition: none;
  }
}

.btn-guest:focus-visible,
.review-header:focus-visible {
  outline: 2px solid var(--color-focus-ring);
  outline-offset: 2px;
}
</style>
