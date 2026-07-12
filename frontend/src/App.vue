<script setup lang="ts">
import { ref, onMounted } from 'vue'
import StudyDashboard from './components/StudyDashboard.vue'
import CardManagement from './components/CardManagement.vue'
import DeckManagement from './components/DeckManagement.vue'
import Login from './components/Login.vue'
import Signup from './components/Signup.vue'

const currentView = ref<'study' | 'manageCards' | 'manageDecks' | 'login' | 'signup'>('login')
const isAuthenticated = ref(false)

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
</script>

<template>
  <div class="h-screen w-screen bg-slate-900 text-slate-100 flex flex-col overflow-hidden">
    <!-- Global Navigation Bar -->
    <nav v-if="isAuthenticated" class="bg-slate-800 p-4 flex justify-between items-center border-b border-slate-700 z-10 shrink-0">
      <h1 class="text-2xl font-bold text-emerald-400">LinguFlow</h1>
      <div class="flex gap-4 items-center">
        <button 
          @click="currentView = 'study'"
          :class="['px-4 py-2 rounded-lg font-medium transition-colors cursor-pointer', currentView === 'study' ? 'bg-emerald-600 text-white' : 'bg-slate-700 text-slate-300 hover:bg-slate-600']"
        >
          Study
        </button>
        <button 
          @click="currentView = 'manageDecks'"
          :class="['px-4 py-2 rounded-lg font-medium transition-colors cursor-pointer', currentView === 'manageDecks' ? 'bg-emerald-600 text-white' : 'bg-slate-700 text-slate-300 hover:bg-slate-600']"
        >
          Decks
        </button>
        <button 
          @click="currentView = 'manageCards'"
          :class="['px-4 py-2 rounded-lg font-medium transition-colors cursor-pointer', currentView === 'manageCards' ? 'bg-emerald-600 text-white' : 'bg-slate-700 text-slate-300 hover:bg-slate-600']"
        >
          Cards
        </button>
        <button 
          @click="logout"
          class="ml-4 px-4 py-2 rounded-lg font-medium transition-colors cursor-pointer bg-rose-500/10 text-rose-400 border border-rose-500/20 hover:bg-rose-500/20"
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
      </template>
      <template v-else>
        <Login v-if="currentView === 'login'" @login-success="handleAuthSuccess" @go-to-signup="currentView = 'signup'" />
        <Signup v-else-if="currentView === 'signup'" @signup-success="handleAuthSuccess" @go-to-login="currentView = 'login'" />
      </template>
    </div>
  </div>
</template>
