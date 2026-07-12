import mongoose, { Schema, Document } from 'mongoose';

export interface ISRSData {
  interval: number;
  easeFactor: number;
  repetitions: number;
  nextReviewDate: Date;
}

export interface ICard extends Document {
  userId: mongoose.Types.ObjectId;
  deckId?: mongoose.Types.ObjectId;
  front: string;
  back: string;
  srsData: ISRSData;
}

const SRSSchema: Schema = new Schema({
  interval: { type: Number, default: 0 },
  easeFactor: { type: Number, default: 2.5 },
  repetitions: { type: Number, default: 0 },
  nextReviewDate: { type: Date, default: Date.now },
}, { _id: false });

const CardSchema: Schema = new Schema({
  userId: { type: Schema.Types.ObjectId, ref: 'User', required: true },
  deckId: { type: Schema.Types.ObjectId, ref: 'Deck' },
  front: { type: String, required: true },
  back: { type: String, required: true },
  srsData: { type: SRSSchema, default: () => ({}) },
}, { timestamps: true });

export default mongoose.model<ICard>('Card', CardSchema);
