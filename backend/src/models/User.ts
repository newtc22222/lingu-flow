import mongoose, { Schema, Document } from 'mongoose';

export interface IUser extends Document {
  username?: string;
  email?: string;
  passwordHash?: string;
  googleId?: string;
  isGuest: boolean;
  dailyStreak: number;
  lastActive: Date;
}

const UserSchema: Schema = new Schema({
  username: { type: String, unique: true, sparse: true },
  email: { type: String, unique: true, sparse: true },
  passwordHash: { type: String },
  googleId: { type: String, unique: true, sparse: true },
  isGuest: { type: Boolean, default: false },
  dailyStreak: { type: Number, default: 0 },
  lastActive: { type: Date, default: Date.now },
}, { timestamps: true });

export default mongoose.model<IUser>('User', UserSchema);
