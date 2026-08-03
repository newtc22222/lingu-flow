<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { apiFetch } from '@/utils/api'
import PixelFrame from '@/shared/components/PixelFrame.vue'
import MarkdownRenderer from '@/shared/components/MarkdownRenderer.vue'

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
  margin-bottom: var(--space-9);
  gap: var(--space-6);
  flex-wrap: wrap;
}
.card-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}
.card-header-right {
  display: flex;
  align-items: center;
  gap: var(--space-6);
}
.count-badge {
  font-size: var(--font-size-base);
  font-weight: 700;
  letter-spacing: 1px;
  color: var(--color-accent);
  background: var(--surface-page);
  border: var(--space-1) solid var(--color-accent);
  padding: var(--space-2) var(--space-5);
}
.card-form-frame {
  margin-bottom: var(--space-11);
}
.card-form-grid {
  padding: var(--space-10);
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--space-10);
}
@media (min-width: 768px) {
  .card-form-grid {
    grid-template-columns: 1fr 1fr;
  }
}
.card-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-7);
}
.form-title {
  font-size: var(--font-size-base);
  letter-spacing: 1px;
  color: var(--text-label-accent);
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
  gap: var(--space-5);
  margin-top: var(--space-2);
}
.btn-arcade {
  font-weight: 700;
  font-size: var(--font-size-md);
  letter-spacing: 1.5px;
  text-transform: uppercase;
  background: var(--status-success);
  color: var(--text-on-accent);
  border: none;
  padding: var(--space-6) var(--space-10);
  cursor: pointer;
  box-shadow: 0 4px 0 var(--status-success-subtle);
}
.btn-arcade:active {
  transform: translateY(4px);
  box-shadow: none;
}
.btn-guest {
  background: transparent;
  border: var(--space-1) solid var(--surface-panel-border);
  color: var(--text-secondary);
  padding: var(--space-5) var(--space-8);
  font-size: var(--font-size-sm);
  letter-spacing: 1px;
  cursor: pointer;
}
.btn-guest:hover {
  border-color: var(--color-accent);
  color: var(--text-primary);
}
.card-preview {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}
.preview-label {
  font-size: var(--font-size-sm);
  letter-spacing: 1px;
  color: var(--text-secondary);
}
.preview-panel {
  background: var(--surface-page);
  padding: var(--space-8);
  flex: 1;
}
.preview-eyebrow {
  font-size: var(--font-size-sm);
  letter-spacing: 1px;
  color: var(--text-label-accent);
  margin-bottom: var(--space-4);
}
.preview-eyebrow--back {
  color: var(--green);
  margin-top: var(--space-8);
}
.preview-content {
  color: var(--text-primary);
  font-size: 15px;
  min-height: 2.5rem;
}
.preview-placeholder {
  color: var(--text-secondary);
  font-style: italic;
}
.preview-divider {
  height: 1px;
  background: var(--surface-panel-border);
  margin-top: var(--space-8);
}
.card-list-status {
  color: var(--text-secondary);
  font-size: var(--font-size-base);
  text-align: center;
  padding: 30px 0;
}
.card-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}
.card-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-8);
  background: var(--surface-panel);
  border-left: 3px solid var(--surface-panel-border);
  padding: var(--space-7) var(--space-8);
  transition: border-color 0.12s, background 0.12s;
}
.card-row:hover {
  border-left-color: var(--color-accent);
  background: var(--state-hover-surface);
}
.card-row-info {
  min-width: 0;
  flex: 1;
}
.card-row-eyebrow {
  font-size: var(--font-size-xs);
  letter-spacing: 1px;
  color: var(--text-label-accent);
  margin-bottom: var(--space-2);
}
.card-row-eyebrow--back {
  color: var(--green);
  margin-top: var(--space-5);
}
.card-row-text {
  font-size: 14px;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.card-row-actions {
  display: flex;
  gap: var(--space-4);
  flex-shrink: 0;
}
.btn-edit,
.btn-delete {
  font-size: var(--font-size-sm);
  letter-spacing: 1px;
  padding: var(--space-3) var(--space-6);
  border: none;
  cursor: pointer;
  background: var(--surface-panel-border);
}
.btn-edit {
  color: var(--color-accent);
}
.btn-edit:hover {
  background: var(--state-selected-surface);
}
.btn-delete {
  color: var(--status-danger);
}
.btn-delete:hover {
  background: var(--status-danger-subtle);
  color: var(--text-primary);
}
.arcade-input:focus-visible,
.btn-arcade:focus-visible,
.btn-guest:focus-visible,
.btn-edit:focus-visible,
.btn-delete:focus-visible {
  outline: 2px solid var(--color-focus-ring);
  outline-offset: 2px;
}
</style>
