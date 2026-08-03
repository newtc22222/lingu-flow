<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { apiFetch } from '../utils/api';
import PixelFrame from '../shared/components/PixelFrame.vue';

interface ExamTemplate {
  _id: string;
  name: string;
  examType: 'toeic' | 'ielts' | 'hsk' | 'jlpt' | 'custom';
  description: string;
  duration: number;
  totalQuestions: number;
  passingScore: number;
  level: string;
  isPublic: boolean;
}

interface ExamSession {
  _id: string;
  examTemplateId: { name: string; examType: string };
  score: number;
  status: string;
  createdAt: string;
  correctCount: number;
  totalCount: number;
}

const emit = defineEmits<{
  (e: 'start-exam', templateId: string): void;
  (e: 'create-exam'): void;
  (e: 'view-session', sessionId: string): void;
}>();

const templates = ref<ExamTemplate[]>([]);
const sessions = ref<ExamSession[]>([]);
const isLoading = ref(true);
const selectedType = ref<string>('all');

const EXAM_CONFIG: Record<string, { label: string; flag: string }> = {
  toeic: { label: 'TOEIC', flag: '🇺🇸' },
  ielts: { label: 'IELTS', flag: '🇬🇧' },
  hsk: { label: 'HSK', flag: '🇨🇳' },
  jlpt: { label: 'JLPT', flag: '🇯🇵' },
  custom: { label: 'Custom', flag: '⚙️' },
};

const typeFilters = [
  { key: 'all', label: 'All Exams', icon: '📚' },
  { key: 'toeic', label: 'TOEIC', icon: '🇺🇸' },
  { key: 'ielts', label: 'IELTS', icon: '🇬🇧' },
  { key: 'hsk', label: 'HSK', icon: '🇨🇳' },
  { key: 'jlpt', label: 'JLPT', icon: '🇯🇵' },
  { key: 'custom', label: 'Custom', icon: '⚙️' },
];

const filteredTemplates = computed(() =>
  selectedType.value === 'all'
    ? templates.value
    : templates.value.filter((t) => t.examType === selectedType.value),
);

const stats = computed(() => {
  const completed = sessions.value.filter((s) => s.status === 'completed');
  const avgScore = completed.length
    ? Math.round(completed.reduce((sum, s) => sum + s.score, 0) / completed.length)
    : 0;
  const bestScore = completed.length ? Math.max(...completed.map((s) => s.score)) : 0;
  return { total: completed.length, avgScore, bestScore };
});

const recentSessions = computed(() => sessions.value.slice(0, 5));

const fetchData = async () => {
  isLoading.value = true;
  try {
    const [templatesRes, sessionsRes] = await Promise.all([
      apiFetch('/api/exams/templates'),
      apiFetch('/api/exams/sessions'),
    ]);
    templates.value = await templatesRes.json();
    sessions.value = await sessionsRes.json();
  } catch (err) {
    console.error('Failed to load exams:', err);
  } finally {
    isLoading.value = false;
  }
};

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
};

const scoreTier = (score: number) => (score >= 80 ? 'good' : score >= 60 ? 'mid' : 'bad');

onMounted(fetchData);
</script>

<template>
  <div class="exam-hub">
    <!-- Header -->
    <div class="hub-header">
      <div class="hub-heading">
        <span class="hub-icon" aria-hidden="true">🎓</span>
        <h1 class="hub-title font-pixel">EXAM SIMULATOR</h1>
      </div>
      <p class="hub-tagline font-label">TOEIC · IELTS · HSK · JLPT — REAL CONDITIONS, REAL RESULTS</p>

      <button type="button" class="btn-arcade hub-create-btn font-label" @click="emit('create-exam')">
        + CREATE CUSTOM EXAM
      </button>

      <!-- Stats Row -->
      <div class="hub-stats">
        <PixelFrame frame-color="amber" surface="cabinet" :ring-width="3">
          <div class="stat-inner">
            <span class="stat-label font-label">EXAMS TAKEN</span>
            <span class="stat-value font-label">{{ stats.total }}</span>
          </div>
        </PixelFrame>
        <PixelFrame frame-color="amber" surface="cabinet" :ring-width="3">
          <div class="stat-inner">
            <span class="stat-label font-label">AVG SCORE</span>
            <span class="stat-value font-label">{{ stats.avgScore }}%</span>
          </div>
        </PixelFrame>
        <PixelFrame frame-color="amber" surface="cabinet" :ring-width="3">
          <div class="stat-inner">
            <span class="stat-label font-label">BEST SCORE</span>
            <span class="stat-value font-label stat-value--green">{{ stats.bestScore }}%</span>
          </div>
        </PixelFrame>
      </div>
    </div>

    <!-- Filter Tabs -->
    <div class="hub-filters">
      <button
        v-for="f in typeFilters"
        :key="f.key"
        type="button"
        class="filter-tab font-label"
        :class="{ 'filter-tab--active': selectedType === f.key }"
        @click="selectedType = f.key"
      >
        <span aria-hidden="true">{{ f.icon }}</span> {{ f.label }}
      </button>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="hub-skeleton-grid">
      <div v-for="i in 4" :key="i" class="hub-skeleton"></div>
    </div>

    <template v-else>
      <!-- Exam Cards Grid -->
      <div v-if="filteredTemplates.length" class="hub-grid">
        <PixelFrame
          v-for="template in filteredTemplates"
          :key="template._id"
          frame-color="amber"
          surface="cabinet"
          :ring-width="3"
          class="exam-card-frame"
        >
          <button type="button" class="exam-card" @click="emit('start-exam', template._id)">
            <div class="exam-card-top">
              <div class="exam-card-id">
                <span class="exam-card-flag" aria-hidden="true">{{ EXAM_CONFIG[template.examType]?.flag || '📄' }}</span>
                <div>
                  <div class="exam-card-type font-label">{{ EXAM_CONFIG[template.examType]?.label || 'Custom' }}</div>
                  <div v-if="template.level" class="exam-card-level font-label">{{ template.level }}</div>
                </div>
              </div>
              <span v-if="template.isPublic" class="badge-official font-label">OFFICIAL</span>
            </div>

            <h3 class="exam-card-name font-body">{{ template.name }}</h3>
            <p class="exam-card-desc font-body">{{ template.description }}</p>

            <div class="exam-card-meta font-label">
              <span>⏱ {{ template.duration }} MIN</span>
              <span>❓ {{ template.totalQuestions }} Qs</span>
              <span>PASS {{ template.passingScore }}%</span>
            </div>
          </button>
        </PixelFrame>
      </div>

      <!-- Empty state -->
      <div v-else class="hub-empty font-label">
        <div class="hub-empty-icon" aria-hidden="true">📭</div>
        <p>NO EXAMS FOUND FOR THIS CATEGORY.</p>
        <p class="hub-empty-sub">Try creating a custom exam!</p>
      </div>

      <!-- Recent History -->
      <div v-if="recentSessions.length" class="hub-recent">
        <h2 class="hub-recent-title font-body">📋 Recent Sessions</h2>
        <ul class="hub-recent-list">
          <li
            v-for="session in recentSessions"
            :key="session._id"
            class="hub-recent-row"
            @click="emit('view-session', session._id)"
          >
            <div class="hub-recent-info">
              <span class="hub-recent-flag" aria-hidden="true">{{ EXAM_CONFIG[session.examTemplateId?.examType]?.flag || '📄' }}</span>
              <div>
                <div class="hub-recent-name font-body">{{ session.examTemplateId?.name || 'Unknown Exam' }}</div>
                <div class="hub-recent-date font-label">{{ formatDate(session.createdAt) }}</div>
              </div>
            </div>
            <div class="hub-recent-result">
              <span class="hub-recent-count font-label">{{ session.correctCount }}/{{ session.totalCount }}</span>
              <span class="score-badge font-label" :class="`score-badge--${scoreTier(session.score)}`">
                {{ session.score }}%
              </span>
              <span class="hub-recent-arrow" aria-hidden="true">→</span>
            </div>
          </li>
        </ul>
      </div>
    </template>
  </div>
</template>

<style scoped>
.exam-hub {
  display: flex;
  flex-direction: column;
}
.hub-header {
  margin-bottom: 26px;
}
.hub-heading {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 4px;
}
.hub-icon {
  font-size: 28px;
}
.hub-title {
  font-size: 16px;
  color: var(--color-accent);
  margin: 0;
}
.hub-tagline {
  color: var(--text-secondary);
  font-size: 12px;
  letter-spacing: 0.5px;
  margin: 0 0 16px;
}
.hub-create-btn {
  margin-bottom: 20px;
}
.hub-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  max-width: 480px;
}
.stat-inner {
  padding: 14px;
}
.stat-label {
  display: block;
  font-weight: 700;
  font-size: 10px;
  letter-spacing: 1.5px;
  text-transform: uppercase;
  color: var(--text-secondary);
  margin-bottom: 6px;
}
.stat-value {
  font-size: 18px;
  font-weight: 700;
  color: var(--color-accent);
}
.stat-value--green {
  color: var(--status-success);
}

.hub-filters {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 22px;
}
.filter-tab {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 14px;
  font-size: 11px;
  letter-spacing: 0.5px;
  background: var(--surface-panel);
  color: var(--text-secondary);
  border: 2px solid var(--surface-panel-border);
  cursor: pointer;
}
.filter-tab:hover:not(.filter-tab--active) {
  color: var(--text-primary);
  border-color: var(--muted);
}
.filter-tab--active {
  background: var(--state-selected-bg);
  border-color: var(--state-selected-bg);
  color: var(--text-on-accent);
}

.hub-skeleton-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
}
.hub-skeleton {
  height: 180px;
  background: var(--surface-panel);
  border: 2px solid var(--surface-panel-border);
  animation: hub-pulse 1.4s ease-in-out infinite;
}
@keyframes hub-pulse {
  50% {
    opacity: 0.5;
  }
}
@media (prefers-reduced-motion: reduce) {
  .hub-skeleton {
    animation: none;
  }
}

.hub-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
  margin-bottom: 32px;
}
.exam-card {
  width: 100%;
  height: 100%;
  background: none;
  border: none;
  padding: 16px;
  text-align: left;
  color: inherit;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 10px;
  transition: background 0.12s;
}
.exam-card:hover {
  background: var(--state-hover-surface);
}
.exam-card-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
}
.exam-card-id {
  display: flex;
  align-items: center;
  gap: 8px;
}
.exam-card-flag {
  font-size: 22px;
}
.exam-card-type {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 1px;
  color: var(--text-label-accent);
}
.exam-card-level {
  font-size: 10px;
  color: var(--text-secondary);
  margin-top: 2px;
}
.badge-official {
  font-size: 9px;
  letter-spacing: 1px;
  color: var(--status-success);
  border: 2px solid var(--status-success);
  padding: 2px 6px;
  white-space: nowrap;
}
.exam-card-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}
.exam-card-desc {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.5;
  margin: 0;
  flex: 1;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.exam-card-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  font-size: 10px;
  color: var(--text-secondary);
  padding-top: 8px;
  border-top: 1px solid var(--surface-panel-border);
}

.hub-empty {
  text-align: center;
  padding: 60px 0;
  color: var(--text-secondary);
}
.hub-empty-icon {
  font-size: 44px;
  margin-bottom: 10px;
}
.hub-empty-sub {
  font-size: 11px;
  margin-top: 4px;
}

.hub-recent-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 12px;
}
.hub-recent-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.hub-recent-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  background: var(--surface-panel);
  border-left: 3px solid var(--surface-panel-border);
  padding: 12px 16px;
  cursor: pointer;
  transition: border-color 0.12s, background 0.12s;
}
.hub-recent-row:hover {
  border-left-color: var(--color-accent);
  background: var(--state-hover-surface);
}
.hub-recent-info {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}
.hub-recent-flag {
  font-size: 16px;
}
.hub-recent-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}
.hub-recent-date {
  font-size: 10px;
  color: var(--text-secondary);
  margin-top: 2px;
}
.hub-recent-result {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}
.hub-recent-count {
  font-size: 11px;
  color: var(--text-secondary);
}
.score-badge {
  font-size: 11px;
  font-weight: 700;
  padding: 3px 9px;
  border: 2px solid;
}
.score-badge--good {
  color: var(--status-success);
  border-color: var(--status-success);
  background: var(--status-success-subtle);
}
.score-badge--mid {
  color: var(--status-caution);
  border-color: var(--status-caution);
  background: var(--status-caution-subtle);
}
.score-badge--bad {
  color: var(--status-danger);
  border-color: var(--status-danger);
  background: var(--status-danger-subtle);
}
.hub-recent-arrow {
  color: var(--text-secondary);
  font-size: 11px;
}

.btn-arcade {
  font-weight: 700;
  font-size: 13px;
  letter-spacing: 1.5px;
  text-transform: uppercase;
  background: var(--status-success);
  color: var(--text-on-accent);
  border: none;
  padding: 12px 22px;
  cursor: pointer;
  box-shadow: 0 4px 0 var(--status-success-subtle);
}
.btn-arcade:active {
  transform: translateY(4px);
  box-shadow: none;
}

.filter-tab:focus-visible,
.hub-create-btn:focus-visible,
.hub-recent-row:focus-visible {
  outline: 2px solid var(--color-focus-ring);
  outline-offset: 2px;
}
.exam-card:focus-visible {
  outline: 2px solid var(--color-focus-ring);
  outline-offset: -2px;
}
</style>
