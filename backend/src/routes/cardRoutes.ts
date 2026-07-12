import { Router } from 'express';
import { CardController } from '../controllers/CardController';
import { CardService } from '../services/CardService';

const router = Router();

// Dependency Injection
const cardService = new CardService();
const cardController = new CardController(cardService);

router.get('/study', cardController.getCardsToStudy);
router.post('/review/:id', cardController.reviewCard);
router.post('/', cardController.addCard);
router.get('/', cardController.getAllCards);
router.put('/:id', cardController.updateCard);
router.delete('/:id', cardController.deleteCard);

export default router;
