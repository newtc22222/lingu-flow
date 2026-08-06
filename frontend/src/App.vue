<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/features/auth/store/authStore'
import { SUPPORTED_LOCALES, setLocale, type AppLocale } from '@/i18n'
import ConfirmDialog from '@/shared/components/ConfirmDialog.vue'
import AppFooter from '@/shared/components/AppFooter.vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const { t, locale } = useI18n()

const showLogoutConfirm = ref(false)

/** Which arcade tab reads as active. */
const activeTab = computed<'dashboard' | 'exams' | 'flashcards' | 'decks' | 'cards' | 'bank' | null>(() => {
  const path = route.path
  if (path.startsWith('/dashboard')) return 'dashboard'
  if (path.startsWith('/exams')) return 'exams'
  if (path.startsWith('/flashcards')) return 'flashcards'
  if (path.startsWith('/decks')) return 'decks'
  if (path.startsWith('/cards')) return 'cards'
  if (path.startsWith('/question-bank')) return 'bank'
  return null
})

/** The nav chrome is for signed-in screens only — `/auth` renders bare. */
const showNav = computed(() => auth.isAuthenticated && route.name !== 'auth')

function switchLocale(next: AppLocale) {
  setLocale(next)
}

function handleLogoutClick() {
  showLogoutConfirm.value = true
}

async function handleConfirmLogout() {
  auth.logout()
  await router.push({ name: 'auth' })
}
</script>

<template>
  <div class="h-screen w-screen bg-ink text-phosphor flex flex-col overflow-hidden">
    <!-- Top Navigation Header -->
    <header v-if="showNav" class="app-header">
      <div class="nav-container">
        <!-- Logo / Wordmark -->
        <RouterLink :to="{ name: 'dashboard' }" class="nav-logo font-pixel">
          LINGUFLOW
        </RouterLink>

        <!-- Navigation Tabs -->
        <nav class="nav-tabs" role="tablist">
          <RouterLink
            :to="{ name: 'dashboard' }"
            class="nav-tab font-label"
            :class="{ 'nav-tab--active': activeTab === 'dashboard' }"
          >
            {{ t('nav.dashboard') }}
          </RouterLink>
          <RouterLink
            :to="{ name: 'exams' }"
            class="nav-tab font-label"
            :class="{ 'nav-tab--active': activeTab === 'exams' }"
          >
            {{ t('nav.examMode') }}
          </RouterLink>
          <RouterLink
            :to="{ name: 'flashcards' }"
            class="nav-tab font-label"
            :class="{ 'nav-tab--active': activeTab === 'flashcards' }"
          >
            {{ t('nav.flashcards') }}
          </RouterLink>
          <RouterLink
            :to="{ name: 'decks' }"
            class="nav-tab font-label"
            :class="{ 'nav-tab--active': activeTab === 'decks' }"
          >
            {{ t('nav.manageDecks') }}
          </RouterLink>
          <RouterLink
            :to="{ name: 'question-bank' }"
            class="nav-tab font-label"
            :class="{ 'nav-tab--active': activeTab === 'bank' }"
          >
            {{ t('nav.questionBank') }}
          </RouterLink>
        </nav>

        <!-- Right Utility Controls -->
        <div class="nav-utils">
          <div class="lang-switch" role="group" :aria-label="t('nav.language')">
            <button
              v-for="code in SUPPORTED_LOCALES"
              :key="code"
              type="button"
              class="lang-btn font-label"
              :class="{ 'lang-btn--active': locale === code }"
              :aria-pressed="locale === code"
              @click="switchLocale(code)"
            >
              {{ code.toUpperCase() }}
            </button>
          </div>

          <button
            type="button"
            class="logout-btn font-label"
            @click="handleLogoutClick"
          >
            [{{ t('nav.logout') }}]
          </button>
        </div>
      </div>
    </header>

    <!-- Main Scrollable Content Area -->
    <div class="flex-1 overflow-y-auto relative flex flex-col justify-between">
      <RouterView v-slot="{ Component, route: current }">
        <component :is="Component" v-if="current.meta.fullBleed" />
        <div v-else class="arcade-app flex-1">
          <component :is="Component" />
        </div>
      </RouterView>

      <!-- Global App Footer -->
      <AppFooter v-if="showNav" />
    </div>

    <!-- Logout Confirmation Modal -->
    <ConfirmDialog
      v-model:is-open="showLogoutConfirm"
      :title="t('nav.logoutConfirmTitle')"
      :message="t('nav.logoutConfirmMessage')"
      :confirm-text="t('nav.logoutConfirm')"
      variant="danger"
      @confirm="handleConfirmLogout"
    />
  </div>
</template>

<style scoped>
.app-header {
  background: var(--surface-panel);
  border-bottom: var(--border-width-accent) solid var(--surface-panel-border);
  box-shadow: 0 4px 12px var(--ink);
  z-index: 40;
  width: 100%;
}

.nav-container {
  max-width: 1024px;
  margin: 0 auto;
  padding: var(--space-4) var(--space-8);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-6);
  flex-wrap: wrap;
}

.nav-logo {
  font-size: var(--font-size-md);
  color: var(--color-accent);
  letter-spacing: var(--tracking-normal);
  text-decoration: none;
}

.nav-logo:hover {
  opacity: 0.9;
}

.nav-tabs {
  display: flex;
  gap: var(--space-2);
  flex-wrap: wrap;
}

.nav-tab {
  font-size: var(--font-size-xs);
  letter-spacing: var(--tracking-wide);
  padding: var(--space-4) var(--space-6);
  background: transparent;
  color: var(--text-secondary);
  border: none;
  border-bottom: var(--border-width-accent) solid transparent;
  cursor: pointer;
  text-decoration: none;
  text-transform: uppercase;
  transition: color 0.15s ease, border-color 0.15s ease;
}

.nav-tab--active {
  color: var(--color-accent);
  border-bottom-color: var(--color-accent);
  font-weight: 700;
}

.nav-tab:hover:not(.nav-tab--active) {
  color: var(--text-primary);
}

.nav-utils {
  display: flex;
  align-items: center;
  gap: var(--space-6);
}

.lang-switch {
  display: flex;
  gap: var(--space-1);
}

.lang-btn {
  background: var(--surface-panel-border);
  border: none;
  color: var(--text-secondary);
  font-size: var(--font-size-2xs);
  letter-spacing: var(--tracking-tight);
  padding: var(--space-2) var(--space-4);
  cursor: pointer;
}

.lang-btn--active {
  background: var(--state-selected-bg);
  color: var(--text-on-accent);
}

.lang-btn:hover:not(.lang-btn--active) {
  color: var(--text-primary);
}

.logout-btn {
  background: none;
  border: none;
  color: var(--status-danger);
  font-size: var(--font-size-xs);
  letter-spacing: var(--tracking-wide);
  cursor: pointer;
  padding: var(--space-2) 0;
  text-transform: uppercase;
}

.logout-btn:hover {
  opacity: 0.8;
}

.nav-tab:focus-visible,
.lang-btn:focus-visible,
.logout-btn:focus-visible {
  outline: var(--focus-ring-width) solid var(--color-focus-ring);
  outline-offset: 2px;
}

.arcade-app {
  max-width: 920px;
  margin: 0 auto;
  width: 100%;
  /* stylelint-disable-next-line scale-unlimited/declaration-strict-value -- approved Step 2 - layout one-off, see design-tokens.json notes */
  padding: 28px var(--space-9) 60px;
  box-sizing: border-box;
}
</style>
