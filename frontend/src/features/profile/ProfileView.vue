<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';
import PixelFrame from '@/shared/components/PixelFrame.vue';
import AppButton from '@/shared/components/AppButton.vue';
import ConfirmDialog from '@/shared/components/ConfirmDialog.vue';
import { useAuthStore } from '@/features/auth/store/authStore';
import { apiFetch } from '@/utils/api';

const { t } = useI18n();
const router = useRouter();
const auth = useAuthStore();

const showLogoutConfirm = ref(false);
const isLoading = ref(true);

interface UserProfileData {
  username: string;
  email: string;
  level: number;
  totalXp: number;
  longestStreak: number;
  cardsLearned: number;
  examsCompleted: number;
}

const profileData = ref<UserProfileData>({
  username: 'PLAYER_ONE',
  email: 'player@linguflow.app',
  level: 12,
  totalXp: 12450,
  longestStreak: 14,
  cardsLearned: 480,
  examsCompleted: 24,
});

async function fetchProfile() {
  isLoading.value = true;
  try {
    const res = await apiFetch('/api/auth/me');
    if (res.ok) {
      const data = await res.json();
      profileData.value.username = data.username || data.email?.split('@')[0] || 'PLAYER_ONE';
      profileData.value.email = data.email || 'player@linguflow.app';
      if (data.xp !== undefined) {
        profileData.value.totalXp = data.xp;
        profileData.value.level = Math.max(1, Math.floor(data.xp / 1000) + 1);
      }
    }
  } catch (err) {
    console.error('Failed to fetch user profile:', err);
  } finally {
    isLoading.value = false;
  }
}

function handleGoToSettings() {
  void router.push({ name: 'settings' });
}

function handleLogoutClick() {
  showLogoutConfirm.value = true;
}

async function handleConfirmLogout() {
  auth.logout();
  await router.push({ name: 'auth' });
}

onMounted(() => {
  void fetchProfile();
});
</script>

<template>
  <div class="profile-view">
    <!-- Profile Header Cabinet -->
    <PixelFrame surface="cabinet" :ring-width="3" class="profile-header-frame">
      <div class="profile-header-inner">
        <!-- Avatar Container -->
        <div class="avatar-box">
          <div class="avatar-img-placeholder font-pixel">👾</div>
          <div class="avatar-level-badge font-pixel">
            {{ t('profile.level', { level: profileData.level }) }}
          </div>
        </div>

        <!-- Player Info -->
        <div class="player-info">
          <h1 class="player-name font-pixel">{{ profileData.username.toUpperCase() }}</h1>
          <div class="player-rank-badge font-label">
            {{ t('profile.rank') }}
          </div>
          <div class="player-meta font-body">
            <span class="meta-item">
              <span class="meta-icon" aria-hidden="true">✉</span> {{ profileData.email }}
            </span>
            <span class="meta-divider">|</span>
            <span class="meta-item">
              <span class="meta-icon" aria-hidden="true">📅</span> {{ t('profile.memberSince') }}
            </span>
          </div>
        </div>
      </div>
    </PixelFrame>

    <!-- Lifetime Stats Grid -->
    <section class="stats-grid">
      <div class="stat-card">
        <span class="stat-card-label font-label">{{ t('profile.stats.totalXp') }}</span>
        <span class="stat-card-value font-pixel text-accent">
          {{ profileData.totalXp.toLocaleString() }} XP
        </span>
      </div>

      <div class="stat-card">
        <span class="stat-card-label font-label">{{ t('profile.stats.longestStreak') }}</span>
        <span class="stat-card-value font-pixel text-danger">
          {{ t('profile.stats.longestStreakDays', { count: profileData.longestStreak }) }}
        </span>
      </div>

      <div class="stat-card">
        <span class="stat-card-label font-label">{{ t('profile.stats.cardsLearned') }}</span>
        <span class="stat-card-value font-pixel text-info">
          {{ t('profile.stats.cardsCount', { count: profileData.cardsLearned }) }}
        </span>
      </div>

      <div class="stat-card">
        <span class="stat-card-label font-label">{{ t('profile.stats.examsCompleted') }}</span>
        <span class="stat-card-value font-pixel text-success">
          {{ t('profile.stats.examsCount', { count: profileData.examsCompleted }) }}
        </span>
      </div>
    </section>

    <!-- Achievements & Medals Section -->
    <section class="achievements-section">
      <h2 class="achievements-title font-pixel">{{ t('profile.achievementsTitle') }}</h2>

      <div class="achievements-grid">
        <div class="achievement-card">
          <div class="achievement-icon" aria-hidden="true">🏆</div>
          <h3 class="achievement-name font-pixel">{{ t('profile.achievements.streakMaster') }}</h3>
          <p class="achievement-desc font-body">{{ t('profile.achievements.streakMasterDesc') }}</p>
        </div>

        <div class="achievement-card">
          <div class="achievement-icon" aria-hidden="true">⚡</div>
          <h3 class="achievement-name font-pixel">{{ t('profile.achievements.speedDemon') }}</h3>
          <p class="achievement-desc font-body">{{ t('profile.achievements.speedDemonDesc') }}</p>
        </div>

        <div class="achievement-card">
          <div class="achievement-icon" aria-hidden="true">🎯</div>
          <h3 class="achievement-name font-pixel">{{ t('profile.achievements.perfectScore') }}</h3>
          <p class="achievement-desc font-body">{{ t('profile.achievements.perfectScoreDesc') }}</p>
        </div>
      </div>
    </section>

    <!-- Bottom Action Buttons -->
    <section class="profile-actions">
      <AppButton variant="danger" class="action-btn" @click="handleLogoutClick">
        {{ t('nav.logout') }}
      </AppButton>
      <AppButton variant="secondary" class="action-btn">
        {{ t('profile.editProfile') }}
      </AppButton>
      <AppButton variant="primary" class="action-btn" @click="handleGoToSettings">
        {{ t('profile.systemSettings') }}
      </AppButton>
    </section>

    <!-- Logout Confirm Modal -->
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
.profile-view {
  display: flex;
  flex-direction: column;
  gap: var(--space-9);
  width: 100%;
}

.profile-header-frame {
  width: 100%;
}

.profile-header-inner {
  padding: var(--space-8);
  display: flex;
  align-items: center;
  gap: var(--space-8);
  flex-wrap: wrap;
}

.avatar-box {
  position: relative;
  width: 120px;
  height: 120px;
  border: var(--space-1) solid var(--surface-panel-border);
  background: var(--surface-page);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.avatar-img-placeholder {
  font-size: 48px;
}

.avatar-level-badge {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: var(--color-accent);
  color: var(--text-on-accent);
  font-size: var(--font-size-xs);
  text-align: center;
  padding: var(--space-1) 0;
  font-weight: 700;
}

.player-info {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  flex: 1;
}

.player-name {
  font-size: var(--font-size-xl);
  color: var(--color-accent);
  letter-spacing: var(--tracking-normal);
}

.player-rank-badge {
  display: inline-block;
  background: var(--surface-page);
  border: var(--space-1) solid var(--surface-panel-border);
  padding: var(--space-2) var(--space-4);
  color: var(--text-primary);
  font-size: var(--font-size-xs);
  width: fit-content;
  font-weight: 700;
}

.player-meta {
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
  display: flex;
  align-items: center;
  gap: var(--space-4);
  flex-wrap: wrap;
  margin-top: var(--space-2);
}

.meta-item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.meta-icon {
  font-size: var(--font-size-md);
}

.meta-divider {
  color: var(--surface-panel-border);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: var(--space-6);
}

.stat-card {
  background: var(--surface-panel);
  border: var(--space-1) solid var(--surface-panel-border);
  padding: var(--space-6);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  box-shadow: 0 4px 12px var(--ink);
}

.stat-card-label {
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
  letter-spacing: var(--tracking-wide);
  text-transform: uppercase;
}

.stat-card-value {
  font-size: var(--font-size-md);
}

.text-accent {
  color: var(--color-accent);
}

.text-danger {
  color: var(--status-danger);
}

.text-info {
  color: #62c0ff;
}

.text-success {
  color: var(--status-success);
}

.achievements-section {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.achievements-title {
  font-size: var(--font-size-lg);
  color: var(--text-primary);
  letter-spacing: var(--tracking-normal);
}

.achievements-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: var(--space-6);
}

.achievement-card {
  background: var(--surface-panel);
  border: var(--space-1) solid var(--surface-panel-border);
  padding: var(--space-6);
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: var(--space-3);
  position: relative;
  overflow: hidden;
  transition: border-color 0.15s ease;
}

.achievement-card:hover {
  border-color: var(--color-accent);
}

.achievement-icon {
  font-size: 36px;
}

.achievement-name {
  font-size: var(--font-size-sm);
  color: var(--text-primary);
  letter-spacing: var(--tracking-normal);
}

.achievement-desc {
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
  line-height: 1.4;
}

.profile-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-5);
  flex-wrap: wrap;
  margin-top: var(--space-4);
}

.action-btn {
  min-width: 140px;
}
</style>
