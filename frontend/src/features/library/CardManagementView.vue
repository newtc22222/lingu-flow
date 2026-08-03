<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { apiFetch } from '@/utils/api'
import PixelFrame from '@/shared/components/PixelFrame.vue'
import MarkdownRenderer from '@/components/MarkdownRenderer.vue'

interface Card {
  id: string
  front: string
  back: string
  deckId?: string
}

interface Deck {
  id: string
  name: string
}

const cards = ref<Card[]>([])
const decks = ref<Deck[]>([])
const isLoading = ref(true)
const isEditing = ref(false)
const editingCardId = ref<string | null>(null)

const form = ref({
  front: '',
  back: '',
  deckId: '',
})

const emit = defineEmits<{
  (e: 'close'): void
}>()

const fetchCardsAndDecks = async () => {
  isLoading.value = true
  try {
    const [cardsRes, decksRes] = await Promise.all([apiFetch('/api/cards'), apiFetch('/api/decks')])
    const rawCards = (await cardsRes.json()) as Record<string, unknown>[]
    const rawDecks = (await decksRes.json()) as Record<string, unknown>[]
    cards.value = rawCards.map((c) => ({
      id: (c.id ?? c._id) as string,
      front: c.front as string,
      back: c.back as string,
      deckId: c.deckId as string | undefined,
    }))
    decks.value = rawDecks.map((d) => ({ id: (d.id ?? d._id) as string, name: d.name as string }))
  } catch (error) {
    console.error('Failed to fetch data:', error)
  } finally {
    isLoading.value = false
  }
}

const saveCard = async () => {
  try {
    if (isEditing.value && editingCardId.value) {
      await apiFetch(`/api/cards/${editingCardId.value}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form.value),
      })
    } else {
      await apiFetch('/api/cards', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form.value),
      })
    }

    form.value = { front: '', back: '', deckId: '' }
    isEditing.value = false
    editingCardId.value = null

    await fetchCardsAndDecks()
  } catch (error) {
    console.error('Failed to save card:', error)
  }
}

const editCard = (card: Card) => {
  form.value = { front: card.front, back: card.back, deckId: card.deckId || '' }
  isEditing.value = true
  editingCardId.value = card.id
}

const deleteCard = async (id: string) => {
  if (!confirm('Bạn có chắc muốn xóa thẻ này?')) return
  try {
    await apiFetch(`/api/cards/${id}`, { method: 'DELETE' })
    await fetchCardsAndDecks()
  } catch (error) {
    console.error('Failed to delete card:', error)
  }
}

const cancelEdit = () => {
  form.value = { front: '', back: '', deckId: '' }
  isEditing.value = false
  editingCardId.value = null
}

onMounted(() => {
  fetchCardsAndDecks()
})
</script>

<template>
  <div class="card-view">
    <div class="card-header">
      <h2 class="card-title font-body">QUẢN LÝ THẺ</h2>
      <div class="card-header-right">
        <span v-if="!isLoading" class="count-badge font-label">{{ cards.length }} THẺ</span>
        <button type="button" class="btn-guest font-label" @click="emit('close')">← QUAY LẠI</button>
      </div>
    </div>

    <PixelFrame frame-color="amber" surface="cabinet" :ring-width="3" class="card-form-frame">
      <div class="card-form-grid">
        <form class="card-form" @submit.prevent="saveCard">
          <h3 class="form-title font-label">{{ isEditing ? 'CHỈNH SỬA THẺ' : 'TẠO THẺ MỚI' }}</h3>

          <div class="arcade-field">
            <label class="arcade-label" for="card-deck">BỘ THẺ (TÙY CHỌN)</label>
            <select id="card-deck" v-model="form.deckId" class="arcade-input">
              <option value="">Không thuộc bộ nào</option>
              <option v-for="deck in decks" :key="deck.id" :value="deck.id">{{ deck.name }}</option>
            </select>
          </div>

          <div class="arcade-field">
            <label class="arcade-label" for="card-front">MẶT TRƯỚC (HỖ TRỢ MARKDOWN)</label>
            <textarea
              id="card-front"
              v-model="form.front"
              required
              rows="4"
              class="arcade-input"
              placeholder="VD: Thủ đô của Pháp là gì?"
            ></textarea>
          </div>

          <div class="arcade-field">
            <label class="arcade-label" for="card-back">MẶT SAU (HỖ TRỢ MARKDOWN)</label>
            <textarea
              id="card-back"
              v-model="form.back"
              required
              rows="4"
              class="arcade-input"
              placeholder="VD: **Paris**"
            ></textarea>
          </div>

          <div class="form-actions">
            <button v-if="isEditing" type="button" class="btn-guest font-label" @click="cancelEdit">HỦY</button>
            <button type="submit" class="btn-arcade font-label">{{ isEditing ? 'CẬP NHẬT' : 'LƯU THẺ' }}</button>
          </div>
        </form>

        <div class="card-preview">
          <span class="preview-label font-label">▸ XEM TRƯỚC</span>
          <div class="preview-panel">
            <div class="preview-eyebrow font-label">MẶT TRƯỚC</div>
            <div class="preview-content font-body">
              <MarkdownRenderer v-if="form.front" :content="form.front" />
              <span v-else class="preview-placeholder">Xem trước mặt trước…</span>
            </div>
            <div class="preview-divider" />
            <div class="preview-eyebrow preview-eyebrow--back font-label">MẶT SAU</div>
            <div class="preview-content font-body">
              <MarkdownRenderer v-if="form.back" :content="form.back" />
              <span v-else class="preview-placeholder">Xem trước mặt sau…</span>
            </div>
          </div>
        </div>
      </div>
    </PixelFrame>

    <div class="card-list-status font-label" v-if="isLoading">▸ ĐANG TẢI THẺ…</div>
    <div class="card-list-status font-label" v-else-if="cards.length === 0">
      CHƯA CÓ THẺ NÀO. TẠO THẺ ĐẦU TIÊN Ở TRÊN.
    </div>

    <ul v-else class="card-list">
      <li v-for="card in cards" :key="card.id" class="card-row">
        <div class="card-row-info">
          <div class="card-row-eyebrow font-label">MẶT TRƯỚC</div>
          <div class="card-row-text font-body">{{ card.front }}</div>
          <div class="card-row-eyebrow card-row-eyebrow--back font-label">MẶT SAU</div>
          <div class="card-row-text font-body">{{ card.back }}</div>
        </div>
        <div class="card-row-actions">
          <button type="button" class="btn-edit font-label" @click="editCard(card)">SỬA</button>
          <button type="button" class="btn-delete font-label" @click="deleteCard(card.id)">XÓA</button>
        </div>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  gap: 12px;
  flex-wrap: wrap;
}
.card-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--phosphor);
  margin: 0;
}
.card-header-right {
  display: flex;
  align-items: center;
  gap: 12px;
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
.card-form-frame {
  margin-bottom: 26px;
}
.card-form-grid {
  padding: 22px;
  display: grid;
  grid-template-columns: 1fr;
  gap: 22px;
}
@media (min-width: 768px) {
  .card-form-grid {
    grid-template-columns: 1fr 1fr;
  }
}
.card-form {
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
textarea.arcade-input {
  resize: vertical;
  font-family: var(--font-body);
}
select.arcade-input {
  font-family: var(--font-body);
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
.card-preview {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.preview-label {
  font-size: 11px;
  letter-spacing: 1px;
  color: var(--muted);
}
.preview-panel {
  background: var(--ink);
  padding: 16px;
  flex: 1;
}
.preview-eyebrow {
  font-size: 11px;
  letter-spacing: 1px;
  color: var(--amber);
  margin-bottom: 8px;
}
.preview-eyebrow--back {
  color: var(--green);
  margin-top: 16px;
}
.preview-content {
  color: var(--phosphor);
  font-size: 15px;
  min-height: 2.5rem;
}
.preview-placeholder {
  color: var(--muted);
  font-style: italic;
}
.preview-divider {
  height: 1px;
  background: var(--cabinet-light);
  margin-top: 16px;
}
.card-list-status {
  color: var(--muted);
  font-size: 12px;
  text-align: center;
  padding: 30px 0;
}
.card-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.card-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  background: var(--cabinet);
  border-left: 3px solid var(--cabinet-light);
  padding: 14px 16px;
  transition: border-color 0.12s, background 0.12s;
}
.card-row:hover {
  border-left-color: var(--amber);
  background: var(--surface-hover);
}
.card-row-info {
  min-width: 0;
  flex: 1;
}
.card-row-eyebrow {
  font-size: 10px;
  letter-spacing: 1px;
  color: var(--amber);
  margin-bottom: 4px;
}
.card-row-eyebrow--back {
  color: var(--green);
  margin-top: 10px;
}
.card-row-text {
  font-size: 14px;
  color: var(--phosphor);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.card-row-actions {
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
