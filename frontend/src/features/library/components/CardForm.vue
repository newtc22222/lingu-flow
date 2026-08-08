<script setup lang="ts">
/**
 * Create/edit form for a card, with live markdown preview. Parent owns the
 * save pipeline; this component presents fields and exposes focusFirstField.
 */
import { nextTick, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import PixelFrame from '@/shared/components/PixelFrame.vue';
import AppButton from '@/shared/components/AppButton.vue';
import MarkdownRenderer from '@/shared/components/MarkdownRenderer.vue';
import type { DeckOption } from '../types';

export interface CardFormModel {
  front: string;
  back: string;
  deckId: string;
  imageUrl: string;
  notes: string;
}

const props = withDefaults(
  defineProps<{
    card: CardFormModel | null;
    decks: DeckOption[];
    defaultDeckId: string | null;
    isSaving: boolean;
    error: string;
    showDeckSelect?: boolean;
    /** False when a console bay already owns the frame and the scroll. */
    framed?: boolean;
  }>(),
  { showDeckSelect: true, framed: true },
);

const emit = defineEmits<{
  (e: 'submit', payload: CardFormModel): void;
  (e: 'cancel'): void;
}>();

const { t } = useI18n();

const frontInput = ref<HTMLTextAreaElement | null>(null);

function blank(defaultDeckId: string | null): CardFormModel {
  return {
    front: '',
    back: '',
    deckId: defaultDeckId ?? '',
    imageUrl: '',
    notes: '',
  };
}

const form = ref<CardFormModel>(blank(props.defaultDeckId));

watch(
  () => [props.card, props.defaultDeckId] as const,
  ([card, defaultDeckId]) => {
    form.value = card
      ? {
          front: card.front,
          back: card.back,
          deckId: card.deckId || '',
          imageUrl: card.imageUrl ?? '',
          notes: card.notes ?? '',
        }
      : blank(defaultDeckId);
  },
  { immediate: true },
);

function onSubmit() {
  emit('submit', { ...form.value });
}

async function focusFirstField() {
  await nextTick();
  frontInput.value?.focus();
  frontInput.value?.select();
}

defineExpose({ focusFirstField });
</script>

<template>
  <component
    :is="framed ? PixelFrame : 'div'"
    v-bind="framed ? { frameColor: 'amber', surface: 'cabinet', ringWidth: 3 } : {}"
    :class="framed ? 'card-form-frame' : 'card-form-bare'"
  >
    <div class="card-form-grid" :class="{ 'card-form-grid--bay': !framed }">
      <form class="card-form" @submit.prevent="onSubmit">
        <h3 class="form-title font-label">
          {{ card ? t('cards.editTitle') : t('cards.createTitle') }}
        </h3>

        <div v-if="showDeckSelect" class="arcade-field">
          <label class="arcade-label" for="card-deck">{{ t('cards.deckOptional') }}</label>
          <select id="card-deck" v-model="form.deckId" class="arcade-input" :disabled="isSaving">
            <option value="">{{ t('cards.noDeck') }}</option>
            <option v-for="deck in decks" :key="deck.id" :value="deck.id">
              {{ deck.name }}
            </option>
          </select>
        </div>

        <div class="arcade-field">
          <label class="arcade-label" for="card-front">{{ t('cards.front') }}</label>
          <textarea
            id="card-front"
            ref="frontInput"
            v-model="form.front"
            required
            rows="4"
            class="arcade-input"
            :placeholder="t('cards.frontPlaceholder')"
            :disabled="isSaving"
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
            :disabled="isSaving"
          ></textarea>
        </div>

        <div class="arcade-field">
          <label class="arcade-label" for="card-image">{{ t('cards.imageUrl') }}</label>
          <input
            id="card-image"
            v-model="form.imageUrl"
            type="url"
            class="arcade-input"
            :disabled="isSaving"
          />
        </div>

        <div class="arcade-field">
          <label class="arcade-label" for="card-notes">{{ t('cards.notes') }}</label>
          <textarea
            id="card-notes"
            v-model="form.notes"
            rows="2"
            class="arcade-input"
            :disabled="isSaving"
          ></textarea>
        </div>

        <p v-if="error" class="form-error font-body" role="alert">{{ error }}</p>

        <div class="form-actions">
          <AppButton
            v-if="card"
            variant="secondary"
            type="button"
            :disabled="isSaving"
            @click="emit('cancel')"
          >
            {{ t('common.cancel') }}
          </AppButton>
          <AppButton type="submit" :disabled="isSaving">
            {{ card ? t('common.update') : t('cards.saveCard') }}
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
  </component>
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
.card-form-bare {
  display: block;
}
/* In a console bay the form already owns only half the page — keep the
   preview stacked under the fields instead of halving the column again. */
@media (min-width: 768px) {
  .card-form-grid--bay {
    grid-template-columns: 1fr;
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
.form-error {
  margin: 0;
  color: var(--status-danger);
  font-size: var(--font-size-md);
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
  color: var(--status-success);
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
.arcade-input:focus-visible {
  outline: var(--focus-ring-width) solid var(--color-focus-ring);
  outline-offset: 2px;
}
</style>
