import mongoose, { Schema, Document } from 'mongoose';

export interface IAnswerRecord {
  questionId: mongoose.Types.ObjectId;
  userAnswer: string; // "A" | "B" | "C" | "D" | "" (unanswered)
  isCorrect: boolean;
  timeTaken: number; // seconds spent on this question
}

export interface IExamSession extends Document {
  userId: mongoose.Types.ObjectId;
  examTemplateId: mongoose.Types.ObjectId;
  startedAt: Date;
  finishedAt?: Date;
  timeLimit: number; // minutes (copied from template at start time)
  answers: IAnswerRecord[];
  score: number; // percentage 0–100
  correctCount: number;
  totalCount: number;
  status: 'in-progress' | 'completed' | 'abandoned';
  createdAt: Date;
  updatedAt: Date;
}

const AnswerRecordSchema: Schema = new Schema({
  questionId: { type: Schema.Types.ObjectId, ref: 'Question', required: true },
  userAnswer: { type: String, default: '' },
  isCorrect: { type: Boolean, default: false },
  timeTaken: { type: Number, default: 0 },
}, { _id: false });

const ExamSessionSchema: Schema = new Schema({
  userId: { type: Schema.Types.ObjectId, ref: 'User', required: true },
  examTemplateId: { type: Schema.Types.ObjectId, ref: 'ExamTemplate', required: true },
  startedAt: { type: Date, default: Date.now },
  finishedAt: { type: Date },
  timeLimit: { type: Number, required: true },
  answers: [AnswerRecordSchema],
  score: { type: Number, default: 0 },
  correctCount: { type: Number, default: 0 },
  totalCount: { type: Number, default: 0 },
  status: { type: String, enum: ['in-progress', 'completed', 'abandoned'], default: 'in-progress' },
}, { timestamps: true });

export default mongoose.model<IExamSession>('ExamSession', ExamSessionSchema);
