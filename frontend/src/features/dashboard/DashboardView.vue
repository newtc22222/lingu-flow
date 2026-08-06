<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { apiFetch } from '@/utils/api'
import PixelFrame from '@/shared/components/PixelFrame.vue'
import AppButton from '@/shared/components/AppButton.vue'
import StatTile from './components/StatTile.vue'
import WorldCard, { type LevelProgress } from './components/WorldCard.vue'

interface WorldProgress {
  id: string
  title: string
  levels: LevelProgress[]
  progressPercent: number
  subLabel: string
}

interface DashboardProgress {
  totalXp: number
  streakDays: number
  examReadiness: number
  worlds: WorldProgress[]
}

const { t } = useI18n()
const router = useRouter()

const isLoading = ref(true)
const error = ref<string | null>(null)
const progress = ref<DashboardProgress | null>(null)

/** First not-yet-finished level across all worlds, in world order — where "CONTINUE" resumes. */
const currentLevel = computed(() => {
  for (const world of progress.value?.worlds ?? []) {
    const level = world.levels.find((l) => l.status === 'current')
    if (level) return level
  }
  return null
})

async function fetchProgress() {
  isLoading.value = true
  error.value = null
  try {
    const res = await apiFetch('/api/dashboard/progress')
    if (!res.ok) throw new Error('Request failed')
    progress.value = (await res.json()) as DashboardProgress
  } catch (err) {
    console.error('Failed to fetch dashboard progress:', err)
    error.value = t('dashboard.error')
  } finally {
    isLoading.value = false
  }
}

function handleContinueCta() {
  void router.push({ name: 'flashcards' })
}

onMounted(() => {
  void fetchProgress()
})
</script>

<template>
  <div class="dashboard-view">
    <!-- Ambient CRT Scanline Overlay -->
    <div class="dash-scanlines" aria-hidden="true" />

    <PixelFrame v-if="isLoading" surface="cabinet" :ring-width="3">
      <div class="dash-status font-label">{{ t('dashboard.loading') }}</div>
    </PixelFrame>

    <div v-else-if="error" class="dash-error">
      <p class="dash-status dash-status--error font-label">{{ error }}</p>
      <AppButton variant="secondary" @click="fetchProgress">{{ t('common.retry') }}</AppButton>
    </div>

    <template v-else-if="progress">
      <!-- Command Center HUD Box -->
      <section class="command-center-cabinet">
        <!-- Corner Bolt Accents -->
        <div class="screw screw-tl" aria-hidden="true" />
        <div class="screw screw-tr" aria-hidden="true" />
        <div class="screw screw-bl" aria-hidden="true" />
        <div class="screw screw-br" aria-hidden="true" />

        <header class="command-header">
          <h2 class="command-title font-pixel">{{ t('dashboard.commandCenter') }}</h2>
        </header>

        <div class="command-stats-grid">
          <StatTile
            :label="t('dashboard.streak')"
            :value="t('dashboard.streakDays', { count: progress.streakDays })"
            icon="🔥"
            accentColor="var(--amber)"
          />
          <StatTile
            :label="t('dashboard.totalXp')"
            :value="progress.totalXp.toLocaleString()"
            icon="⚡"
            accentColor="var(--status-success)"
          />

          <!-- Exam Readiness Meter -->
          <div class="readiness-well">
            <span class="readiness-label font-label">{{ t('dashboard.examReadiness') }}</span>
            <div class="readiness-track">
              <div class="readiness-fill" :style="{ width: `${progress.examReadiness}%` }" />
              <span class="readiness-value font-pixel">{{ progress.examReadiness }}%</span>
            </div>
          </div>
        </div>

        <div v-if="currentLevel" class="command-cta-container">
          <AppButton variant="primary" class="command-cta-btn" @click="handleContinueCta">
            <span>{{ t('dashboard.continueLevel', { level: currentLevel.index }) }}</span>
            <span class="cta-badge font-label">[ENTER]</span>
          </AppButton>
        </div>
      </section>

      <!-- Stage Select & Worlds Section -->
      <section class="worlds-section">
        <h2 class="worlds-heading font-pixel">{{ t('dashboard.stageSelectTitle') }}</h2>

        <div v-if="progress.worlds.length === 0" class="dash-empty">
          <p class="font-label">{{ t('dashboard.emptyTitle') }}</p>
          <p class="dash-empty-sub font-body">{{ t('dashboard.emptySub') }}</p>
          <AppButton variant="primary" @click="router.push({ name: 'decks' })">
            {{ t('dashboard.createDeck') }}
          </AppButton>
        </div>

        <div v-else class="worlds-list">
          <WorldCard
            v-for="world in progress.worlds"
            :key="world.id"
            :title="world.title"
            :levels="world.levels"
            :progress-percent="world.progressPercent"
            :sub-label="world.subLabel"
          />
        </div>
      </section>
    </template>
  </div>
</template>

<style scoped>
.dashboard-view {
  display: flex;
  flex-direction: column;
  gap: var(--space-10);
  position: relative;
  width: 100%;
}

/* stylelint-disable-next-line function-disallowed-list -- ambient CRT scanlines */
.dash-scanlines {
  background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%);
  background-size: 100% 2px;
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 50;
  opacity: 0.2;
}

.command-center-cabinet {
  background: var(--surface-panel);
  border: var(--border-width-accent) solid var(--color-accent);
  padding: var(--space-8);
  position: relative;
  display: flex;
  flex-direction: column;
  gap: var(--space-7);
  box-shadow: 0 8px 24px var(--ink);
}

.screw {
  position: absolute;
  width: var(--space-4);
  height: var(--space-4);
  background: var(--color-accent);
  border: 1px solid var(--surface-page);
  z-index: 10;
}

.screw-tl {
  top: var(--space-2);
  left: var(--space-2);
}

.screw-tr {
  top: var(--space-2);
  right: var(--space-2);
}

.screw-bl {
  bottom: var(--space-2);
  left: var(--space-2);
}

.screw-br {
  bottom: var(--space-2);
  right: var(--space-2);
}

.command-header {
  border-bottom: 1px solid var(--surface-panel-border);
  padding-bottom: var(--space-4);
}

.command-title {
  font-size: var(--font-size-md);
  color: var(--color-accent);
  letter-spacing: var(--tracking-normal);
}

.command-stats-grid {
  display: flex;
  gap: var(--space-6);
  flex-wrap: wrap;
}

.readiness-well {
  background: var(--surface-page);
  border: var(--space-1) solid var(--surface-panel-border);
  padding: var(--space-6) var(--space-7);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-4);
  flex: 1.5;
  min-width: 200px;
}

.readiness-label {
  font-weight: 700;
  font-size: var(--font-size-xs);
  letter-spacing: var(--tracking-wide);
  text-transform: uppercase;
  color: var(--text-secondary);
}

.readiness-track {
  width: 100%;
  height: 24px;
  background: var(--surface-panel-border);
  border: 1px solid var(--cabinet);
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.readiness-fill {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  background: var(--status-success);
  transition: width 0.3s ease;
}

.readiness-value {
  position: relative;
  z-index: 10;
  font-size: var(--font-size-sm);
  color: var(--text-on-accent);
  text-shadow: 0 1px 2px var(--ink);
}

.command-cta-container {
  width: 100%;
}

.command-cta-btn {
  width: 100%;
  padding: var(--space-6) var(--space-8);
  font-size: var(--font-size-md);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-4);
}

.cta-badge {
  font-size: var(--font-size-xs);
  opacity: 0.85;
}

.worlds-section {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.worlds-heading {
  font-size: var(--font-size-lg);
  color: var(--text-primary);
  letter-spacing: var(--tracking-normal);
}

.worlds-list {
  display: flex;
  flex-direction: column;
}

.dash-status {
  color: var(--text-secondary);
  font-size: var(--font-size-md);
  text-align: center;
  padding: var(--space-9);
}

.dash-status--error {
  color: var(--status-danger);
}

.dash-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-8);
  padding: var(--space-9) 0;
}

.dash-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-6);
  text-align: center;
  padding: var(--space-11) 0;
  color: var(--text-primary);
}

.dash-empty-sub {
  color: var(--text-secondary);
  font-size: var(--font-size-md);
}
</style>
