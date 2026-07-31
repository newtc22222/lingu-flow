<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { apiFetch } from '../utils/api';

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

const EXAM_CONFIG: Record<string, { label: string; icon: string; color: string; gradient: string; flag: string }> = {
  toeic: {
    label: 'TOEIC',
    icon: '🇺🇸',
    flag: '🇺🇸',
    color: 'from-blue-500/20 to-cyan-500/20 border-blue-500/30',
    gradient: 'from-blue-600 to-cyan-500',
  },
  ielts: {
    label: 'IELTS',
    icon: '🇬🇧',
    flag: '🇬🇧',
    color: 'from-red-500/20 to-orange-500/20 border-red-500/30',
    gradient: 'from-red-600 to-orange-500',
  },
  hsk: {
    label: 'HSK',
    icon: '🇨🇳',
    flag: '🇨🇳',
    color: 'from-rose-500/20 to-pink-500/20 border-rose-500/30',
    gradient: 'from-rose-600 to-pink-500',
  },
  jlpt: {
    label: 'JLPT',
    icon: '🇯🇵',
    flag: '🇯🇵',
    color: 'from-purple-500/20 to-violet-500/20 border-purple-500/30',
    gradient: 'from-purple-600 to-violet-500',
  },
  custom: {
    label: 'Custom',
    icon: '⚙️',
    flag: '⚙️',
    color: 'from-emerald-500/20 to-teal-500/20 border-emerald-500/30',
    gradient: 'from-emerald-600 to-teal-500',
  },
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

onMounted(fetchData);
</script>

<template>
  <div class="flex flex-col h-full bg-slate-900 text-slate-100 overflow-y-auto">
    <!-- Header -->
    <div class="relative overflow-hidden bg-gradient-to-br from-slate-800 via-slate-800 to-slate-900 border-b border-slate-700/60 px-6 py-8">
      <div class="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_rgba(99,102,241,0.12),_transparent_60%)]"></div>
      <div class="relative max-w-6xl mx-auto">
        <div class="flex items-center justify-between flex-wrap gap-4">
          <div>
            <div class="flex items-center gap-3 mb-1">
              <span class="text-3xl">🎓</span>
              <h1 class="text-3xl font-bold bg-gradient-to-r from-indigo-400 to-cyan-400 bg-clip-text text-transparent">
                Exam Simulator
              </h1>
            </div>
            <p class="text-slate-400 text-sm ml-12">
              TOEIC · IELTS · HSK · JLPT — real conditions, real results
            </p>
          </div>
          <button
            @click="emit('create-exam')"
            class="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 text-white rounded-xl font-medium transition-all duration-200 shadow-lg shadow-indigo-500/20 cursor-pointer"
          >
            <span class="text-lg">+</span> Create Custom Exam
          </button>
        </div>

        <!-- Stats Row -->
        <div class="mt-6 grid grid-cols-3 gap-4 max-w-lg">
          <div class="bg-slate-700/40 rounded-xl p-3 text-center border border-slate-600/30">
            <div class="text-2xl font-bold text-indigo-400">{{ stats.total }}</div>
            <div class="text-xs text-slate-400 mt-0.5">Exams Taken</div>
          </div>
          <div class="bg-slate-700/40 rounded-xl p-3 text-center border border-slate-600/30">
            <div class="text-2xl font-bold text-cyan-400">{{ stats.avgScore }}%</div>
            <div class="text-xs text-slate-400 mt-0.5">Avg Score</div>
          </div>
          <div class="bg-slate-700/40 rounded-xl p-3 text-center border border-slate-600/30">
            <div class="text-2xl font-bold text-emerald-400">{{ stats.bestScore }}%</div>
            <div class="text-xs text-slate-400 mt-0.5">Best Score</div>
          </div>
        </div>
      </div>
    </div>

    <div class="flex-1 max-w-6xl mx-auto w-full px-6 py-6">

      <!-- Filter Tabs -->
      <div class="flex gap-2 mb-6 flex-wrap">
        <button
          v-for="f in typeFilters"
          :key="f.key"
          @click="selectedType = f.key"
          :class="[
            'flex items-center gap-1.5 px-4 py-2 rounded-full text-sm font-medium transition-all duration-200 cursor-pointer',
            selectedType === f.key
              ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-500/20'
              : 'bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-slate-200 border border-slate-700',
          ]"
        >
          <span>{{ f.icon }}</span> {{ f.label }}
        </button>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div
          v-for="i in 4" :key="i"
          class="h-48 bg-slate-800 rounded-2xl animate-pulse border border-slate-700"
        ></div>
      </div>

      <div v-else>
        <!-- Exam Cards Grid -->
        <div v-if="filteredTemplates.length" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
          <div
            v-for="template in filteredTemplates"
            :key="template._id"
            :class="[
              'group relative bg-gradient-to-br border rounded-2xl p-5 flex flex-col cursor-pointer transition-all duration-300 hover:scale-[1.02] hover:shadow-xl',
              EXAM_CONFIG[template.examType]?.color || 'from-slate-700/20 to-slate-600/20 border-slate-600/30',
            ]"
            @click="emit('start-exam', template._id)"
          >
            <!-- Exam type badge -->
            <div class="flex items-start justify-between mb-3">
              <div class="flex items-center gap-2">
                <span class="text-2xl">{{ EXAM_CONFIG[template.examType]?.flag || '📄' }}</span>
                <div>
                  <div
                    :class="[
                      'text-xs font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-gradient-to-r text-white inline-block',
                      EXAM_CONFIG[template.examType]?.gradient || 'from-slate-600 to-slate-500',
                    ]"
                  >
                    {{ EXAM_CONFIG[template.examType]?.label || 'Custom' }}
                  </div>
                  <div v-if="template.level" class="text-xs text-slate-400 mt-0.5">{{ template.level }}</div>
                </div>
              </div>
              <div v-if="template.isPublic" class="text-xs bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 px-2 py-0.5 rounded-full">
                Official
              </div>
            </div>

            <!-- Name & Description -->
            <h3 class="font-semibold text-slate-100 mb-1 group-hover:text-white transition-colors leading-snug">
              {{ template.name }}
            </h3>
            <p class="text-slate-400 text-xs leading-relaxed flex-1 line-clamp-2 mb-4">
              {{ template.description }}
            </p>

            <!-- Meta -->
            <div class="flex items-center justify-between mt-auto pt-3 border-t border-white/5">
              <div class="flex gap-3 text-xs text-slate-400">
                <span class="flex items-center gap-1">⏱ {{ template.duration }} min</span>
                <span class="flex items-center gap-1">❓ {{ template.totalQuestions }} Qs</span>
              </div>
              <div class="text-xs text-slate-400">Pass: {{ template.passingScore }}%</div>
            </div>

            <!-- Hover CTA -->
            <div class="absolute inset-0 rounded-2xl bg-white/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-center justify-center">
              <div
                :class="[
                  'bg-gradient-to-r text-white px-6 py-2.5 rounded-xl font-semibold shadow-lg transform translate-y-2 group-hover:translate-y-0 transition-transform duration-300',
                  EXAM_CONFIG[template.examType]?.gradient || 'from-indigo-600 to-cyan-600',
                ]"
              >
                Start Exam →
              </div>
            </div>
          </div>
        </div>

        <!-- Empty state -->
        <div v-else class="text-center py-16 text-slate-500">
          <div class="text-5xl mb-3">📭</div>
          <p class="text-lg">No exams found for this category.</p>
          <p class="text-sm mt-1">Try creating a custom exam!</p>
        </div>

        <!-- Recent History -->
        <div v-if="recentSessions.length" class="mt-2">
          <h2 class="text-lg font-semibold text-slate-200 mb-3 flex items-center gap-2">
            <span>📋</span> Recent Sessions
          </h2>
          <div class="bg-slate-800 rounded-2xl border border-slate-700 overflow-hidden">
            <div
              v-for="session in recentSessions"
              :key="session._id"
              class="flex items-center justify-between px-5 py-3.5 border-b border-slate-700/50 last:border-0 hover:bg-slate-700/30 transition-colors cursor-pointer"
              @click="emit('view-session', session._id)"
            >
              <div class="flex items-center gap-3">
                <span class="text-lg">{{ EXAM_CONFIG[session.examTemplateId?.examType]?.flag || '📄' }}</span>
                <div>
                  <div class="text-sm font-medium text-slate-200">
                    {{ session.examTemplateId?.name || 'Unknown Exam' }}
                  </div>
                  <div class="text-xs text-slate-500">{{ formatDate(session.createdAt) }}</div>
                </div>
              </div>
              <div class="flex items-center gap-3">
                <div class="text-sm text-slate-400">
                  {{ session.correctCount }}/{{ session.totalCount }}
                </div>
                <div
                  :class="[
                    'text-sm font-bold px-3 py-1 rounded-full',
                    session.score >= 70 ? 'bg-emerald-500/20 text-emerald-400' :
                    session.score >= 50 ? 'bg-yellow-500/20 text-yellow-400' :
                    'bg-rose-500/20 text-rose-400',
                  ]"
                >
                  {{ session.score }}%
                </div>
                <span class="text-slate-500 text-xs">→</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
