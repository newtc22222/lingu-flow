<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';
import KeyboardGridList from '@/shared/components/KeyboardGridList.vue';
import PixelFrame from '@/shared/components/PixelFrame.vue';
import ConfirmDialog from '@/shared/components/ConfirmDialog.vue';
import AppButton from '@/shared/components/AppButton.vue';
import CardForm, { type CardFormModel } from './components/CardForm.vue';
import CardRow from './components/CardRow.vue';
import ConsoleHeader from './components/ConsoleHeader.vue';
import HotkeysDialog, { type HotkeyGroup } from './components/HotkeysDialog.vue';
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
const showHotkeys = ref(false);
const pendingDeleteId = ref<string | null>(null);
const focusAfterDialog = ref(-1);

const draggingIndex = ref<number | null>(null);
const savedOrder = ref<string[]>([]);

// Any open modal must gag the shortcuts, or E/N/Del fire behind it.
const isBlocked = computed(() => showDeleteConfirm.value || showHotkeys.value);

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
  // Unfiled is not a deck, and having nothing in it is a healthy state.
  if (isUnfiled.value) return t('library.unfiledEmpty');
  return t('deckDetail.empty');
});

/**
 * The legend plate tracks machine state: the ORDER group is always listed, but
 * on Unfiled it arrives muted with the reason attached rather than vanishing
 * and leaving the user to wonder where the keys went.
 */
const hotkeyGroups = computed<HotkeyGroup[]>(() => {
  const orderItems = [
    { keys: ['Alt', '↑/↓'], label: t('library.legend.reorder') },
    { keys: ['S'], label: t('library.legend.saveOrder') },
  ];
  return [
    {
      label: t('library.legend.groups.navigate'),
      items: [
        { keys: ['↑', '↓'], label: t('library.legend.navigate') },
        { keys: ['↵'], label: t('library.legend.open') },
        { keys: ['/'], label: t('library.legend.search') },
        { keys: ['Esc'], label: t('library.legend.cancel') },
      ],
    },
    {
      label: t('library.legend.groups.edit'),
      items: [
        { keys: ['E'], label: t('library.legend.edit') },
        { keys: ['N'], label: t('library.legend.new') },
        { keys: ['Del'], label: t('library.legend.delete') },
      ],
    },
    {
      label: t('library.legend.groups.order'),
      items: orderItems,
      note: isUnfiled.value
        ? t('library.reorderDisabled')
        : canReorder.value
          ? undefined
          : t('library.reorderWhileFiltered'),
    },
  ];
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
  onHelp: () => {
    showHotkeys.value = true;
  },
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

    <ConsoleHeader
      :title="isLoading ? t('deckDetail.loading') : deckName"
      :back-label="t('library.backToDecks')"
      @back="router.push({ name: 'decks' })"
    >
      <template #actions>
        <AppButton variant="secondary" @click="showHotkeys = true">
          ? {{ t('library.hotkeys') }}
        </AppButton>
        <template v-if="!isUnfiled && !isLoading && !notFound && !loadError">
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
        </template>
      </template>
    </ConsoleHeader>

    <p v-if="isLoading" class="ws-status font-label">{{ t('deckDetail.loading') }}</p>
    <p v-else-if="notFound" class="ws-status ws-status--error font-label">
      {{ t('deckDetail.notFound') }}
    </p>
    <p v-else-if="loadError" class="ws-status ws-status--error font-body" role="alert">
      {{ loadError }}
      <AppButton variant="secondary" @click="fetchWorkspace">{{ t('common.retry') }}</AppButton>
    </p>

    <div v-else class="ws-body">
      <!-- Left: create / edit form -->
      <section class="ws-compose" :aria-label="t('library.composeBay')">
        <div class="ws-bay-label font-label">{{ t('library.composeBay') }}</div>
        <PixelFrame frame-color="amber" surface="cabinet" :ring-width="3" class="ws-compose-frame">
          <div class="ws-compose-scroll">
            <CardForm
              :key="formKey"
              ref="formRef"
              :card="editingFormModel()"
              :decks="allDecks"
              :default-deck-id="props.deckId"
              :is-saving="isSaving"
              :error="formError"
              :show-deck-select="true"
              :framed="false"
              @submit="saveCard"
              @cancel="cancelEdit"
            />
          </div>
        </PixelFrame>
      </section>

      <!-- Right: card list -->
      <section class="ws-list" :aria-label="t('library.cardListBay')">
        <div class="ws-bay-label font-label">{{ t('library.cardListBay') }}</div>

        <div class="ws-toolbar">
          <label class="sr-only" for="card-search">{{ t('library.search') }}</label>
          <input
            id="card-search"
            ref="searchInputRef"
            v-model="searchQuery"
            type="search"
            class="arcade-input ws-search"
            :placeholder="t('library.searchPlaceholder')"
          />
          <span class="ws-count font-label">
            {{ filteredCards.length }} {{ t('cards.countLabel') }}
          </span>
          <AppButton v-if="searchQuery.trim()" variant="secondary" @click="searchQuery = ''">
            {{ t('library.clearSearch') }}
          </AppButton>
          <AppButton variant="secondary" @click="startNew">
            {{ t('library.addCard') }}
          </AppButton>
        </div>

        <!-- Reorder controls belong with the list they reorder, not the form. -->
        <div v-if="canReorder && cards.length > 0" class="ws-reorder-bar">
          <span class="ws-hint font-body">{{ t('deckDetail.reorderHint') }}</span>
          <span v-if="orderSaved && !isDirty" class="ws-saved font-label">
            {{ t('deckDetail.orderSaved') }}
          </span>
          <AppButton :disabled="!isDirty || isSavingOrder" @click="saveOrder">
            {{ t('deckDetail.saveOrder') }}
          </AppButton>
        </div>

        <p v-if="listError" class="ws-alert font-body" role="alert">{{ listError }}</p>

        <KeyboardGridList
          :rows="filteredCards"
          :is-loading="false"
          :loading-text="t('deckDetail.loading')"
          :empty-text="emptyText"
          :list-label="t('library.a11y.cardList')"
          :active-index="activeIndex"
          :draggable-rows="canReorder"
          @edit="startEdit"
          @delete="requestDelete"
          @row-activate="(item) => startEdit(item)"
          @row-focus="onRowFocus"
          @row-dragstart="onDragStart"
          @row-dragenter="onDragEnter"
          @row-dragend="onDragEnd"
        >
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
        </KeyboardGridList>
      </section>
    </div>

    <HotkeysDialog
      v-model:is-open="showHotkeys"
      :title="t('library.hotkeysTitle')"
      :groups="hotkeyGroups"
    />

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
/*
 * Full-bleed console — but only where there is height to split. Below 768px
 * the two bays stack and the page scrolls normally; pinning the viewport there
 * leaves the list fighting the form for ~90px and losing.
 */
.deck-workspace {
  width: 100%;
  box-sizing: border-box;
  padding: var(--space-9) var(--space-9) var(--space-8);
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}
@media (min-width: 768px) {
  .deck-workspace {
    flex: 1 1 0;
    min-height: 0;
    overflow: hidden;
  }
}

.ws-body {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--space-7);
}
@media (min-width: 768px) {
  .ws-body {
    flex: 1 1 0;
    min-height: 0;
    grid-template-columns: minmax(0, 2fr) minmax(0, 3fr);
    align-items: stretch;
    overflow: hidden;
  }
}

.ws-bay-label {
  font-size: var(--font-size-2xs);
  letter-spacing: var(--tracking-wide);
  color: var(--text-secondary);
  margin: 0 0 var(--space-3);
  flex-shrink: 0;
}

/* CardForm is six fields plus a live preview — this bay fills and scrolls. */
.ws-compose {
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.ws-compose .ws-bay-label {
  color: var(--text-label-accent);
}
@media (min-width: 768px) {
  .ws-compose {
    min-height: 0;
    height: 100%;
  }
  .ws-compose-frame {
    flex: 1 1 auto;
    min-height: 0;
    overflow: hidden;
  }
  .ws-compose-scroll {
    height: 100%;
    overflow-x: hidden;
    overflow-y: auto;
  }
}

.ws-list {
  display: flex;
  flex-direction: column;
  min-width: 0;
}
@media (min-width: 768px) {
  .ws-list {
    min-height: 0;
    overflow: hidden;
  }
}

.ws-toolbar {
  display: flex;
  align-items: center;
  gap: var(--space-5);
  flex-wrap: wrap;
  margin-bottom: var(--space-6);
  flex-shrink: 0;
}
.ws-count {
  font-size: var(--font-size-base);
  font-weight: 700;
  letter-spacing: var(--tracking-normal);
  color: var(--color-accent);
  background: var(--surface-page);
  border: var(--space-1) solid var(--color-accent);
  padding: var(--space-2) var(--space-5);
  flex-shrink: 0;
}
.ws-search {
  min-width: 160px;
  flex: 1 1 auto;
  max-width: 280px;
}
.ws-reorder-bar {
  display: flex;
  align-items: center;
  gap: var(--space-7);
  flex-wrap: wrap;
  margin-bottom: var(--space-6);
  flex-shrink: 0;
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
  margin: 0 0 var(--space-6);
  flex-shrink: 0;
}
.arcade-input:focus-visible {
  outline: var(--focus-ring-width) solid var(--color-focus-ring);
  outline-offset: 2px;
}
</style>
