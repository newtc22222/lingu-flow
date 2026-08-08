<script setup lang="ts">
/**
 * Exam lobby — full-bleed catalog + history console.
 * TAKE opens briefing (session route); does not start the clock here.
 */
import { ref, onMounted, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';
import { apiFetch } from '@/utils/api';
import AppButton from '@/shared/components/AppButton.vue';

interface ExamTemplate {
  id: string;
  name: string;
  examType: 'toeic' | 'ielts' | 'hsk' | 'jlpt' | 'custom';
  description: string;
  durationMinutes: number;
  totalQuestions: number;
  passingScore: number;
  level: string;
  isPublic: boolean;
  parts: string[];
}

interface ExamSession {
  id: string;
  examTemplateId: string;
  score: number;
  status: string;
  startedAt: string;
  correctCount: number;
  totalCount: number;
}

const { t } = useI18n();
const router = useRouter();

const templates = ref<ExamTemplate[]>([]);
const sessions = ref<ExamSession[]>([]);
const isLoading = ref(true);
const loadError = ref('');
const selectedType = ref<string>('all');
const selectedPart = ref<string>('all');

const templatesById = computed(() => new Map(templates.value.map((tpl) => [tpl.id, tpl])));

const TYPE_LABELS: Record<string, string> = {
  toeic: 'TOEIC',
  ielts: 'IELTS',
  hsk: 'HSK',
  jlpt: 'JLPT',
  custom: 'CUSTOM',
};

const typeFilters = computed(() => [
  { key: 'all', label: t('exam.allExams') },
  { key: 'toeic', label: 'TOEIC' },
  { key: 'ielts', label: 'IELTS' },
  { key: 'hsk', label: 'HSK' },
  { key: 'jlpt', label: 'JLPT' },
  { key: 'custom', label: t('exam.custom') },
]);

const availableParts = computed(() => {
  const scoped =
    selectedType.value === 'all'
      ? templates.value
      : templates.value.filter((tpl) => tpl.examType === selectedType.value);
  return [...new Set(scoped.flatMap((tpl) => tpl.parts ?? []))].sort();
});

const filteredTemplates = computed(() =>
  templates.value.filter((tpl) => {
    if (selectedType.value !== 'all' && tpl.examType !== selectedType.value) return false;
    if (selectedPart.value !== 'all' && !(tpl.parts ?? []).includes(selectedPart.value))
      return false;
    return true;
  }),
);

function selectType(key: string) {
  selectedType.value = key;
  if (!availableParts.value.includes(selectedPart.value)) selectedPart.value = 'all';
}

const stats = computed(() => {
  const completed = sessions.value.filter((s) => s.status === 'completed');
  const avgScore = completed.length
    ? Math.round(completed.reduce((sum, s) => sum + s.score, 0) / completed.length)
    : 0;
  const bestScore = completed.length ? Math.max(...completed.map((s) => s.score)) : 0;
  return { total: completed.length, avgScore, bestScore };
});

const recentSessions = computed(() => sessions.value.slice(0, 8));

const fetchData = async () => {
  isLoading.value = true;
  loadError.value = '';
  try {
    const [templatesRes, sessionsRes] = await Promise.all([
      apiFetch('/api/exams/templates'),
      apiFetch('/api/exams/sessions'),
    ]);
    if (!templatesRes.ok || !sessionsRes.ok) {
      throw new Error(
        t('common.requestFailed', { status: templatesRes.status || sessionsRes.status }),
      );
    }
    templates.value = await templatesRes.json();
    sessions.value = await sessionsRes.json();
  } catch (err) {
    loadError.value = err instanceof Error ? err.message : t('exam.loadFailed');
  } finally {
    isLoading.value = false;
  }
};

const formatDate = (dateStr: string) =>
  new Date(dateStr).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });

const scoreTier = (score: number) => (score >= 80 ? 'good' : score >= 60 ? 'mid' : 'bad');

const takeExam = (templateId: string) =>
  router.push({ name: 'exam-session', params: { templateId } });
const editExam = (templateId: string) => router.push({ name: 'exam-edit', params: { templateId } });
const createExam = () => router.push({ name: 'exam-create' });
const viewSession = (sessionId: string) =>
  router.push({ name: 'exam-results', params: { sessionId } });

onMounted(fetchData);
</script>

<template>
  <div class="lobby">
    <header class="lobby-header">
      <div class="lobby-heading">
        <h1 class="lobby-title font-body">{{ t('exam.title') }}</h1>
        <p class="lobby-tagline font-body">{{ t('exam.tagline') }}</p>
      </div>
      <div class="lobby-header-right">
        <div class="lobby-stats font-label">
          <span class="lobby-stat">
            <span class="lobby-stat-k">{{ t('exam.taken') }}</span>
            <span class="lobby-stat-v">{{ stats.total }}</span>
          </span>
          <span class="lobby-stat">
            <span class="lobby-stat-k">{{ t('exam.avgScore') }}</span>
            <span class="lobby-stat-v">{{ stats.avgScore }}%</span>
          </span>
          <span class="lobby-stat">
            <span class="lobby-stat-k">{{ t('exam.bestScore') }}</span>
            <span class="lobby-stat-v lobby-stat-v--best">{{ stats.bestScore }}%</span>
          </span>
        </div>
        <AppButton @click="createExam">{{ t('exam.createCustom') }}</AppButton>
      </div>
    </header>

    <div class="lobby-filters">
      <button
        v-for="f in typeFilters"
        :key="f.key"
        type="button"
        class="filter-tab font-label"
        :class="{ 'filter-tab--active': selectedType === f.key }"
        @click="selectType(f.key)"
      >
        {{ f.label }}
      </button>
      <template v-if="availableParts.length">
        <span class="filter-sep" aria-hidden="true">|</span>
        <button
          type="button"
          class="filter-tab font-label"
          :class="{ 'filter-tab--active': selectedPart === 'all' }"
          @click="selectedPart = 'all'"
        >
          {{ t('questionBank.anyPart') }}
        </button>
        <button
          v-for="part in availableParts"
          :key="part"
          type="button"
          class="filter-tab font-label"
          :class="{ 'filter-tab--active': selectedPart === part }"
          @click="selectedPart = part"
        >
          {{ part }}
        </button>
      </template>
    </div>

    <p v-if="loadError" class="lobby-error font-body" role="alert">
      {{ loadError }}
      <AppButton variant="secondary" @click="fetchData">{{ t('exam.retry') }}</AppButton>
    </p>

    <div class="lobby-body">
      <section class="lobby-catalog" :aria-label="t('exam.catalog')">
        <h2 class="lobby-section-label font-label">{{ t('exam.catalog') }}</h2>

        <div v-if="isLoading" class="lobby-status font-label">{{ t('common.loading') }}</div>

        <div v-else-if="filteredTemplates.length" class="catalog-scroll">
          <article v-for="tpl in filteredTemplates" :key="tpl.id" class="catalog-row">
            <div class="catalog-main">
              <div class="catalog-chips font-label">
                <span class="chip">{{ TYPE_LABELS[tpl.examType] || tpl.examType }}</span>
                <span v-if="tpl.level" class="chip chip--muted">{{ tpl.level }}</span>
                <span v-if="tpl.isPublic" class="chip chip--official">{{
                  t('exam.official')
                }}</span>
              </div>
              <h3 class="catalog-name font-body">{{ tpl.name }}</h3>
              <p v-if="tpl.description" class="catalog-desc font-body">{{ tpl.description }}</p>
              <div class="catalog-meta font-label">
                <span>{{ tpl.durationMinutes }} {{ t('common.minutes') }}</span>
                <span>{{ tpl.totalQuestions }} {{ t('common.questions') }}</span>
                <span>{{ t('exam.pass', { score: tpl.passingScore }) }}</span>
              </div>
            </div>
            <div class="catalog-actions">
              <AppButton v-if="!tpl.isPublic" variant="secondary" @click="editExam(tpl.id)">
                {{ t('exam.editExam') }}
              </AppButton>
              <AppButton @click="takeExam(tpl.id)">{{ t('exam.take') }}</AppButton>
            </div>
          </article>
        </div>

        <div v-else class="lobby-empty font-body">
          <p>{{ t('exam.noExams') }}</p>
          <p class="lobby-empty-sub">{{ t('exam.noExamsSub') }}</p>
          <AppButton @click="createExam">{{ t('exam.createCustom') }}</AppButton>
        </div>
      </section>

      <section class="lobby-history" :aria-label="t('exam.history')">
        <h2 class="lobby-section-label font-label">{{ t('exam.history') }}</h2>
        <div v-if="!isLoading && recentSessions.length" class="history-scroll">
          <button
            v-for="session in recentSessions"
            :key="session.id"
            type="button"
            class="history-row"
            @click="viewSession(session.id)"
          >
            <div class="history-info">
              <div class="history-name font-body">
                {{ templatesById.get(session.examTemplateId)?.name || t('exam.unknownExam') }}
              </div>
              <div class="history-date font-label">{{ formatDate(session.startedAt) }}</div>
            </div>
            <div class="history-result font-label">
              <span>{{ session.correctCount }}/{{ session.totalCount }}</span>
              <span class="score-badge" :class="`score-badge--${scoreTier(session.score)}`">
                {{ session.score }}%
              </span>
            </div>
          </button>
        </div>
        <p v-else-if="!isLoading" class="lobby-status font-label">—</p>
      </section>
    </div>
  </div>
</template>

<style scoped>
.lobby {
  flex: 1 1 0;
  min-height: 0;
  width: 100%;
  box-sizing: border-box;
  /* stylelint-disable-next-line scale-unlimited/declaration-strict-value -- full-bleed console padding */
  padding: 20px var(--space-9) var(--space-8);
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
  overflow: hidden;
}

.lobby-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-7);
  flex-wrap: wrap;
  flex-shrink: 0;
}
.lobby-title {
  margin: 0 0 var(--space-2);
  font-size: var(--font-size-xl);
  font-weight: 700;
  color: var(--color-accent);
}
.lobby-tagline {
  margin: 0;
  font-size: var(--font-size-md);
  color: var(--text-secondary);
}
.lobby-header-right {
  display: flex;
  align-items: center;
  gap: var(--space-7);
  flex-wrap: wrap;
}
.lobby-stats {
  display: flex;
  gap: var(--space-6);
  flex-wrap: wrap;
}
.lobby-stat {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  background: var(--surface-page);
  border: var(--space-1) solid var(--surface-panel-border);
  padding: var(--space-3) var(--space-5);
  min-width: 72px;
}
.lobby-stat-k {
  font-size: var(--font-size-2xs);
  letter-spacing: var(--tracking-wide);
  color: var(--text-secondary);
}
.lobby-stat-v {
  font-size: var(--font-size-lg);
  font-weight: 700;
  color: var(--text-primary);
}
.lobby-stat-v--best {
  color: var(--status-success);
}

.lobby-filters {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
  align-items: center;
  flex-shrink: 0;
}
.filter-tab {
  background: transparent;
  border: var(--space-1) solid var(--surface-panel-border);
  color: var(--text-secondary);
  font-size: var(--font-size-2xs);
  letter-spacing: var(--tracking-wide);
  padding: var(--space-2) var(--space-5);
  cursor: pointer;
  text-transform: uppercase;
}
.filter-tab--active {
  background: var(--state-selected-bg);
  border-color: var(--state-selected-bg);
  color: var(--text-on-accent);
  font-weight: 700;
}
.filter-tab:hover:not(.filter-tab--active) {
  color: var(--text-primary);
  border-color: var(--color-accent);
}
.filter-tab:focus-visible {
  outline: var(--focus-ring-width) solid var(--color-focus-ring);
  outline-offset: 2px;
}
.filter-sep {
  color: var(--text-disabled);
  font-size: var(--font-size-sm);
}

.lobby-error {
  color: var(--status-danger);
  font-size: var(--font-size-md);
  margin: 0;
  display: flex;
  align-items: center;
  gap: var(--space-5);
  flex-wrap: wrap;
  flex-shrink: 0;
}

.lobby-body {
  flex: 1 1 0;
  min-height: 0;
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--space-7);
  overflow: hidden;
}
@media (min-width: 900px) {
  .lobby-body {
    grid-template-columns: minmax(0, 3fr) minmax(0, 2fr);
  }
}

.lobby-section-label {
  margin: 0 0 var(--space-4);
  font-size: var(--font-size-2xs);
  letter-spacing: var(--tracking-wide);
  color: var(--text-secondary);
  flex-shrink: 0;
}

.lobby-catalog,
.lobby-history {
  display: flex;
  flex-direction: column;
  min-height: 0;
  min-width: 0;
  overflow: hidden;
}

.catalog-scroll,
.history-scroll {
  flex: 1 1 0;
  min-height: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.catalog-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-7);
  background: var(--surface-panel);
  border-left: var(--border-width-accent) solid var(--surface-panel-border);
  padding: var(--space-7) var(--space-8);
  flex-wrap: wrap;
}
.catalog-row:hover {
  border-left-color: var(--color-accent);
  background: var(--state-hover-surface);
}
.catalog-main {
  min-width: 0;
  flex: 1;
}
.catalog-chips {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
  margin-bottom: var(--space-3);
}
.chip {
  font-size: var(--font-size-2xs);
  letter-spacing: var(--tracking-normal);
  color: var(--text-label-accent);
  border: var(--space-1) solid var(--surface-panel-border);
  padding: var(--space-1) var(--space-4);
}
.chip--muted {
  color: var(--text-secondary);
}
.chip--official {
  color: var(--status-success);
  border-color: var(--status-success-subtle);
}
.catalog-name {
  margin: 0 0 var(--space-2);
  font-size: var(--font-size-lg);
  font-weight: 600;
  color: var(--text-primary);
}
.catalog-desc {
  margin: 0 0 var(--space-3);
  font-size: var(--font-size-md);
  color: var(--text-secondary);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.catalog-meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-6);
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}
.catalog-actions {
  display: flex;
  gap: var(--space-4);
  flex-shrink: 0;
  align-items: center;
}

.history-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-6);
  width: 100%;
  text-align: left;
  background: var(--surface-panel);
  border: none;
  border-left: var(--border-width-accent) solid var(--surface-panel-border);
  padding: var(--space-6) var(--space-7);
  cursor: pointer;
  color: inherit;
}
.history-row:hover {
  border-left-color: var(--color-accent);
  background: var(--state-hover-surface);
}
.history-row:focus-visible {
  outline: var(--focus-ring-width) solid var(--color-focus-ring);
  outline-offset: 2px;
}
.history-name {
  font-size: var(--font-size-md);
  font-weight: 600;
  color: var(--text-primary);
}
.history-date {
  font-size: var(--font-size-2xs);
  color: var(--text-secondary);
  margin-top: var(--space-1);
  letter-spacing: var(--tracking-normal);
}
.history-result {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
  flex-shrink: 0;
}
.score-badge {
  font-weight: 700;
  padding: var(--space-1) var(--space-3);
  border: var(--space-1) solid var(--surface-panel-border);
}
.score-badge--good {
  color: var(--status-success);
  border-color: var(--status-success-subtle);
}
.score-badge--mid {
  color: var(--status-caution);
  border-color: var(--status-caution-subtle);
}
.score-badge--bad {
  color: var(--status-danger);
  border-color: var(--status-danger-subtle);
}

.lobby-status {
  color: var(--text-secondary);
  font-size: var(--font-size-md);
  margin: 0;
  padding: var(--space-8) 0;
}
.lobby-empty {
  color: var(--text-secondary);
  font-size: var(--font-size-md);
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--space-5);
  padding: var(--space-9) 0;
}
.lobby-empty-sub {
  margin: 0;
  color: var(--text-disabled);
}
.lobby-empty p {
  margin: 0;
}
</style>
