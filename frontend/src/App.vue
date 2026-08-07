<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRoute, useRouter } from 'vue-router';
import { useAuthStore } from '@/features/auth/store/authStore';
import ConfirmDialog from '@/shared/components/ConfirmDialog.vue';
import AppFooter from '@/shared/components/AppFooter.vue';

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();
const { t } = useI18n();

const showLogoutConfirm = ref(false);
const isProfileMenuOpen = ref(false);
const isMobileMenuOpen = ref(false);

/** Which arcade tab reads as active. */
const activeTab = computed<
  'dashboard' | 'exams' | 'flashcards' | 'decks' | 'cards' | 'bank' | 'profile' | null
>(() => {
  const path = route.path;
  if (path.startsWith('/dashboard')) return 'dashboard';
  if (path.startsWith('/exams')) return 'exams';
  if (path.startsWith('/flashcards')) return 'flashcards';
  if (path.startsWith('/decks')) return 'decks';
  if (path.startsWith('/cards')) return 'cards';
  if (path.startsWith('/question-bank')) return 'bank';
  if (path.startsWith('/profile') || path.startsWith('/settings')) return 'profile';
  return null;
});

/** The nav chrome is for signed-in screens only — `/auth` renders bare. */
const showNav = computed(() => auth.isAuthenticated && route.name !== 'auth');

function toggleProfileMenu() {
  isProfileMenuOpen.value = !isProfileMenuOpen.value;
}

function closeProfileMenu() {
  isProfileMenuOpen.value = false;
}

function toggleMobileMenu() {
  isMobileMenuOpen.value = !isMobileMenuOpen.value;
}

function closeMobileMenu() {
  isMobileMenuOpen.value = false;
}

function handleLogoutClick() {
  closeProfileMenu();
  closeMobileMenu();
  showLogoutConfirm.value = true;
}

async function handleConfirmLogout() {
  auth.logout();
  await router.push({ name: 'auth' });
}

function handleDocumentClick(event: MouseEvent) {
  const target = event.target as HTMLElement;
  if (!target.closest('.profile-dropdown-container')) {
    closeProfileMenu();
  }
  if (!target.closest('.mobile-menu') && !target.closest('.hamburger-btn')) {
    closeMobileMenu();
  }
}

onMounted(() => {
  document.addEventListener('click', handleDocumentClick);
});

onUnmounted(() => {
  document.removeEventListener('click', handleDocumentClick);
});
</script>

<template>
  <div class="h-screen w-screen bg-ink text-phosphor flex flex-col overflow-hidden">
    <!-- Top Navigation Header -->
    <header v-if="showNav" class="app-header">
      <div class="nav-container">
        <!-- Logo / Wordmark (Left) -->
        <RouterLink :to="{ name: 'dashboard' }" class="nav-logo font-pixel"> LINGUFLOW </RouterLink>

        <!-- Navigation Tabs (Center, hidden on mobile) -->
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
          <!-- Profile Choice Dropdown Menu (Desktop) -->
          <div class="profile-dropdown-container desktop-only">
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
              <RouterLink :to="{ name: 'profile' }" class="dropdown-item" @click="closeProfileMenu">
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

          <!-- Hamburger Menu Toggle (Mobile) -->
          <button
            type="button"
            class="hamburger-btn mobile-only font-label"
            :aria-label="t('nav.menu')"
            @click.stop="toggleMobileMenu"
          >
            <span v-if="!isMobileMenuOpen">☰</span>
            <span v-else>✕</span>
          </button>
        </div>
      </div>

      <!-- Mobile Navigation Menu -->
      <div v-if="isMobileMenuOpen" class="mobile-menu font-label">
        <RouterLink
          :to="{ name: 'dashboard' }"
          class="mobile-menu-item"
          :class="{ 'mobile-menu-item--active': activeTab === 'dashboard' }"
          @click="closeMobileMenu"
        >
          {{ t('nav.dashboard') }}
        </RouterLink>
        <RouterLink
          :to="{ name: 'exams' }"
          class="mobile-menu-item"
          :class="{ 'mobile-menu-item--active': activeTab === 'exams' }"
          @click="closeMobileMenu"
        >
          {{ t('nav.examMode') }}
        </RouterLink>
        <RouterLink
          :to="{ name: 'flashcards' }"
          class="mobile-menu-item"
          :class="{ 'mobile-menu-item--active': activeTab === 'flashcards' }"
          @click="closeMobileMenu"
        >
          {{ t('nav.flashcards') }}
        </RouterLink>
        <RouterLink
          :to="{ name: 'decks' }"
          class="mobile-menu-item"
          :class="{ 'mobile-menu-item--active': activeTab === 'decks' }"
          @click="closeMobileMenu"
        >
          {{ t('nav.manageDecks') }}
        </RouterLink>
        <RouterLink
          :to="{ name: 'question-bank' }"
          class="mobile-menu-item"
          :class="{ 'mobile-menu-item--active': activeTab === 'bank' }"
          @click="closeMobileMenu"
        >
          {{ t('nav.questionBank') }}
        </RouterLink>
        <div class="mobile-menu-divider" />
        <RouterLink
          :to="{ name: 'profile' }"
          class="mobile-menu-item"
          :class="{ 'mobile-menu-item--active': activeTab === 'profile' }"
          @click="closeMobileMenu"
        >
          👤 {{ t('profile.title') }}
        </RouterLink>
        <RouterLink
          :to="{ name: 'settings' }"
          class="mobile-menu-item"
          @click="closeMobileMenu"
        >
          ⚙ {{ t('profile.systemSettings') }}
        </RouterLink>
        <button
          type="button"
          class="mobile-menu-item mobile-menu-item--danger"
          @click="handleLogoutClick"
        >
          [{{ t('nav.logout') }}]
        </button>
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
}

.nav-logo {
  font-size: var(--font-size-md);
  color: var(--color-accent);
  letter-spacing: var(--tracking-normal);
  text-decoration: none;
  flex-shrink: 0;
}

.nav-logo:hover {
  opacity: 0.9;
}

.nav-tabs {
  display: none;
  gap: var(--space-2);
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
  transition:
    color 0.15s ease,
    border-color 0.15s ease;
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

/* Desktop profile dropdown — hidden on mobile */
.desktop-only {
  display: none;
}

/* Hamburger — shown on mobile only */
.mobile-only {
  display: block;
}

.hamburger-btn {
  background: none;
  border: 1px solid var(--surface-panel-border);
  color: var(--text-primary);
  font-size: var(--font-size-lg);
  padding: var(--space-2) var(--space-4);
  cursor: pointer;
  line-height: 1;
}

.hamburger-btn:hover {
  border-color: var(--color-accent);
  color: var(--color-accent);
}

/* Mobile slide-down menu */
.mobile-menu {
  background: var(--surface-panel);
  border-top: 1px solid var(--surface-panel-border);
  padding: var(--space-4) 0;
  display: flex;
  flex-direction: column;
}

.mobile-menu-item {
  padding: var(--space-4) var(--space-8);
  font-size: var(--font-size-xs);
  letter-spacing: var(--tracking-wide);
  color: var(--text-secondary);
  text-decoration: none;
  text-transform: uppercase;
  background: none;
  border: none;
  text-align: left;
  cursor: pointer;
  transition: background 0.15s ease, color 0.15s ease;
}

.mobile-menu-item:hover,
.mobile-menu-item--active {
  background: var(--state-hover-surface);
  color: var(--color-accent);
}

.mobile-menu-item--danger {
  color: var(--status-danger);
}

.mobile-menu-item--danger:hover {
  background: var(--status-danger-subtle);
  color: var(--text-primary);
}

.mobile-menu-divider {
  height: 1px;
  background: var(--surface-panel-border);
  margin: var(--space-2) var(--space-8);
}

/* Profile dropdown (desktop) */
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
  transition:
    background 0.15s ease,
    color 0.15s ease;
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

/* Focus visible states */
.nav-tab:focus-visible,
.profile-btn:focus-visible,
.dropdown-item:focus-visible,
.hamburger-btn:focus-visible,
.mobile-menu-item:focus-visible {
  outline: var(--focus-ring-width) solid var(--color-focus-ring);
  outline-offset: 2px;
}

/* Responsive breakpoint: show desktop nav on md+ */
@media (min-width: 768px) {
  .nav-tabs {
    display: flex;
  }

  .desktop-only {
    display: block;
  }

  .mobile-only {
    display: none;
  }
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
