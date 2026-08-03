<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import ExamHub from './components/ExamHub.vue'
import ExamResults from './components/ExamResults.vue'
import ExamCreator from './components/ExamCreator.vue'
import ExamView from './features/exam/ExamView.vue'
import FlashcardsView from './features/flashcards/FlashcardsView.vue'
import DashboardView from './features/dashboard/DashboardView.vue'
import AuthView from './features/auth/AuthView.vue'
import DeckManagementView from './features/library/DeckManagementView.vue'
import CardManagementView from './features/library/CardManagementView.vue'

type AppView = 'dashboard' | 'flashcards' | 'manageCards' | 'manageDecks'
             | 'exams' | 'examRoom' | 'examResults' | 'examCreator'

const currentView = ref<AppView>('dashboard')
const isAuthenticated = ref(false)

/** Which arcade tab reads as active — exam sub-screens (hub/room/results/creator) all light up EXAM MODE. */
const activeTab = computed<'exams' | 'flashcards' | 'dashboard' | null>(() => {
  if (['exams', 'examRoom', 'examResults', 'examCreator'].includes(currentView.value)) return 'exams'
  if (currentView.value === 'flashcards') return 'flashcards'
  if (currentView.value === 'dashboard') return 'dashboard'
  return null
})

// Exam state
const activeTemplateId = ref<string>('')
const activeSessionId = ref<string>('')

onMounted(() => {
  const token = localStorage.getItem('token')
  if (token) {
    isAuthenticated.value = true
    currentView.value = 'dashboard'
  }
})

const handleAuthSuccess = () => {
  isAuthenticated.value = true
  currentView.value = 'dashboard'
}

const logout = () => {
  localStorage.removeItem('token')
  isAuthenticated.value = false
}

// ── Exam Navigation ────────────────────────────────────────────────────────
const goToExamHub = () => { currentView.value = 'exams' }

const startExam = (templateId: string) => {
  activeTemplateId.value = templateId
  currentView.value = 'examRoom'
}

const onExamDone = (sessionId: string) => {
  activeSessionId.value = sessionId
  currentView.value = 'examResults'
}

const onViewSession = (sessionId: string) => {
  activeSessionId.value = sessionId
  currentView.value = 'examResults'
}

const goToExamCreator = () => { currentView.value = 'examCreator' }

const onExamCreated = (templateId: string) => {
  startExam(templateId)
}

const backToExamHub = () => { currentView.value = 'exams' }
</script>

<template>
  <div class="h-screen w-screen bg-ink text-phosphor flex flex-col overflow-hidden">
    <!-- Global Navigation Bar -->
    <nav v-if="isAuthenticated" class="bg-cabinet px-4 py-3 flex flex-wrap justify-between items-center gap-3 border-b border-cabinet-light z-10 shrink-0">
      <div class="tabs">
        <button
          type="button"
          class="tab font-pixel"
          :class="{ 'tab--active': activeTab === 'exams' }"
          @click="goToExamHub"
        >
          EXAM MODE
        </button>
        <button
          type="button"
          class="tab font-pixel"
          :class="{ 'tab--active': activeTab === 'flashcards' }"
          @click="currentView = 'flashcards'"
        >
          FLASHCARDS
        </button>
        <button
          type="button"
          class="tab font-pixel"
          :class="{ 'tab--active': activeTab === 'dashboard' }"
          @click="currentView = 'dashboard'"
        >
          DASHBOARD
        </button>
      </div>
      <div class="flex gap-4 items-center font-label text-xs">
        <button type="button" class="util-link" @click="currentView = 'manageDecks'">QUẢN LÝ BỘ THẺ</button>
        <button type="button" class="util-link" @click="currentView = 'manageCards'">QUẢN LÝ THẺ</button>
        <button type="button" class="util-link util-link--danger" @click="logout">ĐĂNG XUẤT</button>
      </div>
    </nav>

    <!-- Main Content Area -->
    <div class="flex-1 overflow-y-auto relative">
      <template v-if="isAuthenticated">
        <div
          v-if="['exams', 'examRoom', 'flashcards', 'dashboard', 'manageDecks', 'manageCards'].includes(currentView)"
          class="arcade-app"
        >
          <ExamHub
            v-if="currentView === 'exams'"
            @start-exam="startExam"
            @create-exam="goToExamCreator"
            @view-session="onViewSession"
          />
          <ExamView
            v-else-if="currentView === 'examRoom'"
            :template-id="activeTemplateId"
            @done="onExamDone"
          />
          <FlashcardsView v-else-if="currentView === 'flashcards'" />
          <DashboardView v-else-if="currentView === 'dashboard'" />
          <DeckManagementView v-else-if="currentView === 'manageDecks'" />
          <CardManagementView v-else-if="currentView === 'manageCards'" @close="currentView = 'dashboard'" />
        </div>

        <ExamResults
          v-else-if="currentView === 'examResults'"
          :session-id="activeSessionId"
          @back="backToExamHub"
          @retake="startExam"
        />
        <ExamCreator
          v-else-if="currentView === 'examCreator'"
          @back="backToExamHub"
          @created="onExamCreated"
        />
      </template>
      <template v-else>
        <AuthView @auth-success="handleAuthSuccess" />
      </template>
    </div>
  </div>
</template>

<style scoped>
.tabs {
  display: flex;
  gap: var(--space-4);
}
.tab {
  font-size: var(--font-size-xs);
  letter-spacing: 0.5px;
  padding: var(--space-6) var(--space-7);
  background: var(--surface-panel);
  color: var(--text-secondary);
  border: none;
  cursor: pointer;
}
.tab--active {
  background: var(--state-selected-bg);
  color: var(--text-on-accent);
}
.tab:hover:not(.tab--active) {
  color: var(--text-primary);
}
.util-link {
  background: none;
  border: none;
  color: var(--text-secondary);
  letter-spacing: 0.5px;
  cursor: pointer;
  padding: var(--space-2) 0;
}
.util-link:hover {
  color: var(--text-primary);
}
.util-link--danger:hover {
  color: var(--status-danger);
}
.arcade-app {
  max-width: 920px;
  margin: 0 auto;
  padding: 28px var(--space-9) 60px;
}
</style>
