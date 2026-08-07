<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';
import ManageListShell from '@/shared/components/ManageListShell.vue';
import ConfirmDialog from '@/shared/components/ConfirmDialog.vue';
import AppButton from '@/shared/components/AppButton.vue';
import CardForm, { type CardFormModel } from './components/CardForm.vue';
import CardRow from './components/CardRow.vue';
import KeycapLegend from './components/KeycapLegend.vue';
import { libraryApi } from './api';
import { useRovingList } from './composables/useRovingList';
import type { DeckCard, DeckOption } from './types';

const props = defineProps<{ deckId: string | null }>();

const { t } = useI18n();
const router = useRouter();

const isUnfiled = computed(() => props.deckId === null);

const shellRef = ref<HTMLElement | null>(null);
const searchInputRef = ref<HTMLInputElement | null>(null);
const formRef = ref<InstanceType<typeof CardForm> | null>(null);
/** Bumped after a successful save so CardForm remounts blank for create. */
const formKey = ref(0);

const deckName = ref('');
const cards = ref<DeckCard[]>([]);
const allDecks = ref<DeckOption[]>([]);
const isLoading = ref(true);
const notFound = ref(false);
const loadError = ref('');
const formError = ref('');
const listError = ref('');
const liveMessage = ref('');
const searchQuery = ref('');

const isSaving = ref(false);
const isSavingOrder = ref(false);
const orderSaved = ref(false);
const isEditing = ref(false);
const editingCard = ref<DeckCard | null>(null);

const showDeleteConfirm = ref(false);
const pendingDeleteId = ref<string | null>(null);
const focusAfterDialog = ref(-1);

const draggingIndex = ref<number | null>(null);
const savedOrder = ref<string[]>([]);

const isBlocked = computed(() => showDeleteConfirm.value);

const isDirty = computed(
  () =>
    cards.value.length === savedOrder.value.length &&
    cards.value.some((card, i) => card.id !== savedOrder.value[i]),
);

const canReorder = computed(() => props.deckId !== null && searchQuery.value.trim() === '');

const filteredCards = computed(() => {
  const q = searchQuery.value.trim().toLowerCase();
  if (!q) return cards.value;
  return cards.value.filter(
    (c) =>
      c.front.toLowerCase().includes(q) ||
      c.back.toLowerCase().includes(q) ||
      (c.notes || '').toLowerCase().includes(q),
  );
});

const emptyText = computed(() => {
  if (searchQuery.value.trim()) {
    return t('library.searchNoResults', { query: searchQuery.value.trim() });
  }
  return t('deckDetail.empty');
});

const legendItems = computed(() => {
  const base = [
    { keys: ['↑', '↓'], label: t('library.legend.navigate') },
    { keys: ['↵'], label: t('library.legend.open') },
    { keys: ['E'], label: t('library.legend.edit') },
    { keys: ['N'], label: t('library.legend.new') },
    { keys: ['Del'], label: t('library.legend.delete') },
    { keys: ['/'], label: t('library.legend.search') },
  ];
  if (canReorder.value) {
    base.push(
      { keys: ['Alt', '↑/↓'], label: t('library.legend.reorder') },
      { keys: ['S'], label: t('library.legend.saveOrder') },
    );
  }
  base.push({ keys: ['Esc'], label: t('library.legend.cancel') });
  return base;
});

function announce(msg: string) {
  liveMessage.value = '';
  nextTick(() => {
    liveMessage.value = msg;
  });
}

async function fetchWorkspace() {
  isLoading.value = true;
  notFound.value = false;
  loadError.value = '';
  try {
    if (isUnfiled.value) {
      deckName.value = t('library.unfiledName');
      const [all, decks] = await Promise.all([
        libraryApi.listAllCards(),
        libraryApi.listDeckOptions(),
      ]);
      cards.value = all.filter((c) => !c.deckId);
      allDecks.value = decks;
      savedOrder.value = cards.value.map((c) => c.id);
      return;
    }

    const [decks, deckCards] = await Promise.all([
      libraryApi.listDecks(),
      libraryApi.listDeckCards(props.deckId!),
    ]);
    allDecks.value = decks.map((d) => ({ id: d.id, name: d.name }));
    const deck = decks.find((d) => d.id === props.deckId);
    if (!deck) {
      notFound.value = true;
      return;
    }
    deckName.value = deck.name;
    cards.value = deckCards;
    savedOrder.value = cards.value.map((c) => c.id);
  } catch (err) {
    console.error('Failed to load workspace:', err);
    loadError.value = err instanceof Error ? err.message : String(err);
  } finally {
    isLoading.value = false;
  }
}

async function refetchCards() {
  try {
    if (isUnfiled.value) {
      const all = await libraryApi.listAllCards();
      cards.value = all.filter((c) => !c.deckId);
    } else {
      cards.value = await libraryApi.listDeckCards(props.deckId!);
    }
    savedOrder.value = cards.value.map((c) => c.id);
    orderSaved.value = false;
  } catch (err) {
    listError.value = err instanceof Error ? err.message : String(err);
  }
}

/**
 * Persist full `cards[]` order for a real deck. Not gated on search filter —
 * interactive Alt/drag stays behind `canReorder`, but flush-before-mutation
 * and an armed SAVE ORDER must still write the pending arrangement.
 * Rethrows on failure so callers (withOrderFlushed) do not continue.
 */
async function saveOrder() {
  if (!props.deckId) return;
  isSavingOrder.value = true;
  listError.value = '';
  try {
    cards.value = await libraryApi.reorderDeckCards(
      props.deckId,
      cards.value.map((c) => c.id),
    );
    savedOrder.value = cards.value.map((c) => c.id);
    orderSaved.value = true;
    announce(t('deckDetail.orderSaved'));
  } catch (err) {
    // isDirty stays true so SAVE ORDER remains armed.
    listError.value = err instanceof Error ? err.message : String(err);
    throw err;
  } finally {
    isSavingOrder.value = false;
  }
}

/**
 * Flush pending reorder before any card mutation so PATCH cover stays exact.
 * Gated on deckId + isDirty — NOT canReorder — so a dirty order still flushes
 * when the user types a search query then creates/edits/deletes.
 */
async function withOrderFlushed(fn: () => Promise<void>) {
  if (props.deckId && isDirty.value) await saveOrder();
  await fn();
  await refetchCards();
}

function startEdit(card: DeckCard) {
  editingCard.value = card;
  isEditing.value = true;
  formError.value = '';
  nextTick(() => formRef.value?.focusFirstField());
}

function startNew() {
  editingCard.value = null;
  isEditing.value = false;
  formError.value = '';
  nextTick(() => formRef.value?.focusFirstField());
}

function cancelEdit() {
  editingCard.value = null;
  isEditing.value = false;
  formError.value = '';
}

function requestDelete(id: string) {
  pendingDeleteId.value = id;
  focusAfterDialog.value = filteredCards.value.findIndex((c) => c.id === id);
  showDeleteConfirm.value = true;
}

function editingFormModel(): CardFormModel | null {
  const c = editingCard.value;
  if (!c) return null;
  return {
    front: c.front,
    back: c.back,
    deckId: c.deckId || '',
    imageUrl: c.imageUrl ?? '',
    notes: c.notes ?? '',
  };
}

function focusSearch() {
  searchInputRef.value?.focus();
  searchInputRef.value?.select();
}

const { activeIndex, focusIndex, onRowFocus } = useRovingList<DeckCard>({
  containerRef: shellRef,
  items: filteredCards,
  onActivate: (item) => startEdit(item),
  onEdit: (item) => startEdit(item),
  onDelete: (item) => requestDelete(item.id),
  onNew: () => startNew(),
  onSearch: () => focusSearch(),
  onSave: () => {
    if (canReorder.value && isDirty.value) void saveOrder();
  },
  onMove: (from, to) => {
    const delta = (to - from) as 1 | -1;
    if (delta !== 1 && delta !== -1) return false;
    return moveBy(delta, from);
  },
  announce,
  isBlocked,
  searchQuery,
  searchInputRef,
  isEditing,
  onCancelEdit: () => cancelEdit(),
});

function moveBy(delta: 1 | -1, fromIndex?: number): boolean {
  if (!canReorder.value) {
    if (isUnfiled.value) {
      announce(t('library.reorderDisabled'));
    } else {
      announce(t('library.reorderWhileFiltered'));
    }
    return false;
  }
  const from = fromIndex ?? activeIndex.value;
  const to = from + delta;
  if (from < 0 || to < 0 || to >= cards.value.length) {
    announce(t('library.a11y.reorderBoundary'));
    return false;
  }
  const [moved] = cards.value.splice(from, 1);
  cards.value.splice(to, 0, moved);
  activeIndex.value = to;
  orderSaved.value = false;
  announce(
    t('library.a11y.moved', {
      name: moved.front,
      index: to + 1,
      total: cards.value.length,
    }),
  );
  nextTick(() => focusIndex(to));
  return true;
}

function onDragStart(index: number) {
  if (!canReorder.value) return;
  draggingIndex.value = index;
  orderSaved.value = false;
  activeIndex.value = index;
}

function onDragEnter(index: number) {
  if (!canReorder.value) return;
  const from = draggingIndex.value;
  if (from === null || from === index) return;
  const [moved] = cards.value.splice(from, 1);
  cards.value.splice(index, 0, moved);
  draggingIndex.value = index;
  activeIndex.value = index;
}

function onDragEnd() {
  draggingIndex.value = null;
}

async function confirmDelete() {
  const id = pendingDeleteId.value;
  if (!id) return;
  const restore = focusAfterDialog.value;
  try {
    await withOrderFlushed(async () => {
      await libraryApi.deleteCard(id);
    });
    announce(t('library.a11y.cardDeleted'));
    pendingDeleteId.value = null;
    cancelEdit();
    await nextTick();
    const next = Math.min(restore, Math.max(0, filteredCards.value.length - 1));
    if (filteredCards.value.length > 0) focusIndex(next);
  } catch (err) {
    listError.value = err instanceof Error ? err.message : String(err);
    await nextTick();
    if (restore >= 0) focusIndex(restore);
  }
}

async function onDeleteCancel() {
  const restore = focusAfterDialog.value;
  pendingDeleteId.value = null;
  await nextTick();
  if (restore >= 0) focusIndex(restore);
}

async function saveCard(payload: CardFormModel) {
  isSaving.value = true;
  formError.value = '';
  try {
    await withOrderFlushed(async () => {
      if (editingCard.value) {
        await libraryApi.updateCard(editingCard.value.id, {
          front: payload.front,
          back: payload.back,
          deckId: payload.deckId || null,
          imageUrl: payload.imageUrl,
          notes: payload.notes,
        });
        announce(t('library.a11y.cardUpdated'));
      } else {
        await libraryApi.createCard({
          front: payload.front,
          back: payload.back,
          deckId: payload.deckId || null,
          imageUrl: payload.imageUrl,
          notes: payload.notes,
        });
        announce(t('library.a11y.cardCreated'));
      }
    });
    cancelEdit();
    formKey.value += 1;
  } catch (err) {
    formError.value = err instanceof Error ? err.message : String(err);
  } finally {
    isSaving.value = false;
  }
}
let searchAnnounceTimer: ReturnType<typeof setTimeout> | null = null;
watch(searchQuery, () => {
  if (searchAnnounceTimer) clearTimeout(searchAnnounceTimer);
  searchAnnounceTimer = setTimeout(() => {
    const q = searchQuery.value.trim();
    if (!q) return;
    if (filteredCards.value.length === 0) {
      announce(t('library.searchNoResults', { query: q }));
    }
  }, 250);
});

watch(
  () => props.deckId,
  () => {
    fetchWorkspace();
  },
);

onMounted(fetchWorkspace);
</script>

<template>
  <div ref="shellRef" class="deck-workspace">
    <div class="sr-only" role="status" aria-live="polite" aria-atomic="true">{{ liveMessage }}</div>

    <div class="ws-top">
      <AppButton variant="secondary" @click="router.push({ name: 'decks' })">
        {{ t('library.backToDecks') }}
      </AppButton>
    </div>

    <p v-if="isLoading" class="ws-status font-label">{{ t('deckDetail.loading') }}</p>
    <p v-else-if="notFound" class="ws-status ws-status--error font-label">
      {{ t('deckDetail.notFound') }}
    </p>
    <p v-else-if="loadError" class="ws-status ws-status--error font-body" role="alert">
      {{ loadError }}
      <AppButton variant="secondary" @click="fetchWorkspace">{{ t('common.retry') }}</AppButton>
    </p>

    <template v-else>
      <div class="ws-header">
        <h1 class="ws-title font-body">{{ deckName }}</h1>
        <div v-if="!isUnfiled" class="ws-actions">
          <AppButton
            variant="secondary"
            @click="router.push({ name: 'learn', params: { deckId: props.deckId! } })"
          >
            {{ t('deckDetail.startLearn') }}
          </AppButton>
          <AppButton
            variant="secondary"
            @click="router.push({ name: 'match', params: { deckId: props.deckId! } })"
          >
            {{ t('deckDetail.startMatch') }}
          </AppButton>
        </div>
      </div>

      <KeycapLegend :items="legendItems" :legend-label="t('library.legend.title')" />

      <p v-if="listError" class="ws-alert font-body" role="alert">{{ listError }}</p>

      <ManageListShell
        :title="deckName"
        :count-label="t('cards.countLabel')"
        :count="filteredCards.length"
        :is-loading="false"
        :loading-text="t('deckDetail.loading')"
        :empty-text="emptyText"
        :rows="filteredCards"
        row-navigation
        :active-index="activeIndex"
        :list-label="t('library.a11y.cardList')"
        :draggable-rows="canReorder"
        @edit="startEdit"
        @delete="requestDelete"
        @row-activate="(item) => startEdit(item)"
        @row-focus="onRowFocus"
        @row-dragstart="onDragStart"
        @row-dragenter="onDragEnter"
        @row-dragend="onDragEnd"
      >
        <template #header-extra>
          <label class="sr-only" for="card-search">{{ t('library.search') }}</label>
          <input
            id="card-search"
            ref="searchInputRef"
            v-model="searchQuery"
            type="search"
            class="arcade-input ws-search"
            :placeholder="t('library.searchPlaceholder')"
          />
          <AppButton variant="secondary" @click="startNew">
            {{ t('library.addCard') }}
          </AppButton>
        </template>

        <template #form>
          <CardForm
            :key="formKey"
            ref="formRef"
            :card="editingFormModel()"
            :decks="allDecks"
            :default-deck-id="props.deckId"
            :is-saving="isSaving"
            :error="formError"
            :show-deck-select="true"
            @submit="saveCard"
            @cancel="cancelEdit"
          />

          <div v-if="canReorder && cards.length > 0" class="ws-reorder-bar">
            <span class="ws-hint font-body">{{ t('deckDetail.reorderHint') }}</span>
            <span v-if="orderSaved && !isDirty" class="ws-saved font-label">
              {{ t('deckDetail.orderSaved') }}
            </span>
            <AppButton :disabled="!isDirty || isSavingOrder" @click="saveOrder">
              {{ t('deckDetail.saveOrder') }}
            </AppButton>
          </div>

          <div v-if="searchQuery.trim() && filteredCards.length === 0" class="ws-search-empty">
            <AppButton variant="secondary" @click="searchQuery = ''">
              {{ t('library.clearSearch') }}
            </AppButton>
          </div>
        </template>

        <template #row="{ item, index }">
          <CardRow
            :card="item"
            :index="index"
            :is-dragging="draggingIndex === index"
            :is-reorderable="canReorder"
            @move-up="moveBy(-1, index)"
            @move-down="moveBy(1, index)"
          />
        </template>
      </ManageListShell>
    </template>

    <ConfirmDialog
      v-model:is-open="showDeleteConfirm"
      :title="t('library.confirmDeleteCardTitle')"
      :message="t('cards.confirmDelete')"
      :confirm-text="t('common.delete')"
      variant="danger"
      @confirm="confirmDelete"
      @cancel="onDeleteCancel"
    />
  </div>
</template>

<style scoped>
.ws-top {
  margin-bottom: var(--space-7);
}
.ws-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--space-7);
  margin-bottom: var(--space-7);
}
.ws-title {
  font-size: var(--font-size-xl);
  font-weight: 700;
  color: var(--color-accent);
  margin: 0;
}
.ws-actions {
  display: flex;
  gap: var(--space-5);
}
.ws-search {
  min-width: 160px;
  max-width: 220px;
}
.ws-reorder-bar {
  display: flex;
  align-items: center;
  gap: var(--space-7);
  flex-wrap: wrap;
  margin-bottom: var(--space-7);
}
.ws-hint {
  flex: 1;
  min-width: 200px;
  font-size: var(--font-size-md);
  color: var(--text-secondary);
}
.ws-saved {
  font-size: var(--font-size-sm);
  color: var(--status-success);
}
.ws-status {
  color: var(--text-secondary);
  font-size: var(--font-size-md);
  text-align: center;
  padding: var(--space-11) 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-5);
}
.ws-status--error {
  color: var(--status-danger);
}
.ws-alert {
  color: var(--status-danger);
  font-size: var(--font-size-md);
  margin: 0 0 var(--space-7);
}
.ws-search-empty {
  display: flex;
  justify-content: center;
  margin-bottom: var(--space-7);
}
.arcade-input:focus-visible {
  outline: var(--focus-ring-width) solid var(--color-focus-ring);
  outline-offset: 2px;
}
</style>
