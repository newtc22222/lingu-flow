<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
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
  imageUrl?: string | null
  notes?: string | null
}

interface Deck {
  id: string
  name: string
}

const { t } = useI18n()
const router = useRouter()

const cards = ref<Card[]>([])
const decks = ref<Deck[]>([])
const isLoading = ref(true)
const isEditing = ref(false)
const editingCardId = ref<string | null>(null)

const blankForm = () => ({
  front: '',
  back: '',
  deckId: '',
  imageUrl: '',
  notes: '',
})

const form = ref(blankForm())

const fetchCardsAndDecks = async () => {
  isLoading.value = true
  try {
    const [cardsRes, decksRes] = await Promise.all([apiFetch('/api/cards'), apiFetch('/api/decks')])
    const rawCards = (await cardsRes.json()) as Record<string, unknown>[]
    const rawDecks = (await decksRes.json()) as Record<string, unknown>[]
    cards.value = rawCards.map((c) => ({
      id: c.id as string,
      front: c.front as string,
      back: c.back as string,
      deckId: c.deckId as string | undefined,
      imageUrl: c.imageUrl as string | null | undefined,
      notes: c.notes as string | null | undefined,
    }))
    decks.value = rawDecks.map((d) => ({ id: d.id as string, name: d.name as string }))
  } catch (error) {
    console.error('Failed to fetch data:', error)
  } finally {
    isLoading.value = false
  }
}

const saveCard = async () => {
  try {
    // Empty optional inputs are sent as null, not "", so the column stays NULL.
    const payload = {
      front: form.value.front,
      back: form.value.back,
      deckId: form.value.deckId || null,
      imageUrl: form.value.imageUrl.trim() || null,
      notes: form.value.notes.trim() || null,
    }

    if (isEditing.value && editingCardId.value) {
      await apiFetch(`/api/cards/${editingCardId.value}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
    } else {
      await apiFetch('/api/cards', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
    }

    form.value = blankForm()
    isEditing.value = false
    editingCardId.value = null

    await fetchCardsAndDecks()
  } catch (error) {
    console.error('Failed to save card:', error)
  }
}

const editCard = (card: Card) => {
  form.value = {
    front: card.front,
    back: card.back,
    deckId: card.deckId || '',
    imageUrl: card.imageUrl ?? '',
    notes: card.notes ?? '',
  }
  isEditing.value = true
  editingCardId.value = card.id
}

const deleteCard = async (id: string) => {
  if (!confirm(t('cards.confirmDelete'))) return
  try {
    await apiFetch(`/api/cards/${id}`, { method: 'DELETE' })
    await fetchCardsAndDecks()
  } catch (error) {
    console.error('Failed to delete card:', error)
  }
}

const cancelEdit = () => {
  form.value = blankForm()
  isEditing.value = false
  editingCardId.value = null
}

onMounted(() => {
  fetchCardsAndDecks()
})
</script>

<template>
  <ManageListShell
    :title="t('cards.title')"
    :count-label="t('cards.countLabel')"
    :count="cards.length"
    :is-loading="isLoading"
    :loading-text="t('cards.loading')"
    :empty-text="t('cards.empty')"
    :rows="cards"
    @edit="editCard"
    @delete="deleteCard"
  >
    <template #header-extra>
      <AppButton variant="secondary" @click="router.push({ name: 'dashboard' })">
        {{ t('common.back') }}
      </AppButton>
    </template>

    <template #form>
      <PixelFrame frame-color="amber" surface="cabinet" :ring-width="3" class="card-form-frame">
        <div class="card-form-grid">
          <form class="card-form" @submit.prevent="saveCard">
            <h3 class="form-title font-label">
              {{ isEditing ? t('cards.editTitle') : t('cards.createTitle') }}
            </h3>

            <div class="arcade-field">
              <label class="arcade-label" for="card-deck">{{ t('cards.deckOptional') }}</label>
              <select id="card-deck" v-model="form.deckId" class="arcade-input">
                <option value="">{{ t('cards.noDeck') }}</option>
                <option v-for="deck in decks" :key="deck.id" :value="deck.id">{{ deck.name }}</option>
              </select>
            </div>

            <div class="arcade-field">
              <label class="arcade-label" for="card-front">{{ t('cards.front') }}</label>
              <textarea
                id="card-front"
                v-model="form.front"
                required
                rows="4"
                class="arcade-input"
                :placeholder="t('cards.frontPlaceholder')"
              ></textarea>
            </div>

            <div class="arcade-field">
              <label class="arcade-label" for="card-back">{{ t('cards.back') }}</label>
              <textarea
                id="card-back"
                v-model="form.back"
                required
                rows="4"
                class="arcade-input"
                :placeholder="t('cards.backPlaceholder')"
              ></textarea>
            </div>

            <div class="arcade-field">
              <label class="arcade-label" for="card-image">{{ t('cards.imageUrl') }}</label>
              <input id="card-image" v-model="form.imageUrl" type="url" class="arcade-input" />
            </div>

            <div class="arcade-field">
              <label class="arcade-label" for="card-notes">{{ t('cards.notes') }}</label>
              <textarea
                id="card-notes"
                v-model="form.notes"
                rows="2"
                class="arcade-input"
              ></textarea>
            </div>

            <div class="form-actions">
              <AppButton v-if="isEditing" variant="secondary" type="button" @click="cancelEdit">
                {{ t('common.cancel') }}
              </AppButton>
              <AppButton type="submit">
                {{ isEditing ? t('common.update') : t('cards.saveCard') }}
              </AppButton>
            </div>
          </form>

          <div class="card-preview">
            <span class="preview-label font-label">{{ t('cards.preview') }}</span>
            <div class="preview-panel">
              <div class="preview-eyebrow font-label">{{ t('cards.frontShort') }}</div>
              <div class="preview-content font-body">
                <MarkdownRenderer v-if="form.front" :content="form.front" />
                <span v-else class="preview-placeholder">{{ t('cards.previewFront') }}</span>
              </div>
              <div class="preview-divider" />
              <div class="preview-eyebrow preview-eyebrow--back font-label">
                {{ t('cards.backShort') }}
              </div>
              <div class="preview-content font-body">
                <MarkdownRenderer v-if="form.back" :content="form.back" />
                <span v-else class="preview-placeholder">{{ t('cards.previewBack') }}</span>
              </div>
            </div>
          </div>
        </div>
      </PixelFrame>
    </template>

    <template #row="{ item }">
      <div class="card-row-eyebrow font-label">{{ t('cards.frontShort') }}</div>
      <div class="card-row-text font-body">{{ item.front }}</div>
      <div class="card-row-eyebrow card-row-eyebrow--back font-label">{{ t('cards.backShort') }}</div>
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
