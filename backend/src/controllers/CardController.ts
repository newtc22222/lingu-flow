import { Request, Response } from 'express';
import { CardService } from '../services/CardService';
import { sseEmitter } from '../app';

export class CardController {
  private cardService: CardService;

  constructor(cardService: CardService) {
    this.cardService = cardService;
  }

  getCardsToStudy = async (req: Request, res: Response): Promise<void> => {
    try {
      const userId = (req as any).user.userId; 
      
      const cards = await this.cardService.getCardsToStudy(userId);
      res.json(cards);
    } catch (error: any) {
      res.status(500).json({ error: error.message });
    }
  };

  reviewCard = async (req: Request, res: Response): Promise<void> => {
    try {
      const { id } = req.params;
      const { score } = req.body;
      const userId = (req as any).user.userId;

      if (score === undefined) {
        res.status(400).json({ error: 'Score is required' });
        return;
      }

      const updatedCard = await this.cardService.processReview(id as string, userId, score);
      
      if (!updatedCard) {
        res.status(404).json({ error: 'Card not found' });
        return;
      }

      // Trigger SSE update for the user's progress/streak
      sseEmitter.emit('progress', {
        userId,
        message: 'Card reviewed successfully',
        cardId: updatedCard._id,
        nextReview: updatedCard.srsData.nextReviewDate,
      });

      res.json(updatedCard);
    } catch (error: any) {
      res.status(500).json({ error: error.message });
    }
  };

  addCard = async (req: Request, res: Response): Promise<void> => {
    try {
      const { front, back, deckId } = req.body;
      const userId = (req as any).user.userId;

      if (!front || !back) {
        res.status(400).json({ error: 'Front and back are required' });
        return;
      }

      const newCard = await this.cardService.addCard(userId, front, back, deckId);
      res.status(201).json(newCard);
    } catch (error: any) {
      res.status(500).json({ error: error.message });
    }
  };

  getAllCards = async (req: Request, res: Response): Promise<void> => {
    try {
      const userId = (req as any).user.userId;
      const cards = await this.cardService.getAllCards(userId);
      res.json(cards);
    } catch (error: any) {
      res.status(500).json({ error: error.message });
    }
  };

  updateCard = async (req: Request, res: Response): Promise<void> => {
    try {
      const id = req.params.id as string;
      const { front, back } = req.body;
      const userId = (req as any).user.userId;

      if (!front || !back) {
        res.status(400).json({ error: 'Front and back are required' });
        return;
      }

      const updatedCard = await this.cardService.updateCard(id, userId, front, back);
      
      if (!updatedCard) {
        res.status(404).json({ error: 'Card not found' });
        return;
      }

      res.json(updatedCard);
    } catch (error: any) {
      res.status(500).json({ error: error.message });
    }
  };

  deleteCard = async (req: Request, res: Response): Promise<void> => {
    try {
      const id = req.params.id as string;
      const userId = (req as any).user.userId;

      const success = await this.cardService.deleteCard(id, userId);
      
      if (!success) {
        res.status(404).json({ error: 'Card not found' });
        return;
      }

      res.status(204).send();
    } catch (error: any) {
      res.status(500).json({ error: error.message });
    }
  };
}
