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
