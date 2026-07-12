import mongoose, { Schema, Document } from 'mongoose';

export interface IDeck extends Document {
  userId: mongoose.Types.ObjectId;
  name: string;
  description?: string;
  createdAt: Date;
  updatedAt: Date;
}

const DeckSchema: Schema = new Schema({
  userId: { type: Schema.Types.ObjectId, ref: 'User', required: true },
  name: { type: String, required: true },
  description: { type: String },
}, { timestamps: true });

export default mongoose.model<IDeck>('Deck', DeckSchema);
