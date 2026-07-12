import { Router } from 'express';
import { DeckController } from '../controllers/DeckController';

const router = Router();
const deckController = new DeckController();

router.get('/', deckController.getAllDecks);
router.post('/', deckController.createDeck);
router.put('/:id', deckController.updateDeck);
router.delete('/:id', deckController.deleteDeck);

export default router;
