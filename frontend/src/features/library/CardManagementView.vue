<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { apiFetch } from '@/utils/api'
import PixelFrame from '@/shared/components/PixelFrame.vue'
import AppButton from '@/shared/components/AppButton.vue'
import ManageListShell from '@/shared/components/ManageListShell.vue'
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
  <ManageListShell
    title="QUẢN LÝ THẺ"
    count-label="THẺ"
    :count="cards.length"
    :is-loading="isLoading"
    loading-text="▸ ĐANG TẢI THẺ…"
    empty-text="CHƯA CÓ THẺ NÀO. TẠO THẺ ĐẦU TIÊN Ở TRÊN."
    :rows="cards"
    @edit="editCard"
    @delete="deleteCard"
  >
    <template #header-extra>
      <AppButton variant="secondary" @click="emit('close')">← QUAY LẠI</AppButton>
    </template>

    <template #form>
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
              <AppButton v-if="isEditing" variant="secondary" type="button" @click="cancelEdit">HỦY</AppButton>
              <AppButton type="submit">{{ isEditing ? 'CẬP NHẬT' : 'LƯU THẺ' }}</AppButton>
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
    </template>

    <template #row="{ item }">
      <div class="card-row-eyebrow font-label">MẶT TRƯỚC</div>
      <div class="card-row-text font-body">{{ item.front }}</div>
      <div class="card-row-eyebrow card-row-eyebrow--back font-label">MẶT SAU</div>
      <div class="card-row-text font-body">{{ item.back }}</div>
    </template>
  </ManageListShell>
</template>

<style scoped>
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
  letter-spacing: var(--tracking-normal);
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
.card-preview {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}
.preview-label {
  font-size: var(--font-size-sm);
  letter-spacing: var(--tracking-normal);
  color: var(--text-secondary);
}
.preview-panel {
  background: var(--surface-page);
  padding: var(--space-8);
  flex: 1;
}
.preview-eyebrow {
  font-size: var(--font-size-sm);
  letter-spacing: var(--tracking-normal);
  color: var(--text-label-accent);
  margin-bottom: var(--space-4);
}
.preview-eyebrow--back {
  color: var(--green);
  margin-top: var(--space-8);
}
.preview-content {
  color: var(--text-primary);
  font-size: var(--font-size-lg);
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
.card-row-eyebrow {
  font-size: var(--font-size-xs);
  letter-spacing: var(--tracking-normal);
  color: var(--text-label-accent);
  margin-bottom: var(--space-2);
}
.card-row-eyebrow--back {
  color: var(--green);
  margin-top: var(--space-5);
}
.card-row-text {
  font-size: var(--font-size-md-plus);
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.arcade-input:focus-visible {
  outline: var(--focus-ring-width) solid var(--color-focus-ring);
  outline-offset: 2px;
}
</style>
