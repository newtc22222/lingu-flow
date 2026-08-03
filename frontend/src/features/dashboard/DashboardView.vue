<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { apiFetch } from '@/utils/api'
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

const isLoading = ref(true)
const error = ref<string | null>(null)
const progress = ref<DashboardProgress | null>(null)

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
    <div v-if="isLoading" class="dash-status font-label">▸ ĐANG TẢI TIẾN TRÌNH…</div>
    <div v-else-if="error" class="dash-status dash-status--error font-label">{{ error }}</div>

    <template v-else-if="progress">
      <div class="stats-row">
        <div class="stat-wrap">
          <StatTile label="TỔNG XP" :value="progress.totalXp.toLocaleString('vi-VN')" />
        </div>
        <div class="stat-wrap">
          <StatTile label="CHUỖI NGÀY" :value="progress.streakDays" />
        </div>
        <div class="stat-wrap">
          <StatTile label="SẴN SÀNG THI" :value="`${progress.examReadiness}%`" accent="green" />
        </div>
      </div>

      <div class="worlds">
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
.stats-row {
  display: flex;
  gap: 14px;
  margin-bottom: 26px;
  flex-wrap: wrap;
}
.stat-wrap {
  flex: 1;
  min-width: 140px;
}
.worlds {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
}
.dash-status {
  color: var(--muted);
  font-size: 13px;
  text-align: center;
  padding: 40px 0;
}
.dash-status--error {
  color: var(--red);
}
</style>
