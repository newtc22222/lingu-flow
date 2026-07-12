import { Request, Response } from 'express';
import Deck from '../models/Deck';
import mongoose from 'mongoose';

export class DeckController {
  getAllDecks = async (req: Request, res: Response): Promise<void> => {
    try {
      const userId = (req as any).user.userId;
      const decks = await Deck.find({ userId: new mongoose.Types.ObjectId(userId) }).sort({ createdAt: -1 });
      res.json(decks);
    } catch (error: any) {
      res.status(500).json({ error: error.message });
    }
  };

  createDeck = async (req: Request, res: Response): Promise<void> => {
    try {
      const { name, description } = req.body;
      const userId = (req as any).user.userId;

      if (!name) {
        res.status(400).json({ error: 'Name is required' });
        return;
      }

      const deck = new Deck({
        userId: new mongoose.Types.ObjectId(userId),
        name,
        description
      });
      await deck.save();
      res.status(201).json(deck);
    } catch (error: any) {
      res.status(500).json({ error: error.message });
    }
  };

  updateDeck = async (req: Request, res: Response): Promise<void> => {
    try {
      const id = req.params.id as string;
      const { name, description } = req.body;
      const userId = (req as any).user.userId;

      const updatedDeck = await Deck.findOneAndUpdate(
        { _id: new mongoose.Types.ObjectId(id), userId: new mongoose.Types.ObjectId(userId) },
        { name, description },
        { new: true }
      );

      if (!updatedDeck) {
        res.status(404).json({ error: 'Deck not found' });
        return;
      }

      res.json(updatedDeck);
    } catch (error: any) {
      res.status(500).json({ error: error.message });
    }
  };

  deleteDeck = async (req: Request, res: Response): Promise<void> => {
    try {
      const id = req.params.id as string;
      const userId = (req as any).user.userId;

      const result = await Deck.deleteOne({
        _id: new mongoose.Types.ObjectId(id),
        userId: new mongoose.Types.ObjectId(userId)
      });

      if (result.deletedCount === 0) {
        res.status(404).json({ error: 'Deck not found' });
        return;
      }

      res.status(204).send();
    } catch (error: any) {
      res.status(500).json({ error: error.message });
    }
  };
}
