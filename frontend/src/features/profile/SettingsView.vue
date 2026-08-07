<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import PixelFrame from '@/shared/components/PixelFrame.vue';
import AppButton from '@/shared/components/AppButton.vue';
import { SUPPORTED_LOCALES, setLocale, type AppLocale } from '@/i18n';
import { apiFetch } from '@/utils/api';

const { t, locale } = useI18n();

/** Saved state from the server (or defaults). */
interface SettingsState {
  locale: AppLocale;
  crtEnabled: boolean;
  dailyXpGoal: number;
  audioSfxEnabled: boolean;
  notificationsEnabled: boolean;
}

const savedSettings = ref<SettingsState>({
  locale: locale.value as AppLocale,
  crtEnabled: true,
  dailyXpGoal: 50,
  audioSfxEnabled: false,
  notificationsEnabled: false,
});

/** Buffered draft — only applied on explicit Save. */
const draftSettings = ref<SettingsState>({ ...savedSettings.value });

const isSaving = ref(false);
const saveSuccess = ref(false);
const isLoading = ref(true);

/** True when the draft differs from saved state. */
const hasChanges = computed(() => {
  return (
    draftSettings.value.locale !== savedSettings.value.locale ||
    draftSettings.value.crtEnabled !== savedSettings.value.crtEnabled ||
    draftSettings.value.dailyXpGoal !== savedSettings.value.dailyXpGoal
  );
});

async function fetchSettings() {
  isLoading.value = true;
  try {
    const res = await apiFetch('/api/settings');
    if (res.ok) {
      const data = await res.json();
      const loaded: SettingsState = {
        locale: data.locale ?? locale.value,
        crtEnabled: data.crtEnabled ?? true,
        dailyXpGoal: data.dailyXpGoal ?? 50,
        audioSfxEnabled: data.audioSfxEnabled ?? false,
        notificationsEnabled: data.notificationsEnabled ?? false,
      };
      savedSettings.value = { ...loaded };
      draftSettings.value = { ...loaded };
      
      // Apply the loaded locale immediately so the UI reflects the backend state
      if (loaded.locale !== locale.value) {
        locale.value = loaded.locale;
        setLocale(loaded.locale);
      }
    }
  } catch (err) {
    console.error('Failed to fetch settings:', err);
  } finally {
    isLoading.value = false;
  }
}

async function handleSave() {
  isSaving.value = true;
  saveSuccess.value = false;
  try {
    const res = await apiFetch('/api/settings', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        locale: draftSettings.value.locale,
        crtEnabled: draftSettings.value.crtEnabled,
        dailyXpGoal: draftSettings.value.dailyXpGoal,
      }),
    });
    if (res.ok) {
      const data = await res.json();
      const persisted: SettingsState = {
        locale: data.locale ?? draftSettings.value.locale,
        crtEnabled: data.crtEnabled ?? draftSettings.value.crtEnabled,
        dailyXpGoal: data.dailyXpGoal ?? draftSettings.value.dailyXpGoal,
        audioSfxEnabled: data.audioSfxEnabled ?? false,
        notificationsEnabled: data.notificationsEnabled ?? false,
      };
      savedSettings.value = { ...persisted };
      draftSettings.value = { ...persisted };

      // Apply locale change explicitly to the local i18n instance and globally
      locale.value = persisted.locale;
      setLocale(persisted.locale);

      saveSuccess.value = true;
      setTimeout(() => {
        saveSuccess.value = false;
      }, 3000);
    }
  } catch (err) {
    console.error('Failed to save settings:', err);
  } finally {
    isSaving.value = false;
  }
}

function handleReset() {
  draftSettings.value = { ...savedSettings.value };
}

function setDraftLocale(code: AppLocale) {
  draftSettings.value.locale = code;
}

function setDraftCrt(enabled: boolean) {
  draftSettings.value.crtEnabled = enabled;
}

onMounted(() => {
  void fetchSettings();
});
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
          ✔ {{ t('settings.savedMessage') }}
        </div>

        <!-- Section 1: Language & Display -->
        <section class="settings-section">
          <h2 class="section-title font-pixel">
            {{ t('settings.sections.languageAndTheme') }}
          </h2>

          <!-- Language Selector (buffered) -->
          <div class="setting-row">
            <span class="setting-label font-label">{{ t('settings.fields.language') }}</span>
            <div class="toggle-group" role="group">
              <button
                v-for="code in SUPPORTED_LOCALES"
                :key="code"
                type="button"
                class="toggle-btn font-label"
                :class="{ 'toggle-btn--active': draftSettings.locale === code }"
                @click="setDraftLocale(code)"
              >
                {{ code.toUpperCase() }}
              </button>
            </div>
          </div>

          <!-- CRT Scanlines (buffered) -->
          <div class="setting-row">
            <span class="setting-label font-label">{{ t('settings.fields.crtScanlines') }}</span>
            <div class="toggle-group" role="group">
              <button
                type="button"
                class="toggle-btn font-label"
                :class="{ 'toggle-btn--active': draftSettings.crtEnabled }"
                @click="setDraftCrt(true)"
              >
                {{ t('settings.options.on') }}
              </button>
              <button
                type="button"
                class="toggle-btn font-label"
                :class="{ 'toggle-btn--active': !draftSettings.crtEnabled }"
                @click="setDraftCrt(false)"
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

          <!-- Daily XP Goal (buffered) -->
          <div class="setting-field">
            <label class="setting-label font-label" for="daily-xp">
              {{ t('settings.fields.dailyGoal') }}
            </label>
            <div class="input-wrapper">
              <input
                id="daily-xp"
                v-model.number="draftSettings.dailyXpGoal"
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

        <!-- Action Buttons -->
        <footer class="settings-actions">
          <AppButton variant="secondary" class="action-btn" :disabled="!hasChanges" @click="handleReset">
            {{ t('settings.options.reset') }}
          </AppButton>
          <AppButton variant="primary" class="action-btn" :disabled="!hasChanges || isSaving" @click="handleSave">
            {{ isSaving ? t('common.loading') : t('settings.options.save') }}
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
