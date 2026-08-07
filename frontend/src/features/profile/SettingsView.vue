<script setup lang="ts">
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';
import PixelFrame from '@/shared/components/PixelFrame.vue';
import AppButton from '@/shared/components/AppButton.vue';
import { SUPPORTED_LOCALES, setLocale, type AppLocale } from '@/i18n';

const { t, locale } = useI18n();
const router = useRouter();

const isCrtEnabled = ref(true);
const dailyXpGoal = ref(50);
const saveSuccess = ref(false);

function switchLocale(next: AppLocale) {
  setLocale(next);
}

function toggleCrt(enabled: boolean) {
  isCrtEnabled.value = enabled;
}

function handleSave() {
  saveSuccess.value = true;
  setTimeout(() => {
    saveSuccess.value = false;
  }, 3000);
}

function handleCancel() {
  void router.push({ name: 'profile' });
}
</script>

<template>
  <div class="settings-view">
    <h1 class="settings-title font-pixel">{{ t('settings.title') }}</h1>

    <PixelFrame surface="cabinet" :ring-width="3" class="settings-cabinet">
      <div class="settings-inner">
        <!-- Corner Stud Accents -->
        <div class="stud stud-tl" aria-hidden="true" />
        <div class="stud stud-tr" aria-hidden="true" />
        <div class="stud stud-bl" aria-hidden="true" />
        <div class="stud stud-br" aria-hidden="true" />

        <!-- Notification Banner -->
        <div v-if="saveSuccess" class="settings-banner font-label">
          ✔ SETTINGS SAVED SUCCESSFULLY
        </div>

        <!-- Section 1: Language & Display -->
        <section class="settings-section">
          <h2 class="section-title font-pixel">
            {{ t('settings.sections.languageAndTheme') }}
          </h2>

          <!-- Language Selector -->
          <div class="setting-row">
            <span class="setting-label font-label">{{ t('settings.fields.language') }}</span>
            <div class="toggle-group" role="group">
              <button
                v-for="code in SUPPORTED_LOCALES"
                :key="code"
                type="button"
                class="toggle-btn font-label"
                :class="{ 'toggle-btn--active': locale === code }"
                @click="switchLocale(code)"
              >
                {{ code.toUpperCase() }}
              </button>
            </div>
          </div>

          <!-- CRT Scanlines -->
          <div class="setting-row">
            <span class="setting-label font-label">{{ t('settings.fields.crtScanlines') }}</span>
            <div class="toggle-group" role="group">
              <button
                type="button"
                class="toggle-btn font-label"
                :class="{ 'toggle-btn--active': isCrtEnabled }"
                @click="toggleCrt(true)"
              >
                {{ t('settings.options.on') }}
              </button>
              <button
                type="button"
                class="toggle-btn font-label"
                :class="{ 'toggle-btn--active': !isCrtEnabled }"
                @click="toggleCrt(false)"
              >
                {{ t('settings.options.off') }}
              </button>
            </div>
          </div>

          <!-- 8-Bit Audio SFX (Disabled Feature) -->
          <div class="setting-row setting-row--disabled">
            <div class="setting-label-box">
              <span class="setting-label font-label">{{ t('settings.fields.audioSfx') }}</span>
              <span class="disabled-badge font-label"
                >[{{ t('settings.options.notAvailable') }}]</span
              >
            </div>
            <div class="toggle-group" role="group">
              <button type="button" disabled class="toggle-btn toggle-btn--disabled font-label">
                {{ t('settings.options.off') }}
              </button>
            </div>
          </div>
        </section>

        <!-- Section 2: Learning Goals -->
        <section class="settings-section">
          <h2 class="section-title font-pixel">
            {{ t('settings.sections.learningGoals') }}
          </h2>

          <!-- Daily XP Goal -->
          <div class="setting-field">
            <label class="setting-label font-label" for="daily-xp">
              {{ t('settings.fields.dailyGoal') }}
            </label>
            <div class="input-wrapper">
              <input
                id="daily-xp"
                v-model.number="dailyXpGoal"
                type="text"
                class="arcade-input setting-input font-pixel"
              />
              <span class="input-suffix font-label">XP / DAY</span>
            </div>
          </div>

          <!-- Reminder Notifications (Disabled Feature) -->
          <div class="setting-row setting-row--disabled">
            <div class="setting-label-box">
              <span class="setting-label font-label">{{ t('settings.fields.notifications') }}</span>
              <span class="disabled-badge font-label"
                >[{{ t('settings.options.notAvailable') }}]</span
              >
            </div>
            <div class="toggle-group" role="group">
              <button type="button" disabled class="toggle-btn toggle-btn--disabled font-label">
                {{ t('settings.options.off') }}
              </button>
            </div>
          </div>
        </section>

        <!-- Section 3: Account & Security -->
        <section class="settings-section">
          <h2 class="section-title font-pixel">
            {{ t('settings.sections.accountAndSecurity') }}
          </h2>

          <div class="setting-row">
            <span class="setting-label font-label">{{ t('settings.fields.password') }}</span>
            <AppButton variant="edit" class="password-btn">
              {{ t('settings.options.changePassword') }}
            </AppButton>
          </div>
        </section>

        <!-- Action Buttons -->
        <footer class="settings-actions">
          <AppButton variant="secondary" class="action-btn" @click="handleCancel">
            {{ t('settings.options.cancel') }}
          </AppButton>
          <AppButton variant="primary" class="action-btn" @click="handleSave">
            {{ t('settings.options.save') }}
          </AppButton>
        </footer>
      </div>
    </PixelFrame>
  </div>
</template>

<style scoped>
.settings-view {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-8);
  width: 100%;
}

.settings-title {
  font-size: var(--font-size-xl);
  color: var(--color-accent);
  letter-spacing: var(--tracking-normal);
  text-align: center;
}

.settings-cabinet {
  width: 100%;
  max-width: 680px;
}

.settings-inner {
  padding: var(--space-8);
  display: flex;
  flex-direction: column;
  gap: var(--space-8);
  position: relative;
}

.stud {
  position: absolute;
  width: 8px;
  height: 8px;
  background: var(--color-accent);
  border: 1px solid var(--surface-page);
  z-index: 10;
}

.stud-tl {
  top: var(--space-3);
  left: var(--space-3);
}

.stud-tr {
  top: var(--space-3);
  right: var(--space-3);
}

.stud-bl {
  bottom: var(--space-3);
  left: var(--space-3);
}

.stud-br {
  bottom: var(--space-3);
  right: var(--space-3);
}

.settings-banner {
  background: var(--surface-page);
  border-left: var(--border-width-accent) solid var(--status-success);
  padding: var(--space-4) var(--space-6);
  color: var(--status-success);
  font-size: var(--font-size-sm);
}

.settings-section {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.section-title {
  font-size: var(--font-size-sm);
  color: var(--text-primary);
  border-bottom: 1px solid var(--surface-panel-border);
  padding-bottom: var(--space-3);
  letter-spacing: var(--tracking-normal);
}

.setting-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--surface-page);
  border: 1px solid var(--surface-panel-border);
  padding: var(--space-5) var(--space-6);
  gap: var(--space-4);
  flex-wrap: wrap;
}

.setting-row--disabled {
  opacity: 0.6;
}

.setting-label-box {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.setting-label {
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
  letter-spacing: var(--tracking-wide);
  text-transform: uppercase;
}

.disabled-badge {
  font-size: var(--font-size-2xs);
  color: var(--status-danger);
  letter-spacing: var(--tracking-tight);
}

.toggle-group {
  display: flex;
  gap: var(--space-2);
}

.toggle-btn {
  background: var(--surface-panel-border);
  border: none;
  color: var(--text-secondary);
  font-size: var(--font-size-xs);
  letter-spacing: var(--tracking-wide);
  padding: var(--space-3) var(--space-5);
  cursor: pointer;
  transition:
    background 0.15s ease,
    color 0.15s ease;
}

.toggle-btn--active {
  background: var(--state-selected-bg);
  color: var(--text-on-accent);
  font-weight: 700;
}

.toggle-btn--disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.setting-field {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.input-wrapper {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.setting-input {
  background: var(--surface-page);
  border: 1px solid var(--surface-panel-border);
  color: var(--color-accent);
  padding: var(--space-4) var(--space-6);
  font-size: var(--font-size-sm);
  max-width: 160px;
}

.input-suffix {
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
}

.password-btn {
  font-size: var(--font-size-xs);
}

.settings-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-5);
  padding-top: var(--space-4);
  border-top: 1px solid var(--surface-panel-border);
}

.action-btn {
  min-width: 120px;
}
</style>
