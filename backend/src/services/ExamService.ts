import ExamTemplate, { IExamTemplate } from '../models/ExamTemplate';
import Question, { IQuestion } from '../models/Question';
import ExamSession, { IExamSession } from '../models/ExamSession';
import mongoose from 'mongoose';

export class ExamService {
  // ─── Exam Templates ───────────────────────────────────────────────────────

  async listTemplates(userId: string): Promise<IExamTemplate[]> {
    // Return public (built-in) templates plus user's own custom ones
    return ExamTemplate.find({
      $or: [{ isPublic: true }, { userId: new mongoose.Types.ObjectId(userId) }],
    }).sort({ examType: 1, name: 1 });
  }

  async getTemplate(templateId: string): Promise<IExamTemplate | null> {
    return ExamTemplate.findById(templateId);
  }

  async createTemplate(
    userId: string,
    data: Partial<IExamTemplate>,
  ): Promise<IExamTemplate> {
    const template = new ExamTemplate({ ...data, userId, isPublic: false });
    return template.save();
  }

  async deleteTemplate(templateId: string, userId: string): Promise<boolean> {
    const result = await ExamTemplate.deleteOne({
      _id: templateId,
      userId,
      isPublic: false, // never allow deleting built-in templates
    });
    return result.deletedCount > 0;
  }

  // ─── Questions ────────────────────────────────────────────────────────────

  async listQuestions(examTemplateId: string): Promise<IQuestion[]> {
    return Question.find({ examTemplateId }).sort({ orderIndex: 1 });
  }

  async addQuestion(
    examTemplateId: string,
    userId: string,
    data: Partial<IQuestion>,
  ): Promise<IQuestion> {
    const count = await Question.countDocuments({ examTemplateId });
    const question = new Question({
      ...data,
      examTemplateId,
      userId,
      orderIndex: count,
    });
    // Update totalQuestions on template
    await ExamTemplate.findByIdAndUpdate(examTemplateId, { $inc: { totalQuestions: 1 } });
    return question.save();
  }

  async updateQuestion(questionId: string, userId: string, data: Partial<IQuestion>): Promise<IQuestion | null> {
    return Question.findOneAndUpdate(
      { _id: questionId, userId }, // only owner can edit (userId null for built-ins won't match)
      data,
      { new: true },
    );
  }

  async deleteQuestion(questionId: string, userId: string): Promise<boolean> {
    const q = await Question.findOne({ _id: questionId, userId });
    if (!q) return false;
    await q.deleteOne();
    await ExamTemplate.findByIdAndUpdate(q.examTemplateId, { $inc: { totalQuestions: -1 } });
    return true;
  }

  // ─── Exam Sessions ────────────────────────────────────────────────────────

  async startSession(userId: string, examTemplateId: string): Promise<IExamSession> {
    const template = await ExamTemplate.findById(examTemplateId);
    if (!template) throw new Error('Exam template not found');
    const questions = await Question.find({ examTemplateId }).sort({ orderIndex: 1 });

    // Initialise empty answer records
    const answers = questions.map((q) => ({
      questionId: q._id as mongoose.Types.ObjectId,
      userAnswer: '',
      isCorrect: false,
      timeTaken: 0,
    }));

    const session = new ExamSession({
      userId,
      examTemplateId,
      timeLimit: template.duration,
      answers,
      totalCount: questions.length,
    });
    return session.save();
  }

  async getUserSessions(userId: string): Promise<IExamSession[]> {
    return ExamSession.find({ userId })
      .populate('examTemplateId', 'name examType duration')
      .sort({ createdAt: -1 })
      .limit(50);
  }

  async getSession(sessionId: string, userId: string): Promise<IExamSession | null> {
    return ExamSession.findOne({ _id: sessionId, userId })
      .populate({
        path: 'examTemplateId',
        select: 'name examType duration passingScore',
      });
  }

  async submitAnswer(
    sessionId: string,
    userId: string,
    questionId: string,
    userAnswer: string,
    timeTaken: number,
  ): Promise<IExamSession | null> {
    const session = await ExamSession.findOne({ _id: sessionId, userId, status: 'in-progress' });
    if (!session) return null;

    const question = await Question.findById(questionId);
    if (!question) return null;

    const isCorrect = question.correctAnswer.toUpperCase() === userAnswer.toUpperCase();

    // Find existing answer index
    const idx = session.answers.findIndex((a) => a.questionId.toString() === questionId);
    if (idx !== -1) {
      session.answers[idx].userAnswer = userAnswer;
      session.answers[idx].isCorrect = isCorrect;
      session.answers[idx].timeTaken = timeTaken;
    }

    session.markModified('answers');
    return session.save();
  }

  async finishSession(
    sessionId: string,
    userId: string,
    status: 'completed' | 'abandoned' = 'completed',
  ): Promise<IExamSession | null> {
    const session = await ExamSession.findOne({ _id: sessionId, userId, status: 'in-progress' });
    if (!session) return null;

    const correctCount = session.answers.filter((a) => a.isCorrect).length;
    const totalCount = session.answers.length;
    const score = totalCount > 0 ? Math.round((correctCount / totalCount) * 100) : 0;

    session.finishedAt = new Date();
    session.correctCount = correctCount;
    session.totalCount = totalCount;
    session.score = score;
    session.status = status;

    return session.save();
  }

  async getSessionWithQuestions(sessionId: string, userId: string): Promise<any | null> {
    const session = await ExamSession.findOne({ _id: sessionId, userId })
      .populate('examTemplateId')
      .lean();
    if (!session) return null;

    const questionIds = session.answers.map((a: any) => a.questionId);
    const questions = await Question.find({ _id: { $in: questionIds } }).lean();

    const questionsMap: Record<string, any> = {};
    questions.forEach((q) => { questionsMap[q._id.toString()] = q; });

    return { ...session, questionsMap };
  }
}
