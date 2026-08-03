<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { apiFetch } from '@/utils/api'
import PixelFrame from '@/shared/components/PixelFrame.vue'
import AppButton from '@/shared/components/AppButton.vue'
import ManageListShell from '@/shared/components/ManageListShell.vue'

interface Deck {
  id: string
  name: string
  description: string
}

const decks = ref<Deck[]>([])
const isLoading = ref(true)
const isEditing = ref(false)
const editingDeckId = ref<string | null>(null)

const form = ref({
  name: '',
  description: '',
})

const fetchDecks = async () => {
  isLoading.value = true
  try {
    const res = await apiFetch('/api/decks')
    const raw = (await res.json()) as Record<string, unknown>[]
    decks.value = raw.map((d) => ({
      id: (d.id ?? d._id) as string,
      name: d.name as string,
      description: (d.description as string) ?? '',
    }))
  } catch (error) {
    console.error('Failed to fetch decks:', error)
  } finally {
    isLoading.value = false
  }
}

const saveDeck = async () => {
  try {
    if (isEditing.value && editingDeckId.value) {
      await apiFetch(`/api/decks/${editingDeckId.value}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form.value),
      })
    } else {
      await apiFetch('/api/decks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form.value),
      })
    }

    form.value = { name: '', description: '' }
    isEditing.value = false
    editingDeckId.value = null
    await fetchDecks()
  } catch (error) {
    console.error('Failed to save deck:', error)
  }
}

const editDeck = (deck: Deck) => {
  form.value = { name: deck.name, description: deck.description || '' }
  isEditing.value = true
  editingDeckId.value = deck.id
}

const deleteDeck = async (id: string) => {
  if (!confirm('Bạn có chắc muốn xóa bộ thẻ này?')) return
  try {
    await apiFetch(`/api/decks/${id}`, { method: 'DELETE' })
    await fetchDecks()
  } catch (error) {
    console.error('Failed to delete deck:', error)
  }
}

const cancelEdit = () => {
  form.value = { name: '', description: '' }
  isEditing.value = false
  editingDeckId.value = null
}

onMounted(() => {
  fetchDecks()
})
</script>

<template>
  <ManageListShell
    title="QUẢN LÝ BỘ THẺ"
    count-label="BỘ"
    :count="decks.length"
    :is-loading="isLoading"
    loading-text="▸ ĐANG TẢI BỘ THẺ…"
    empty-text="CHƯA CÓ BỘ THẺ NÀO. TẠO BỘ THẺ ĐẦU TIÊN Ở TRÊN."
    :rows="decks"
    @edit="editDeck"
    @delete="deleteDeck"
  >
    <template #form>
      <PixelFrame frame-color="amber" surface="cabinet" :ring-width="3" class="deck-form-frame">
        <form class="deck-form" @submit.prevent="saveDeck">
          <h3 class="form-title font-label">{{ isEditing ? 'CHỈNH SỬA BỘ THẺ' : 'TẠO BỘ THẺ MỚI' }}</h3>

          <div class="arcade-field">
            <label class="arcade-label" for="deck-name">TÊN BỘ THẺ</label>
            <input
              id="deck-name"
              v-model="form.name"
              required
              type="text"
              class="arcade-input"
              placeholder="VD: Từ vựng tiếng Tây Ban Nha"
            />
          </div>

          <div class="arcade-field">
            <label class="arcade-label" for="deck-desc">MÔ TẢ (TÙY CHỌN)</label>
            <input
              id="deck-desc"
              v-model="form.description"
              type="text"
              class="arcade-input"
              placeholder="VD: 1000 từ thông dụng nhất"
            />
          </div>

          <div class="form-actions">
            <AppButton v-if="isEditing" variant="secondary" type="button" @click="cancelEdit">HỦY</AppButton>
            <AppButton type="submit">{{ isEditing ? 'CẬP NHẬT' : 'LƯU BỘ THẺ' }}</AppButton>
          </div>
        </form>
      </PixelFrame>
    </template>

    <template #row="{ item }">
      <div class="deck-row-name font-body">{{ item.name }}</div>
      <div class="deck-row-desc font-body">{{ item.description }}</div>
    </template>
  </ManageListShell>
</template>

<style scoped>
.deck-form-frame {
  margin-bottom: var(--space-11);
}
.deck-form {
  padding: var(--space-10);
  display: flex;
  flex-direction: column;
  gap: var(--space-7);
}
.form-title {
  font-size: var(--font-size-base);
  letter-spacing: var(--tracking-normal);
  color: var(--text-label-accent);
  margin: 0;
}
.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-5);
  margin-top: var(--space-2);
}
.deck-row-name {
  font-size: var(--font-size-lg);
  font-weight: 600;
  color: var(--text-primary);
}
.deck-row-desc {
  font-size: var(--font-size-md);
  color: var(--text-secondary);
  margin-top: var(--space-1);
}
.arcade-input:focus-visible {
  outline: var(--focus-ring-width) solid var(--color-focus-ring);
  outline-offset: 2px;
}
</style>
