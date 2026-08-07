<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';
import { apiFetch } from '@/utils/api';
import PixelFrame from '@/shared/components/PixelFrame.vue';
import AppButton from '@/shared/components/AppButton.vue';

/**
 * `GET /api/exams/sessions/:id/details` returns four sibling keys — it does NOT
 * return a flat session carrying `answers`/`questionsMap`/an embedded template,
 * which is what this view previously (incorrectly) assumed. See
 * `SessionDetailsResponse` in `backend/app/schemas/exam.py`.
 */
interface QuestionData {
  id: string;
  questionText: string;
  passage?: string;
  options: string[];
  correctAnswer: string;
  explanation?: string;
  difficulty: string;
  tags?: string[] | null;
}

interface UserAnswer {
  userAnswer: string;
  isCorrect: boolean;
  timeTakenSeconds: number;
}

interface SessionDetails {
  session: {
    id: string;
    score: number;
    correctCount: number;
    totalCount: number;
    timeLimitMinutes: number;
    startedAt: string;
    finishedAt?: string;
    status: string;
  };
  template: {
    id: string;
    name: string;
    examType: string;
    passingScore: number;
  };
  questions: QuestionData[];
  userAnswers: Record<string, UserAnswer>;
}

const props = defineProps<{ sessionId: string }>();

const { t } = useI18n();
const router = useRouter();

const details = ref<SessionDetails | null>(null);
const isLoading = ref(true);
const expandedIdx = ref<number | null>(null);

/**
 * The review list is driven by the question list (so unanswered questions still
 * appear, in exam order) with each question's answer record joined in.
 */
const reviewRows = computed(() =>
  (details.value?.questions ?? []).map((question) => {
    const answer = details.value?.userAnswers[question.id];
    return {
      question,
      userAnswer: answer?.userAnswer ?? '',
      isCorrect: answer?.isCorrect ?? false,
      timeTakenSeconds: answer?.timeTakenSeconds ?? 0,
    };
  }),
);

const EXAM_CONFIG: Record<string, { flag: string }> = {
  toeic: { flag: '🇺🇸' },
  ielts: { flag: '🇬🇧' },
  hsk: { flag: '🇨🇳' },
  jlpt: { flag: '🇯🇵' },
  custom: { flag: '⚙️' },
};

const OPTION_KEYS = ['A', 'B', 'C', 'D'];

/** Tags with fewer than this many questions are too noisy to report — a lone
 *  miss would read as a categorical "0%" weakness. */
const MIN_TAG_SAMPLE = 2;

/**
 * Correctness per question tag, worst ratio first.
 *
 * Sorted by weakness rather than alphabetically because the point of the
 * breakdown is to show what to revise next. Computed entirely client-side —
 * the tags are already on the wire.
 */
const tagBreakdown = computed(() => {
  const totals = new Map<string, { correct: number; total: number }>();

  for (const row of reviewRows.value) {
    for (const tag of row.question.tags ?? []) {
      const entry = totals.get(tag) ?? { correct: 0, total: 0 };
      entry.total += 1;
      if (row.isCorrect) entry.correct += 1;
      totals.set(tag, entry);
    }
  }

  return [...totals.entries()]
    .filter(([, { total }]) => total >= MIN_TAG_SAMPLE)
    .map(([tag, { correct, total }]) => ({
      tag,
      correct,
      total,
      percent: Math.round((correct / total) * 100),
    }))
    .sort((a, b) => a.percent - b.percent || b.total - a.total);
});

const passed = computed(() =>
  details.value
    ? details.value.session.score >= (details.value.template?.passingScore ?? 60)
    : false,
);

const timeTaken = computed(() => {
  const s = details.value?.session;
  if (!s?.startedAt || !s?.finishedAt) return '—';
  const ms = new Date(s.finishedAt).getTime() - new Date(s.startedAt).getTime();
  const m = Math.floor(ms / 60000);
  const sec = Math.floor((ms % 60000) / 1000);
  return `${m}m ${sec}s`;
});

const scoreTier = computed(() => {
  const s = details.value?.session.score ?? 0;
  if (s >= 80) return 'good';
  if (s >= 60) return 'mid';
  return 'bad';
});

const circumference = 2 * Math.PI * 52; // radius 52 SVG circle

const strokeDashoffset = computed(() => {
  const score = details.value?.session.score ?? 0;
  return circumference - (score / 100) * circumference;
});

const fetchResults = async () => {
  isLoading.value = true;
  try {
    const res = await apiFetch(`/api/exams/sessions/${props.sessionId}/details`);
    if (!res.ok) throw new Error('Request failed');
    details.value = (await res.json()) as SessionDetails;
  } catch (err) {
    console.error('Failed to load results:', err);
  } finally {
    isLoading.value = false;
  }
};

const backToExams = () => router.push({ name: 'exams' });
const retake = () => {
  const templateId = details.value?.template.id;
  if (templateId) router.push({ name: 'exam-session', params: { templateId } });
};

onMounted(fetchResults);
</script>

<template>
  <div class="results-screen">
    <!-- Loading -->
    <div v-if="isLoading" class="results-loading">
      <div class="loading-icon" aria-hidden="true">⏳</div>
      <p class="font-label">{{ t('results.loading') }}</p>
    </div>

    <template v-else-if="details">
      <!-- ── Hero Score Section ──────────────────────────────────────────────── -->
      <div class="hero">
        <!-- Circular Score Gauge -->
        <div class="hero-gauge">
          <svg width="140" height="140" class="gauge-svg">
            <circle cx="70" cy="70" r="52" fill="none" stroke-width="10" class="gauge-track" />
            <circle
              cx="70"
              cy="70"
              r="52"
              fill="none"
              stroke-width="10"
              stroke-linecap="round"
              :stroke-dasharray="circumference"
              :stroke-dashoffset="strokeDashoffset"
              :class="['gauge-fill', passed ? 'gauge-fill--pass' : 'gauge-fill--fail']"
            />
          </svg>
          <div class="gauge-center">
            <span class="gauge-score font-label" :class="`gauge-score--${scoreTier}`">
              {{ Math.round(details.session.score) }}%
            </span>
            <span class="gauge-label font-label">{{ t('results.score') }}</span>
          </div>
        </div>

        <!-- Summary Text -->
        <div class="hero-summary">
          <div class="hero-title-row">
            <span class="hero-flag" aria-hidden="true">{{
              EXAM_CONFIG[details.template?.examType]?.flag || '📝'
            }}</span>
            <h1 class="hero-title font-body">{{ details.template?.name }}</h1>
          </div>
          <div
            class="pass-badge font-label"
            :class="passed ? 'pass-badge--pass' : 'pass-badge--fail'"
          >
            {{ passed ? t('results.passed') : t('results.notPassed') }}
            <span class="pass-badge-sub">
              {{ t('results.passThreshold', { score: details.template?.passingScore }) }}
            </span>
          </div>
          <div class="hero-stats">
            <PixelFrame frame-color="amber" surface="cabinet" :ring-width="3">
              <div class="hero-stat">
                <span class="hero-stat-value font-label">
                  {{ details.session.correctCount }}/{{ details.session.totalCount }}
                </span>
                <span class="hero-stat-label font-label">{{ t('results.correct') }}</span>
              </div>
            </PixelFrame>
            <PixelFrame frame-color="amber" surface="cabinet" :ring-width="3">
              <div class="hero-stat">
                <span class="hero-stat-value font-label">{{ timeTaken }}</span>
                <span class="hero-stat-label font-label">{{ t('results.timeTaken') }}</span>
              </div>
            </PixelFrame>
            <PixelFrame frame-color="amber" surface="cabinet" :ring-width="3">
              <div class="hero-stat">
                <span class="hero-stat-value font-label">
                  {{ details.session.timeLimitMinutes }} {{ t('common.minutes') }}
                </span>
                <span class="hero-stat-label font-label">{{ t('results.timeLimit') }}</span>
              </div>
            </PixelFrame>
          </div>
        </div>
      </div>

      <!-- ── Action Buttons ─────────────────────────────────────────────────── -->
      <div class="actions-row">
        <AppButton variant="secondary" @click="backToExams">{{
          t('results.backToExams')
        }}</AppButton>
        <AppButton variant="primary" @click="retake">{{ t('results.retake') }}</AppButton>
      </div>

      <!-- ── Question Review ─────────────────────────────────────────────────── -->
      <div class="review">
        <template v-if="tagBreakdown.length">
          <h2 class="review-title font-body">{{ t('results.byCategory') }}</h2>
          <ul class="tag-breakdown">
            <li v-for="entry in tagBreakdown" :key="entry.tag" class="tag-row">
              <span class="tag-name font-body">{{ entry.tag }}</span>
              <span class="tag-track">
                <span
                  class="tag-fill"
                  :class="{
                    'tag-fill--good': entry.percent >= 80,
                    'tag-fill--mid': entry.percent >= 50 && entry.percent < 80,
                    'tag-fill--bad': entry.percent < 50,
                  }"
                  :style="{ width: `${entry.percent}%` }"
                />
              </span>
              <span class="tag-score font-label">{{ entry.correct }}/{{ entry.total }}</span>
            </li>
          </ul>
        </template>

        <h2 class="review-title font-body">{{ t('results.review') }}</h2>

        <div class="review-list">
          <div
            v-for="(row, idx) in reviewRows"
            :key="row.question.id"
            class="review-row"
            :class="row.isCorrect ? 'review-row--correct' : 'review-row--incorrect'"
          >
            <!-- Question Header (always visible) -->
            <button
              type="button"
              class="review-header"
              @click="expandedIdx = expandedIdx === idx ? null : idx"
            >
              <span
                class="review-mark font-pixel"
                :class="row.isCorrect ? 'review-mark--correct' : 'review-mark--incorrect'"
              >
                {{ row.isCorrect ? '✓' : '✗' }}
              </span>
              <span class="review-body">
                <span class="review-question font-body">
                  Q{{ idx + 1 }}. {{ row.question.questionText || t('results.questionNotFound') }}
                </span>
                <span class="review-meta font-label">
                  <span>
                    {{ t('results.yourAnswer') }}
                    <strong :class="row.isCorrect ? 'text-correct' : 'text-incorrect'">{{
                      row.userAnswer || '—'
                    }}</strong>
                  </span>
                  <span v-if="!row.isCorrect">
                    {{ t('results.correctAnswer') }}
                    <strong class="text-correct">{{ row.question.correctAnswer }}</strong>
                  </span>
                  <span>⏱ {{ row.timeTakenSeconds }}S</span>
                </span>
              </span>
              <span class="review-chevron font-label" aria-hidden="true">{{
                expandedIdx === idx ? '▲' : '▼'
              }}</span>
            </button>

            <!-- Expanded Detail -->
            <Transition name="slide">
              <div v-if="expandedIdx === idx" class="review-detail">
                <!-- Passage if present -->
                <div v-if="row.question.passage" class="review-passage font-body">
                  <div class="review-passage-label font-label">{{ t('results.passage') }}</div>
                  {{ row.question.passage }}
                </div>

                <!-- Options -->
                <div class="review-options">
                  <div
                    v-for="(option, oi) in row.question.options"
                    :key="oi"
                    class="review-option font-body"
                    :class="{
                      'review-option--correct': OPTION_KEYS[oi] === row.question.correctAnswer,
                      'review-option--wrong': OPTION_KEYS[oi] === row.userAnswer && !row.isCorrect,
                    }"
                  >
                    <span class="review-option-key font-label">{{ OPTION_KEYS[oi] }}</span>
                    <span class="review-option-text">{{ option }}</span>
                    <span
                      v-if="OPTION_KEYS[oi] === row.question.correctAnswer"
                      class="review-option-tag text-correct font-label"
                      >{{ t('results.correctTag') }}</span
                    >
                    <span
                      v-else-if="OPTION_KEYS[oi] === row.userAnswer && !row.isCorrect"
                      class="review-option-tag text-incorrect font-label"
                      >{{ t('results.yourAnswerTag') }}</span
                    >
                  </div>
                </div>

                <!-- Explanation -->
                <div v-if="row.question.explanation" class="review-explanation">
                  <div class="review-explanation-label font-label">
                    {{ t('results.explanation') }}
                  </div>
                  <p class="review-explanation-text font-body">{{ row.question.explanation }}</p>
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
  gap: var(--space-6);
  color: var(--text-secondary);
}
.loading-icon {
  font-size: var(--font-size-display);
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
  border-bottom: var(--space-1) solid var(--surface-panel-border);
  /* stylelint-disable-next-line scale-unlimited/declaration-strict-value -- approved Step 2 - layout one-off, see design-tokens.json notes */
  padding: 36px var(--space-10);
  display: flex;
  flex-wrap: wrap;
  /* stylelint-disable-next-line scale-unlimited/declaration-strict-value -- approved Step 2 - layout one-off, see design-tokens.json notes */
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
  /* stylelint-disable-next-line scale-unlimited/declaration-strict-value -- isolated layout value, not part of the type scale */
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
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
  margin-top: var(--space-1);
}

.hero-summary {
  flex: 1;
  min-width: 260px;
}
.hero-title-row {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  margin-bottom: var(--space-4);
}
.hero-flag {
  font-size: var(--font-size-2xl);
}
.hero-title {
  font-size: var(--font-size-xl);
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}
.pass-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--space-4);
  font-size: var(--font-size-base);
  font-weight: 700;
  padding: var(--space-3) var(--space-7);
  border: var(--space-1) solid;
  margin-bottom: var(--space-8);
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
  font-size: var(--font-size-xs);
  font-weight: 400;
  opacity: 0.8;
}

.hero-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-5);
}
.hero-stat {
  padding: var(--space-6);
  text-align: center;
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}
.hero-stat-value {
  font-size: var(--font-size-lg);
  font-weight: 700;
  color: var(--text-primary);
}
.hero-stat-label {
  font-size: var(--font-size-2xs);
  color: var(--text-secondary);
  letter-spacing: var(--tracking-normal);
}

.actions-row {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-6);
  padding: var(--space-8) var(--space-10);
  border-bottom: var(--space-1) solid var(--surface-panel-border);
  max-width: 900px;
  margin: 0 auto;
  width: 100%;
}
.review {
  max-width: 900px;
  margin: 0 auto;
  width: 100%;
  padding: var(--space-10);
  flex: 1;
}
.review-title {
  font-size: var(--font-size-lg);
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 var(--space-8);
}
.tag-breakdown {
  list-style: none;
  margin: 0 0 var(--space-11);
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}
.tag-row {
  display: flex;
  align-items: center;
  gap: var(--space-6);
}
.tag-name {
  flex: 0 0 160px;
  font-size: var(--font-size-md);
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.tag-track {
  flex: 1;
  height: 10px;
  background: var(--surface-page);
}
.tag-fill {
  display: block;
  height: 100%;
}
.tag-fill--good {
  background: var(--status-success);
}
.tag-fill--mid {
  background: var(--status-caution);
}
.tag-fill--bad {
  background: var(--status-danger);
}
.tag-score {
  flex: 0 0 48px;
  text-align: right;
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}
.review-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}
.review-row {
  background: var(--surface-panel);
  border-left: var(--border-width-accent) solid var(--surface-panel-border);
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
  gap: var(--space-6);
  padding: var(--space-7) var(--space-8);
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
  font-size: var(--font-size-xs);
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
  gap: var(--space-3);
}
.review-question {
  font-size: var(--font-size-md);
  color: var(--text-primary);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.review-meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-6);
  font-size: var(--font-size-xs);
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
  font-size: var(--font-size-xs);
  margin-top: var(--space-1);
}

.review-detail {
  border-top: var(--space-1) solid var(--surface-panel-border);
  padding: var(--space-8) var(--space-9);
  background: var(--surface-page);
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}
.review-passage {
  background: var(--surface-panel);
  border: var(--space-1) solid var(--surface-panel-border);
  padding: var(--space-6);
  color: var(--text-secondary);
  font-size: var(--font-size-base);
  line-height: 1.6;
}
.review-passage-label {
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
  letter-spacing: var(--tracking-normal);
  margin-bottom: var(--space-3);
}
.review-options {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}
.review-option {
  display: flex;
  align-items: center;
  gap: var(--space-5);
  padding: var(--space-4) var(--space-6);
  border: var(--space-1) solid var(--surface-panel-border);
  color: var(--text-secondary);
  font-size: var(--font-size-md);
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
  font-size: var(--font-size-xs);
  font-weight: 700;
  flex-shrink: 0;
}

.review-explanation {
  background: var(--amber-dim);
  border: var(--space-1) solid var(--amber);
  padding: var(--space-6);
}
.review-explanation-label {
  font-size: var(--font-size-xs);
  font-weight: 700;
  color: var(--text-label-accent);
  letter-spacing: var(--tracking-normal);
  margin-bottom: var(--space-3);
}
.review-explanation-text {
  color: var(--text-primary);
  font-size: var(--font-size-md);
  line-height: 1.6;
  margin: 0;
}

.slide-enter-active,
.slide-leave-active {
  transition:
    max-height 0.25s ease,
    opacity 0.2s ease;
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

.review-header:focus-visible {
  outline: var(--focus-ring-width) solid var(--color-focus-ring);
  outline-offset: 2px;
}
</style>
