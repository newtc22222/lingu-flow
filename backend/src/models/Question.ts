import mongoose, { Schema, Document } from 'mongoose';

export type QuestionType = 'multiple-choice';

export interface IQuestion extends Document {
  examTemplateId: mongoose.Types.ObjectId;
  userId?: mongoose.Types.ObjectId; // null for built-in seeded questions
  questionText: string;
  type: QuestionType;
  passage?: string; // optional reading passage for context
  options: string[]; // exactly 4 for MCQ (A/B/C/D)
  correctAnswer: string; // e.g. "A", "B", "C", or "D"
  explanation?: string;
  tags: string[];
  difficulty: 'easy' | 'medium' | 'hard';
  orderIndex: number; // order within the exam
  createdAt: Date;
  updatedAt: Date;
}

const QuestionSchema: Schema = new Schema({
  examTemplateId: { type: Schema.Types.ObjectId, ref: 'ExamTemplate', required: true },
  userId: { type: Schema.Types.ObjectId, ref: 'User' },
  questionText: { type: String, required: true },
  type: { type: String, enum: ['multiple-choice'], default: 'multiple-choice' },
  passage: { type: String },
  options: [{ type: String }],
  correctAnswer: { type: String, required: true }, // "A" | "B" | "C" | "D"
  explanation: { type: String },
  tags: [{ type: String }],
  difficulty: { type: String, enum: ['easy', 'medium', 'hard'], default: 'medium' },
  orderIndex: { type: Number, default: 0 },
}, { timestamps: true });

export default mongoose.model<IQuestion>('Question', QuestionSchema);
