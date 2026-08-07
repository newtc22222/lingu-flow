/** Mirrors `CardResponse` in `backend/app/schemas/card.py`. */
export interface DeckCard {
  id: string;
  deckId?: string | null;
  front: string;
  back: string;
  position: number;
  imageUrl?: string | null;
  notes?: string | null;
}

export interface LibraryDeck {
  id: string;
  name: string;
  description: string;
  cardCount: number;
}

export interface DeckOption {
  id: string;
  name: string;
}

export interface CardPayload {
  front: string;
  back: string;
  deckId: string | null;
  imageUrl: string | null;
  notes: string | null;
}

/** Synthetic rack row id for the Unfiled workspace entry. */
export const UNFILED_ROW_ID = '__unfiled__';
