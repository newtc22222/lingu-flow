<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
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

const emit = defineEmits<{
  navigate: [view: 'flashcards' | 'manageDecks']
}>()

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

/**
 * Expected contract: GET /api/dashboard/progress ->
 * { totalXp, streakDays, examReadiness, worlds: [{ id, title, levels: [{id,index,status}], progressPercent, subLabel }] }
 * Locked/current/done level state must come from here — never hardcoded — so
 * this view has no fallback mock data; a failed fetch surfaces as an error.
 */
async function fetchProgress() {
  isLoading.value = true
  error.value = null
  try {
    const res = await apiFetch('/api/dashboard/progress')
    if (!res.ok) throw new Error('Request failed')
    progress.value = (await res.json()) as DashboardProgress
  } catch (err) {
    console.error('Failed to fetch dashboard progress:', err)
    error.value = 'Không thể tải dữ liệu tiến trình. Vui lòng thử lại sau.'
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  void fetchProgress()
})
</script>

<template>
  <div class="dashboard-view">
    <PixelFrame v-if="isLoading" surface="cabinet" :ring-width="3">
      <div class="dash-status font-label">▸ ĐANG TẢI TIẾN TRÌNH…</div>
    </PixelFrame>

    <div v-else-if="error" class="dash-error">
      <p class="dash-status dash-status--error font-label">{{ error }}</p>
      <AppButton variant="secondary" @click="fetchProgress">THỬ LẠI</AppButton>
    </div>

    <template v-else-if="progress">
      <PixelFrame surface="cabinet" :ring-width="3" class="hud-frame">
        <div class="hud-inner">
          <div class="hud-stats">
            <StatTile label="CHUỖI NGÀY" :value="progress.streakDays" icon="🔥" />
            <StatTile label="TỔNG XP" :value="progress.totalXp.toLocaleString('vi-VN')" />
            <div class="hud-meter">
              <span class="stat-label font-label">SẴN SÀNG THI</span>
              <div class="hud-meter-row">
                <div class="hud-meter-track">
                  <div class="hud-meter-fill" :style="{ width: `${progress.examReadiness}%` }" />
                </div>
                <span class="hud-meter-value font-pixel">{{ progress.examReadiness }}%</span>
              </div>
            </div>
          </div>

          <div v-if="currentLevel" class="hud-cta">
            <AppButton variant="primary" @click="emit('navigate', 'flashcards')">
              ▶ TIẾP TỤC — CẤP {{ currentLevel.index }}
            </AppButton>
            <span class="hud-cta-hint font-label">[ENTER]</span>
          </div>
        </div>
      </PixelFrame>

      <div v-if="progress.worlds.length === 0" class="dash-empty">
        <p class="font-label">CHƯA CÓ THẾ GIỚI NÀO</p>
        <p class="dash-empty-sub font-body">Tạo bộ thẻ đầu tiên để bắt đầu hành trình học tập.</p>
        <AppButton variant="primary" @click="emit('navigate', 'manageDecks')">TẠO BỘ THẺ</AppButton>
      </div>

      <div v-else class="worlds">
        <WorldCard
          v-for="world in progress.worlds"
          :key="world.id"
          :title="world.title"
          :levels="world.levels"
          :progress-percent="world.progressPercent"
          :sub-label="world.subLabel"
        />
      </div>
    </template>
  </div>
</template>

<style scoped>
.hud-frame {
  margin-bottom: var(--space-11);
}
.hud-inner {
  padding: var(--space-9);
  display: flex;
  flex-direction: column;
  gap: var(--space-9);
}
.hud-stats {
  display: flex;
  gap: var(--space-11);
  flex-wrap: wrap;
}
.hud-meter {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  flex: 1;
  min-width: 160px;
}
.stat-label {
  font-weight: 700;
  font-size: var(--font-size-xs);
  letter-spacing: var(--tracking-wide);
  text-transform: uppercase;
  color: var(--text-secondary);
}
.hud-meter-row {
  display: flex;
  align-items: center;
  gap: var(--space-6);
}
.hud-meter-track {
  flex: 1;
  height: 8px;
  background: var(--surface-page);
}
.hud-meter-fill {
  height: 100%;
  background: var(--status-success);
}
.hud-meter-value {
  font-size: var(--font-size-sm);
  color: var(--status-success);
  min-width: 40px;
  text-align: right;
}
.hud-cta {
  display: flex;
  align-items: center;
  gap: var(--space-7);
}
.hud-cta-hint {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  letter-spacing: var(--tracking-normal);
}
.worlds {
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
