import mongoose, { Schema, Document } from 'mongoose';

export type ExamType = 'toeic' | 'ielts' | 'hsk' | 'jlpt' | 'custom';

export interface IExamTemplate extends Document {
  name: string;
  examType: ExamType;
  description: string;
  duration: number; // minutes
  totalQuestions: number;
  passingScore: number; // percentage
  tags: string[];
  isPublic: boolean; // true = built-in/seed
  userId?: mongoose.Types.ObjectId; // null for built-in
  level?: string; // e.g. "N5", "HSK 2", "Part 5"
  createdAt: Date;
  updatedAt: Date;
}

const ExamTemplateSchema: Schema = new Schema({
  name: { type: String, required: true },
  examType: { type: String, enum: ['toeic', 'ielts', 'hsk', 'jlpt', 'custom'], required: true },
  description: { type: String, default: '' },
  duration: { type: Number, required: true }, // minutes
  totalQuestions: { type: Number, required: true },
  passingScore: { type: Number, default: 60 }, // percent
  tags: [{ type: String }],
  isPublic: { type: Boolean, default: false },
  userId: { type: Schema.Types.ObjectId, ref: 'User' },
  level: { type: String },
}, { timestamps: true });

export default mongoose.model<IExamTemplate>('ExamTemplate', ExamTemplateSchema);
