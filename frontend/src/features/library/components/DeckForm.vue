<script setup lang="ts">
/**
 * Create/edit form for a deck. Parent owns submit/cancel and the deck list;
 * this component only presents fields and exposes focusFirstField for N/E.
 */
import { nextTick, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import PixelFrame from '@/shared/components/PixelFrame.vue';
import AppButton from '@/shared/components/AppButton.vue';

export interface DeckFormModel {
  name: string;
  description: string;
}

const props = withDefaults(
  defineProps<{
    deck: DeckFormModel | null;
    isSaving: boolean;
    error: string;
    /** False when a console bay already owns the frame and the scroll. */
    framed?: boolean;
  }>(),
  { framed: true },
);

const emit = defineEmits<{
  (e: 'submit', payload: DeckFormModel): void;
  (e: 'cancel'): void;
}>();

const { t } = useI18n();

const nameInput = ref<HTMLInputElement | null>(null);
const form = ref<DeckFormModel>({ name: '', description: '' });

watch(
  () => props.deck,
  (deck) => {
    form.value = deck
      ? { name: deck.name, description: deck.description || '' }
      : { name: '', description: '' };
  },
  { immediate: true },
);

function onSubmit() {
  emit('submit', { ...form.value });
}

async function focusFirstField() {
  await nextTick();
  nameInput.value?.focus();
  nameInput.value?.select();
}

defineExpose({ focusFirstField });
</script>

<template>
  <component
    :is="framed ? PixelFrame : 'div'"
    v-bind="framed ? { frameColor: 'amber', surface: 'cabinet', ringWidth: 3 } : {}"
    :class="framed ? 'deck-form-frame' : 'deck-form-bare'"
  >
    <form class="deck-form" @submit.prevent="onSubmit">
      <h3 class="form-title font-label">
        {{ deck ? t('decks.editTitle') : t('decks.createTitle') }}
      </h3>

      <div class="arcade-field">
        <label class="arcade-label" for="deck-name">{{ t('decks.name') }}</label>
        <input
          id="deck-name"
          ref="nameInput"
          v-model="form.name"
          required
          type="text"
          class="arcade-input"
          :placeholder="t('decks.namePlaceholder')"
          :disabled="isSaving"
        />
      </div>

      <div class="arcade-field">
        <label class="arcade-label" for="deck-desc">{{ t('decks.description') }}</label>
        <input
          id="deck-desc"
          v-model="form.description"
          type="text"
          class="arcade-input"
          :placeholder="t('decks.descriptionPlaceholder')"
          :disabled="isSaving"
        />
      </div>

      <p v-if="error" class="form-error font-body" role="alert">{{ error }}</p>

      <div class="form-actions">
        <AppButton
          v-if="deck"
          variant="secondary"
          type="button"
          :disabled="isSaving"
          @click="emit('cancel')"
        >
          {{ t('common.cancel') }}
        </AppButton>
        <AppButton type="submit" :disabled="isSaving">
          {{ deck ? t('common.update') : t('decks.saveDeck') }}
        </AppButton>
      </div>
    </form>
  </component>
</template>

<style scoped>
.deck-form-frame {
  margin-bottom: var(--space-11);
}
.deck-form-bare {
  display: block;
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
.form-error {
  margin: 0;
  color: var(--status-danger);
  font-size: var(--font-size-md);
}
.arcade-input:focus-visible {
  outline: var(--focus-ring-width) solid var(--color-focus-ring);
  outline-offset: 2px;
}
</style>
