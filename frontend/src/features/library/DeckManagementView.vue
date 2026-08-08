<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';
import KeyboardGridList from '@/shared/components/KeyboardGridList.vue';
import PixelFrame from '@/shared/components/PixelFrame.vue';
import ConfirmDialog from '@/shared/components/ConfirmDialog.vue';
import AppButton from '@/shared/components/AppButton.vue';
import DeckForm, { type DeckFormModel } from './components/DeckForm.vue';
import ConsoleHeader from './components/ConsoleHeader.vue';
import HotkeysDialog, { type HotkeyGroup } from './components/HotkeysDialog.vue';
import { libraryApi } from './api';
import { useRovingList } from './composables/useRovingList';
import { UNFILED_ROW_ID, type LibraryDeck } from './types';

const { t } = useI18n();
const router = useRouter();

const shellRef = ref<HTMLElement | null>(null);
const searchInputRef = ref<HTMLInputElement | null>(null);
const formRef = ref<InstanceType<typeof DeckForm> | null>(null);
/** Bumped after a successful save so DeckForm remounts with a blank create form. */
const formKey = ref(0);

const realDecks = ref<LibraryDeck[]>([]);
const unfiledCount = ref<number | null>(null);
const isLoading = ref(true);
const isSaving = ref(false);
const formError = ref('');
const listError = ref('');
const liveMessage = ref('');
const searchQuery = ref('');

const isEditing = ref(false);
const editingDeck = ref<LibraryDeck | null>(null);

const showDeleteConfirm = ref(false);
const showHotkeys = ref(false);
const pendingDelete = ref<LibraryDeck | null>(null);
const focusAfterDialog = ref(-1);

// Any open modal must gag the shortcuts, or E/N/Del fire behind it.
const isBlocked = computed(() => showDeleteConfirm.value || showHotkeys.value);

function announce(msg: string) {
  liveMessage.value = '';
  nextTick(() => {
    liveMessage.value = msg;
  });
}

const filteredDecks = computed(() => {
  const q = searchQuery.value.trim().toLowerCase();
  if (!q) return realDecks.value;
  return realDecks.value.filter(
    (d) => d.name.toLowerCase().includes(q) || (d.description || '').toLowerCase().includes(q),
  );
});

/**
 * Synthetic Unfiled row is pinned last. Suppressed when the library is truly
 * empty so the shell empty state can fire (rows.length is otherwise never 0).
 */
const rows = computed(() => {
  const q = searchQuery.value.trim().toLowerCase();
  const unfiledName = t('library.unfiledName').toLowerCase();
  const unfiledDesc = t('library.unfiledDescription').toLowerCase();
  const unfiledMatches = !q || unfiledName.includes(q) || unfiledDesc.includes(q);

  // Only suppress Unfiled when we *know* count is zero. null (loading/failed)
  // still renders Unfiled without a count (§9 degrade-silently).
  const trulyEmpty = realDecks.value.length === 0 && unfiledCount.value === 0;
  if (trulyEmpty && !q) return [] as LibraryDeck[];

  const list = [...filteredDecks.value];
  if (unfiledMatches) {
    list.push({
      id: UNFILED_ROW_ID,
      name: t('library.unfiledName'),
      description: t('library.unfiledDescription'),
      cardCount: unfiledCount.value ?? -1,
    });
  }
  return list;
});

const emptyText = computed(() => {
  if (searchQuery.value.trim())
    return t('library.searchNoResults', { query: searchQuery.value.trim() });
  return t('decks.empty');
});

const hotkeyGroups = computed<HotkeyGroup[]>(() => [
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
]);

function canModify(d: LibraryDeck) {
  return d.id !== UNFILED_ROW_ID;
}

function openDeck(d: LibraryDeck) {
  if (d.id === UNFILED_ROW_ID) {
    router.push({ name: 'deck-unfiled' });
    return;
  }
  router.push({ name: 'deck-detail', params: { deckId: d.id } });
}

function startEdit(d: LibraryDeck) {
  if (!canModify(d)) return;
  editingDeck.value = d;
  isEditing.value = true;
  formError.value = '';
  nextTick(() => formRef.value?.focusFirstField());
}

function startNew() {
  editingDeck.value = null;
  isEditing.value = false;
  formError.value = '';
  nextTick(() => formRef.value?.focusFirstField());
}

function cancelEdit() {
  editingDeck.value = null;
  isEditing.value = false;
  formError.value = '';
}

function requestDelete(id: string) {
  const deck = realDecks.value.find((d) => d.id === id);
  if (!deck) return;
  pendingDelete.value = deck;
  focusAfterDialog.value = rows.value.findIndex((r) => r.id === id);
  showDeleteConfirm.value = true;
}

const deleteMessage = computed(() => {
  const deck = pendingDelete.value;
  if (!deck) return '';
  if (deck.cardCount > 0) {
    return t('library.deleteDeckWarning', { count: deck.cardCount });
  }
  return t('decks.confirmDelete');
});

async function confirmDelete() {
  const deck = pendingDelete.value;
  if (!deck) return;
  const restore = focusAfterDialog.value;
  try {
    await libraryApi.deleteDeck(deck.id);
    announce(t('library.a11y.deckDeleted'));
    pendingDelete.value = null;
    await fetchDecks();
    await nextTick();
    focusIndex(Math.min(restore, Math.max(0, rows.value.length - 1)));
  } catch (err) {
    listError.value = err instanceof Error ? err.message : String(err);
    await nextTick();
    focusIndex(restore >= 0 ? restore : 0);
  }
}

async function onDeleteCancel() {
  const restore = focusAfterDialog.value;
  pendingDelete.value = null;
  await nextTick();
  if (restore >= 0) focusIndex(restore);
}

async function saveDeck(payload: DeckFormModel) {
  isSaving.value = true;
  formError.value = '';
  try {
    if (editingDeck.value) {
      await libraryApi.updateDeck(editingDeck.value.id, payload);
      announce(t('library.a11y.deckUpdated'));
    } else {
      await libraryApi.createDeck(payload);
      announce(t('library.a11y.deckCreated'));
    }
    cancelEdit();
    formKey.value += 1;
    await fetchDecks();
  } catch (err) {
    formError.value = err instanceof Error ? err.message : String(err);
  } finally {
    isSaving.value = false;
  }
}

async function fetchDecks() {
  isLoading.value = true;
  listError.value = '';
  try {
    realDecks.value = await libraryApi.listDecks();
  } catch (err) {
    listError.value = err instanceof Error ? err.message : String(err);
  } finally {
    isLoading.value = false;
  }
}

/** Unfiled count loads after first paint — never block the rack on it. */
async function fetchUnfiledCount() {
  try {
    const cards = await libraryApi.listAllCards();
    unfiledCount.value = cards.filter((c) => !c.deckId).length;
  } catch (err) {
    console.error('Failed to count unfiled cards:', err);
    unfiledCount.value = null;
  }
}

function focusSearch() {
  searchInputRef.value?.focus();
  searchInputRef.value?.select();
}

const { activeIndex, focusIndex, onRowFocus } = useRovingList<LibraryDeck>({
  containerRef: shellRef,
  items: rows,
  canModify,
  onActivate: (item) => openDeck(item),
  onEdit: (item) => startEdit(item),
  onDelete: (item) => requestDelete(item.id),
  onNew: () => startNew(),
  onSearch: () => focusSearch(),
  onHelp: () => {
    showHotkeys.value = true;
  },
  announce,
  isBlocked,
  searchQuery,
  searchInputRef,
  isEditing,
  onCancelEdit: () => cancelEdit(),
});

let searchAnnounceTimer: ReturnType<typeof setTimeout> | null = null;
watch(searchQuery, () => {
  if (searchAnnounceTimer) clearTimeout(searchAnnounceTimer);
  searchAnnounceTimer = setTimeout(() => {
    const q = searchQuery.value.trim();
    if (!q) return;
    if (rows.value.length === 0) {
      announce(t('library.searchNoResults', { query: q }));
    }
  }, 250);
});

onMounted(async () => {
  await fetchDecks();
  fetchUnfiledCount();
});
</script>

<template>
  <div ref="shellRef" class="deck-rack">
    <div class="sr-only" role="status" aria-live="polite" aria-atomic="true">{{ liveMessage }}</div>

    <ConsoleHeader
      :title="t('decks.title')"
      :count="isLoading ? -1 : realDecks.length"
      :count-label="t('decks.countLabel')"
    >
      <template #actions>
        <AppButton variant="secondary" @click="showHotkeys = true">
          ? {{ t('library.hotkeys') }}
        </AppButton>
      </template>
    </ConsoleHeader>

    <div class="rack-body">
      <!-- Left: create / edit form -->
      <section class="rack-compose" :aria-label="t('library.composeBay')">
        <div class="rack-bay-label font-label">{{ t('library.composeBay') }}</div>
        <PixelFrame frame-color="amber" surface="cabinet" :ring-width="3">
          <DeckForm
            :key="formKey"
            ref="formRef"
            :deck="
              editingDeck ? { name: editingDeck.name, description: editingDeck.description } : null
            "
            :is-saving="isSaving"
            :error="formError"
            :framed="false"
            @submit="saveDeck"
            @cancel="cancelEdit"
          />
        </PixelFrame>
      </section>

      <!-- Right: deck list -->
      <section class="rack-list" :aria-label="t('library.deckListBay')">
        <div class="rack-bay-label font-label">{{ t('library.deckListBay') }}</div>

        <div class="rack-toolbar">
          <label class="sr-only" for="deck-search">{{ t('library.search') }}</label>
          <input
            id="deck-search"
            ref="searchInputRef"
            v-model="searchQuery"
            type="search"
            class="arcade-input rack-search"
            :placeholder="t('library.searchPlaceholder')"
          />
          <AppButton v-if="searchQuery.trim()" variant="secondary" @click="searchQuery = ''">
            {{ t('library.clearSearch') }}
          </AppButton>
        </div>

        <p v-if="listError" class="rack-error font-body" role="alert">
          {{ listError }}
          <AppButton variant="secondary" @click="fetchDecks">{{ t('common.retry') }}</AppButton>
        </p>

        <KeyboardGridList
          :rows="rows"
          :is-loading="isLoading"
          :loading-text="t('decks.loading')"
          :empty-text="emptyText"
          :list-label="t('library.a11y.deckList')"
          :active-index="activeIndex"
          :can-modify="canModify"
          @edit="startEdit"
          @delete="requestDelete"
          @row-activate="(item) => openDeck(item)"
          @row-focus="onRowFocus"
        >
          <template #row="{ item }">
            <RouterLink
              :to="
                item.id === UNFILED_ROW_ID
                  ? { name: 'deck-unfiled' }
                  : { name: 'deck-detail', params: { deckId: item.id } }
              "
              class="deck-row-link"
              tabindex="-1"
              @click.stop
            >
              <div class="deck-row-name font-body">{{ item.name }}</div>
              <div class="deck-row-desc font-body">{{ item.description }}</div>
              <div class="deck-row-meta font-label">
                <span v-if="item.cardCount >= 0">{{
                  t('decks.cardCount', { count: item.cardCount })
                }}</span>
                <span class="deck-row-open">{{ t('decks.open') }} →</span>
              </div>
            </RouterLink>
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
      :title="t('library.confirmDeleteDeckTitle')"
      :message="deleteMessage"
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
.deck-rack {
  width: 100%;
  box-sizing: border-box;
  padding: var(--space-9) var(--space-9) var(--space-8);
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}
@media (min-width: 768px) {
  .deck-rack {
    flex: 1 1 0;
    min-height: 0;
    overflow: hidden;
  }
}

.rack-body {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--space-7);
}
@media (min-width: 768px) {
  .rack-body {
    flex: 1 1 0;
    min-height: 0;
    grid-template-columns: minmax(0, 2fr) minmax(0, 3fr);
    align-items: start;
    overflow: hidden;
  }
}

.rack-bay-label {
  font-size: var(--font-size-2xs);
  letter-spacing: var(--tracking-wide);
  color: var(--text-secondary);
  margin: 0 0 var(--space-3);
  flex-shrink: 0;
}

/*
 * The deck form is two fields — the bay hugs it rather than stretching to
 * full height, which would recreate the empty space this layout removes.
 */
.rack-compose {
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.rack-compose .rack-bay-label {
  color: var(--text-label-accent);
}
@media (min-width: 768px) {
  .rack-compose {
    max-height: 100%;
    overflow-y: auto;
  }
}

.rack-list {
  display: flex;
  flex-direction: column;
  min-width: 0;
}
@media (min-width: 768px) {
  .rack-list {
    min-height: 0;
    height: 100%;
    overflow: hidden;
  }
}

.rack-toolbar {
  display: flex;
  align-items: center;
  gap: var(--space-5);
  flex-wrap: wrap;
  margin-bottom: var(--space-6);
  flex-shrink: 0;
}

.rack-error {
  color: var(--status-danger);
  font-size: var(--font-size-md);
  margin: 0 0 var(--space-7);
  display: flex;
  align-items: center;
  gap: var(--space-5);
  flex-wrap: wrap;
  flex-shrink: 0;
}
.rack-search {
  min-width: 160px;
  flex: 1 1 auto;
  max-width: 320px;
}
.deck-row-link {
  display: block;
  text-decoration: none;
  color: inherit;
}
.deck-row-open {
  display: inline-block;
  font-size: var(--font-size-2xs);
  letter-spacing: var(--tracking-normal);
  color: var(--text-label-accent);
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
.deck-row-meta {
  display: flex;
  align-items: center;
  gap: var(--space-6);
  margin-top: var(--space-3);
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}
.arcade-input:focus-visible {
  outline: var(--focus-ring-width) solid var(--color-focus-ring);
  outline-offset: 2px;
}
</style>
