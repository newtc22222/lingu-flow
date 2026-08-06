<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/features/auth/store/authStore'
import { SUPPORTED_LOCALES, setLocale, type AppLocale } from '@/i18n'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const { t, locale } = useI18n()

/** Which arcade tab reads as active — every exam sub-route lights up EXAM MODE. */
const activeTab = computed<'exams' | 'flashcards' | 'dashboard' | null>(() => {
  const path = route.path
  if (path.startsWith('/exams')) return 'exams'
  if (path.startsWith('/flashcards')) return 'flashcards'
  if (path.startsWith('/dashboard')) return 'dashboard'
  return null
})

/** The nav chrome is for signed-in screens only — `/auth` renders bare. */
const showNav = computed(() => auth.isAuthenticated && route.name !== 'auth')

function switchLocale(next: AppLocale) {
  setLocale(next)
}

async function logout() {
  auth.logout()
  await router.push({ name: 'auth' })
}
</script>

<template>
  <div class="h-screen w-screen bg-ink text-phosphor flex flex-col overflow-hidden">
    <nav
      v-if="showNav"
      class="bg-cabinet px-4 py-3 flex flex-wrap justify-between items-center gap-3 border-b border-cabinet-light z-10 shrink-0"
    >
      <div class="tabs">
        <RouterLink
          :to="{ name: 'exams' }"
          class="tab font-label"
          :class="{ 'tab--active': activeTab === 'exams' }"
        >
          {{ t('nav.examMode') }}
        </RouterLink>
        <RouterLink
          :to="{ name: 'flashcards' }"
          class="tab font-label"
          :class="{ 'tab--active': activeTab === 'flashcards' }"
        >
          {{ t('nav.flashcards') }}
        </RouterLink>
        <RouterLink
          :to="{ name: 'dashboard' }"
          class="tab font-label"
          :class="{ 'tab--active': activeTab === 'dashboard' }"
        >
          {{ t('nav.dashboard') }}
        </RouterLink>
      </div>
      <div class="flex gap-4 items-center font-label text-xs">
        <RouterLink :to="{ name: 'decks' }" class="util-link">{{ t('nav.manageDecks') }}</RouterLink>
        <RouterLink :to="{ name: 'cards' }" class="util-link">{{ t('nav.manageCards') }}</RouterLink>
        <RouterLink :to="{ name: 'question-bank' }" class="util-link">
          {{ t('nav.questionBank') }}
        </RouterLink>

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

        <button type="button" class="util-link util-link--danger" @click="logout">
          {{ t('nav.logout') }}
        </button>
      </div>
    </nav>

    <div class="flex-1 overflow-y-auto relative">
      <RouterView v-slot="{ Component, route: current }">
        <!-- Exam results/creator own their full-bleed layout; every other view
             sits inside the centered arcade cabinet column. -->
        <component :is="Component" v-if="current.meta.fullBleed" />
        <div v-else class="arcade-app">
          <component :is="Component" />
        </div>
      </RouterView>
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
  letter-spacing: var(--tracking-tight);
  padding: var(--space-6) var(--space-7);
  background: var(--surface-panel);
  color: var(--text-secondary);
  border: none;
  cursor: pointer;
  text-decoration: none;
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
  letter-spacing: var(--tracking-tight);
  cursor: pointer;
  padding: var(--space-2) 0;
  text-decoration: none;
}
.util-link:hover {
  color: var(--text-primary);
}
.util-link--danger:hover {
  color: var(--status-danger);
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
.tab:focus-visible,
.util-link:focus-visible,
.lang-btn:focus-visible {
  outline: var(--focus-ring-width) solid var(--color-focus-ring);
  outline-offset: 2px;
}
.arcade-app {
  max-width: 920px;
  margin: 0 auto;
  /* stylelint-disable-next-line scale-unlimited/declaration-strict-value -- approved Step 2 - layout one-off, see design-tokens.json notes */
  padding: 28px var(--space-9) 60px;
}
</style>
