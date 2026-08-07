/**
 * Typed library API wrappers. Every call checks `res.ok` once here so views
 * never treat a 500 as success.
 */
import { apiFetch } from '@/utils/api';
import { i18n } from '@/i18n';
import type { CardPayload, DeckCard, DeckOption, LibraryDeck } from './types';

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) {
    throw new Error(i18n.global.t('common.requestFailed', { status: res.status }));
  }
  // DELETE returns 204 with no body.
  if (res.status === 204) return undefined as T;
  const text = await res.text();
  if (!text) return undefined as T;
  return JSON.parse(text) as T;
}

export async function listDecks(): Promise<LibraryDeck[]> {
  const res = await apiFetch('/api/decks');
  const raw = await json<Record<string, unknown>[]>(res);
  return raw.map((d) => ({
    id: d.id as string,
    name: d.name as string,
    description: (d.description as string) ?? '',
    cardCount: (d.cardCount as number) ?? 0,
  }));
}

export async function createDeck(body: {
  name: string;
  description: string;
}): Promise<LibraryDeck> {
  const res = await apiFetch('/api/decks', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  const d = await json<Record<string, unknown>>(res);
  return {
    id: d.id as string,
    name: d.name as string,
    description: (d.description as string) ?? '',
    cardCount: (d.cardCount as number) ?? 0,
  };
}

export async function updateDeck(
  id: string,
  body: { name: string; description: string },
): Promise<LibraryDeck> {
  const res = await apiFetch(`/api/decks/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  const d = await json<Record<string, unknown>>(res);
  return {
    id: d.id as string,
    name: d.name as string,
    description: (d.description as string) ?? '',
    cardCount: (d.cardCount as number) ?? 0,
  };
}

export async function deleteDeck(id: string): Promise<void> {
  const res = await apiFetch(`/api/decks/${id}`, { method: 'DELETE' });
  await json<void>(res);
}

export async function listAllCards(): Promise<DeckCard[]> {
  const res = await apiFetch('/api/cards');
  return json<DeckCard[]>(res);
}

export async function listDeckCards(deckId: string): Promise<DeckCard[]> {
  const res = await apiFetch(`/api/decks/${deckId}/cards`);
  return json<DeckCard[]>(res);
}

/**
 * Empty optional fields are coerced to null (not ""), matching the DB column
 * contract previously enforced at CardManagementView create/update.
 */
function coerceCardPayload(form: {
  front: string;
  back: string;
  deckId: string | null | undefined;
  imageUrl?: string | null;
  notes?: string | null;
}): CardPayload {
  return {
    front: form.front,
    back: form.back,
    deckId: form.deckId || null,
    imageUrl: (form.imageUrl ?? '').trim() || null,
    notes: (form.notes ?? '').trim() || null,
  };
}

export async function createCard(form: {
  front: string;
  back: string;
  deckId: string | null | undefined;
  imageUrl?: string | null;
  notes?: string | null;
}): Promise<DeckCard> {
  const payload = coerceCardPayload(form);
  const res = await apiFetch('/api/cards', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return json<DeckCard>(res);
}

export async function updateCard(
  id: string,
  form: {
    front: string;
    back: string;
    deckId: string | null | undefined;
    imageUrl?: string | null;
    notes?: string | null;
  },
): Promise<DeckCard> {
  const payload = coerceCardPayload(form);
  const res = await apiFetch(`/api/cards/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return json<DeckCard>(res);
}

export async function deleteCard(id: string): Promise<void> {
  const res = await apiFetch(`/api/cards/${id}`, { method: 'DELETE' });
  await json<void>(res);
}

export async function reorderDeckCards(deckId: string, cardIds: string[]): Promise<DeckCard[]> {
  const res = await apiFetch(`/api/decks/${deckId}/cards/reorder`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ cardIds }),
  });
  return json<DeckCard[]>(res);
}

export async function listDeckOptions(): Promise<DeckOption[]> {
  const decks = await listDecks();
  return decks.map((d) => ({ id: d.id, name: d.name }));
}

export const libraryApi = {
  listDecks,
  createDeck,
  updateDeck,
  deleteDeck,
  listAllCards,
  listDeckCards,
  createCard,
  updateCard,
  deleteCard,
  reorderDeckCards,
  listDeckOptions,
};
