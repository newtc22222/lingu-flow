import Card, { ICard } from '../models/Card';
import { calculateSM2 } from '../utils/sm2';
import mongoose from 'mongoose';

export class CardService {
  /**
   * Fetch all active cards for a user where nextReviewDate <= current time
   */
  async getCardsToStudy(userId: string): Promise<ICard[]> {
    const now = new Date();
    return await Card.find({
      userId: new mongoose.Types.ObjectId(userId),
      'srsData.nextReviewDate': { $lte: now },
    });
  }

  /**
   * Process a review score for a card and update its SRS data
   */
  async processReview(cardId: string, userId: string, score: number): Promise<ICard | null> {
    const card = await Card.findOne({
      _id: new mongoose.Types.ObjectId(cardId),
      userId: new mongoose.Types.ObjectId(userId),
    });

    if (!card) {
      return null;
    }

    // Map 1-4 scale from frontend to 0-5 scale for SM-2 if needed. 
    // Assuming score is 1-4. Map: 1 -> 0 (Blackout), 2 -> 2 (Hard), 3 -> 4 (Good), 4 -> 5 (Easy)
    // For simplicity, we just assume the frontend sends a mapped 0-5 score, or we map it here:
    let sm2Quality = score; // Default to direct mapping if frontend handles it
    if (score === 1) sm2Quality = 0;
    else if (score === 2) sm2Quality = 2;
    else if (score === 3) sm2Quality = 4;
    else if (score === 4) sm2Quality = 5;
    
    card.srsData = calculateSM2(card.srsData, sm2Quality);
    
    await card.save();
    return card;
  }

  /**
   * Add a new card
   */
  async addCard(userId: string, front: string, back: string, deckId?: string): Promise<ICard> {
    const cardData: any = {
      userId: new mongoose.Types.ObjectId(userId),
      front,
      back,
    };
    if (deckId) {
      cardData.deckId = new mongoose.Types.ObjectId(deckId);
    }
    const card = new Card(cardData);
    await card.save();
    return card;
  }

  /**
   * Fetch all cards for a user (not just due cards)
   */
  async getAllCards(userId: string): Promise<ICard[]> {
    return await Card.find({
      userId: new mongoose.Types.ObjectId(userId),
    }).sort({ createdAt: -1 });
  }

  /**
   * Update an existing card
   */
  async updateCard(cardId: string, userId: string, front: string, back: string): Promise<ICard | null> {
    const card = await Card.findOneAndUpdate(
      {
        _id: new mongoose.Types.ObjectId(cardId),
        userId: new mongoose.Types.ObjectId(userId),
      },
      { front, back },
      { new: true }
    );
    return card;
  }

  /**
   * Delete a card
   */
  async deleteCard(cardId: string, userId: string): Promise<boolean> {
    const result = await Card.deleteOne({
      _id: new mongoose.Types.ObjectId(cardId),
      userId: new mongoose.Types.ObjectId(userId),
    });
    return result.deletedCount === 1;
  }
}
