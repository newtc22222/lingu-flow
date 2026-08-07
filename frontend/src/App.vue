<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'
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
const isProfileMenuOpen = ref(false)

/** Which arcade tab reads as active. */
const activeTab = computed<'dashboard' | 'exams' | 'flashcards' | 'decks' | 'cards' | 'bank' | 'profile' | null>(() => {
  const path = route.path
  if (path.startsWith('/dashboard')) return 'dashboard'
  if (path.startsWith('/exams')) return 'exams'
  if (path.startsWith('/flashcards')) return 'flashcards'
  if (path.startsWith('/decks')) return 'decks'
  if (path.startsWith('/cards')) return 'cards'
  if (path.startsWith('/question-bank')) return 'bank'
  if (path.startsWith('/profile') || path.startsWith('/settings')) return 'profile'
  return null
})

/** The nav chrome is for signed-in screens only — `/auth` renders bare. */
const showNav = computed(() => auth.isAuthenticated && route.name !== 'auth')

function switchLocale(next: AppLocale) {
  setLocale(next)
}

function toggleProfileMenu() {
  isProfileMenuOpen.value = !isProfileMenuOpen.value
}

function closeProfileMenu() {
  isProfileMenuOpen.value = false
}

function handleLogoutClick() {
  closeProfileMenu()
  showLogoutConfirm.value = true
}

async function handleConfirmLogout() {
  auth.logout()
  await router.push({ name: 'auth' })
}

function handleDocumentClick(event: MouseEvent) {
  const target = event.target as HTMLElement
  if (!target.closest('.profile-dropdown-container')) {
    closeProfileMenu()
  }
}

onMounted(() => {
  document.addEventListener('click', handleDocumentClick)
})

onUnmounted(() => {
  document.removeEventListener('click', handleDocumentClick)
})
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
          <RouterLink
            :to="{ name: 'profile' }"
            class="nav-tab font-label"
            :class="{ 'nav-tab--active': activeTab === 'profile' }"
          >
            {{ t('profile.title') }}
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

          <!-- Profile Choice Dropdown Menu -->
          <div class="profile-dropdown-container">
            <button
              type="button"
              class="profile-btn font-label"
              :class="{ 'profile-btn--active': isProfileMenuOpen || activeTab === 'profile' }"
              @click.stop="toggleProfileMenu"
            >
              <span>👤 PLAYER_ONE</span>
              <span class="dropdown-arrow">▼</span>
            </button>

            <div v-if="isProfileMenuOpen" class="profile-dropdown font-label">
              <RouterLink
                :to="{ name: 'profile' }"
                class="dropdown-item"
                @click="closeProfileMenu"
              >
                {{ t('profile.title') }}
              </RouterLink>
              <RouterLink
                :to="{ name: 'settings' }"
                class="dropdown-item"
                @click="closeProfileMenu"
              >
                {{ t('profile.systemSettings') }}
              </RouterLink>
              <div class="dropdown-divider" />
              <button
                type="button"
                class="dropdown-item dropdown-item--danger"
                @click="handleLogoutClick"
              >
                [{{ t('nav.logout') }}]
              </button>
            </div>
          </div>
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

.profile-dropdown-container {
  position: relative;
}

.profile-btn {
  background: var(--surface-panel-border);
  border: 1px solid var(--surface-panel-border);
  color: var(--text-primary);
  font-size: var(--font-size-xs);
  letter-spacing: var(--tracking-normal);
  padding: var(--space-2) var(--space-4);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.profile-btn--active,
.profile-btn:hover {
  border-color: var(--color-accent);
  color: var(--color-accent);
}

.dropdown-arrow {
  font-size: 8px;
}

.profile-dropdown {
  position: absolute;
  right: 0;
  top: calc(100% + var(--space-2));
  background: var(--surface-panel);
  border: 2px solid var(--surface-panel-border);
  box-shadow: 0 8px 24px var(--ink);
  display: flex;
  flex-direction: column;
  min-width: 180px;
  z-index: 50;
}

.dropdown-item {
  padding: var(--space-4) var(--space-6);
  font-size: var(--font-size-xs);
  letter-spacing: var(--tracking-normal);
  color: var(--text-secondary);
  text-decoration: none;
  background: none;
  border: none;
  text-align: left;
  cursor: pointer;
  transition: background 0.15s ease, color 0.15s ease;
}

.dropdown-item:hover {
  background: var(--state-hover-surface);
  color: var(--color-accent);
}

.dropdown-item--danger {
  color: var(--status-danger);
}

.dropdown-item--danger:hover {
  background: var(--status-danger-subtle);
  color: var(--text-primary);
}

.dropdown-divider {
  height: 1px;
  background: var(--surface-panel-border);
  margin: var(--space-1) 0;
}

.nav-tab:focus-visible,
.lang-btn:focus-visible,
.profile-btn:focus-visible,
.dropdown-item:focus-visible {
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
