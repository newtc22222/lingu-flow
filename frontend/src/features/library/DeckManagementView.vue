<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { apiFetch } from '@/utils/api'
import PixelFrame from '@/shared/components/PixelFrame.vue'

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
  <div class="deck-view">
    <div class="deck-header">
      <h2 class="deck-title font-body">QUẢN LÝ BỘ THẺ</h2>
      <span v-if="!isLoading" class="count-badge font-label">{{ decks.length }} BỘ</span>
    </div>

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
          <button v-if="isEditing" type="button" class="btn-guest font-label" @click="cancelEdit">HỦY</button>
          <button type="submit" class="btn-arcade font-label">{{ isEditing ? 'CẬP NHẬT' : 'LƯU BỘ THẺ' }}</button>
        </div>
      </form>
    </PixelFrame>

    <div class="deck-list-status font-label" v-if="isLoading">▸ ĐANG TẢI BỘ THẺ…</div>
    <div class="deck-list-status font-label" v-else-if="decks.length === 0">
      CHƯA CÓ BỘ THẺ NÀO. TẠO BỘ THẺ ĐẦU TIÊN Ở TRÊN.
    </div>

    <ul v-else class="deck-list">
      <li v-for="deck in decks" :key="deck.id" class="deck-row">
        <div class="deck-row-info">
          <div class="deck-row-name font-body">{{ deck.name }}</div>
          <div class="deck-row-desc font-body">{{ deck.description }}</div>
        </div>
        <div class="deck-row-actions">
          <button type="button" class="btn-edit font-label" @click="editDeck(deck)">SỬA</button>
          <button type="button" class="btn-delete font-label" @click="deleteDeck(deck.id)">XÓA</button>
        </div>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.deck-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}
.deck-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--phosphor);
  margin: 0;
}
.count-badge {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 1px;
  color: var(--amber);
  background: var(--ink);
  border: 2px solid var(--amber);
  padding: 4px 10px;
}
.deck-form-frame {
  margin-bottom: 26px;
}
.deck-form {
  padding: 22px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.form-title {
  font-size: 12px;
  letter-spacing: 1px;
  color: var(--amber);
  margin: 0;
}
.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 4px;
}
.btn-arcade {
  font-weight: 700;
  font-size: 13px;
  letter-spacing: 1.5px;
  text-transform: uppercase;
  background: var(--green);
  color: var(--ink);
  border: none;
  padding: 12px 22px;
  cursor: pointer;
  box-shadow: 0 4px 0 var(--green-shadow);
}
.btn-arcade:active {
  transform: translateY(4px);
  box-shadow: none;
}
.btn-guest {
  background: transparent;
  border: 2px solid var(--cabinet-light);
  color: var(--muted);
  padding: 10px 18px;
  font-size: 11px;
  letter-spacing: 1px;
  cursor: pointer;
}
.btn-guest:hover {
  border-color: var(--amber);
  color: var(--phosphor);
}
.deck-list-status {
  color: var(--muted);
  font-size: 12px;
  text-align: center;
  padding: 30px 0;
}
.deck-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.deck-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  background: var(--cabinet);
  border-left: 3px solid var(--cabinet-light);
  padding: 14px 16px;
  transition: border-color 0.12s, background 0.12s;
}
.deck-row:hover {
  border-left-color: var(--amber);
  background: var(--surface-hover);
}
.deck-row-info {
  min-width: 0;
}
.deck-row-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--phosphor);
}
.deck-row-desc {
  font-size: 13px;
  color: var(--muted);
  margin-top: 2px;
}
.deck-row-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}
.btn-edit,
.btn-delete {
  font-size: 11px;
  letter-spacing: 1px;
  padding: 6px 12px;
  border: none;
  cursor: pointer;
  background: var(--cabinet-light);
}
.btn-edit {
  color: var(--amber);
}
.btn-edit:hover {
  background: var(--surface-selected);
}
.btn-delete {
  color: var(--red);
}
.btn-delete:hover {
  background: var(--red-shadow);
  color: var(--phosphor);
}
.arcade-input:focus-visible,
.btn-arcade:focus-visible,
.btn-guest:focus-visible,
.btn-edit:focus-visible,
.btn-delete:focus-visible {
  outline: 2px solid var(--amber);
  outline-offset: 2px;
}
</style>
