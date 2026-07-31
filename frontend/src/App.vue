<script setup lang="ts">
import { ref, onMounted } from 'vue'
import StudyDashboard from './components/StudyDashboard.vue'
import CardManagement from './components/CardManagement.vue'
import DeckManagement from './components/DeckManagement.vue'
import Login from './components/Login.vue'
import Signup from './components/Signup.vue'
import ExamHub from './components/ExamHub.vue'
import ExamRoom from './components/ExamRoom.vue'
import ExamResults from './components/ExamResults.vue'
import ExamCreator from './components/ExamCreator.vue'

type AppView = 'study' | 'manageCards' | 'manageDecks' | 'login' | 'signup'
             | 'exams' | 'examRoom' | 'examResults' | 'examCreator'

const currentView = ref<AppView>('login')
const isAuthenticated = ref(false)

// Exam state
const activeTemplateId = ref<string>('')
const activeSessionId = ref<string>('')

onMounted(() => {
  const token = localStorage.getItem('token')
  if (token) {
    isAuthenticated.value = true
    currentView.value = 'study'
  }
})

const handleAuthSuccess = () => {
  isAuthenticated.value = true
  currentView.value = 'study'
}

const logout = () => {
  localStorage.removeItem('token')
  isAuthenticated.value = false
  currentView.value = 'login'
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
  <div class="h-screen w-screen bg-slate-900 text-slate-100 flex flex-col overflow-hidden">
    <!-- Global Navigation Bar -->
    <nav v-if="isAuthenticated" class="bg-slate-800 px-4 py-3 flex justify-between items-center border-b border-slate-700 z-10 shrink-0">
      <h1 class="text-xl font-bold text-emerald-400 tracking-tight">LinguFlow</h1>
      <div class="flex gap-2 items-center">
        <button
          @click="currentView = 'study'"
          :class="['px-3 py-1.5 rounded-lg font-medium transition-colors cursor-pointer text-sm', currentView === 'study' ? 'bg-emerald-600 text-white' : 'bg-slate-700 text-slate-300 hover:bg-slate-600']"
        >
          📚 Study
        </button>
        <button
          @click="goToExamHub"
          :class="[
            'px-3 py-1.5 rounded-lg font-medium transition-colors cursor-pointer text-sm flex items-center gap-1',
            ['exams','examRoom','examResults','examCreator'].includes(currentView) ? 'bg-indigo-600 text-white' : 'bg-slate-700 text-slate-300 hover:bg-slate-600',
          ]"
        >
          🎓 Exams
        </button>
        <button
          @click="currentView = 'manageDecks'"
          :class="['px-3 py-1.5 rounded-lg font-medium transition-colors cursor-pointer text-sm', currentView === 'manageDecks' ? 'bg-emerald-600 text-white' : 'bg-slate-700 text-slate-300 hover:bg-slate-600']"
        >
          Decks
        </button>
        <button
          @click="currentView = 'manageCards'"
          :class="['px-3 py-1.5 rounded-lg font-medium transition-colors cursor-pointer text-sm', currentView === 'manageCards' ? 'bg-emerald-600 text-white' : 'bg-slate-700 text-slate-300 hover:bg-slate-600']"
        >
          Cards
        </button>
        <button
          @click="logout"
          class="ml-2 px-3 py-1.5 rounded-lg font-medium transition-colors cursor-pointer text-sm bg-rose-500/10 text-rose-400 border border-rose-500/20 hover:bg-rose-500/20"
        >
          Logout
        </button>
      </div>
    </nav>

    <!-- Main Content Area -->
    <div class="flex-1 overflow-hidden relative">
      <template v-if="isAuthenticated">
        <StudyDashboard v-if="currentView === 'study'" />
        <DeckManagement v-else-if="currentView === 'manageDecks'" />
        <CardManagement v-else-if="currentView === 'manageCards'" @close="currentView = 'study'" />

        <!-- Exam Views -->
        <ExamHub
          v-else-if="currentView === 'exams'"
          @start-exam="startExam"
          @create-exam="goToExamCreator"
          @view-session="onViewSession"
        />
        <ExamRoom
          v-else-if="currentView === 'examRoom'"
          :template-id="activeTemplateId"
          @done="onExamDone"
          @back="backToExamHub"
        />
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
        <Login v-if="currentView === 'login'" @login-success="handleAuthSuccess" @go-to-signup="currentView = 'signup'" />
        <Signup v-else-if="currentView === 'signup'" @signup-success="handleAuthSuccess" @go-to-login="currentView = 'login'" />
      </template>
    </div>
  </div>
</template>
