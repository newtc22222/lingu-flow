import { Request, Response } from 'express';
import { ExamService } from '../services/ExamService';

// Helper: safely extract a single param string
const param = (p: string | string[]): string => (Array.isArray(p) ? p[0] : p);

export class ExamController {
  constructor(private examService: ExamService) {}

  // ─── Templates ────────────────────────────────────────────────────────────

  listTemplates = async (req: Request, res: Response): Promise<void> => {
    try {
      const userId = (req as any).user.id;
      const templates = await this.examService.listTemplates(userId);
      res.json(templates);
    } catch (err) {
      res.status(500).json({ error: 'Failed to list templates' });
    }
  };

  getTemplate = async (req: Request, res: Response): Promise<void> => {
    try {
      const template = await this.examService.getTemplate(param(req.params.id));
      if (!template) { res.status(404).json({ error: 'Not found' }); return; }
      res.json(template);
    } catch (err) {
      res.status(500).json({ error: 'Failed to get template' });
    }
  };

  createTemplate = async (req: Request, res: Response): Promise<void> => {
    try {
      const userId = (req as any).user.id;
      const template = await this.examService.createTemplate(userId, req.body);
      res.status(201).json(template);
    } catch (err) {
      res.status(500).json({ error: 'Failed to create template' });
    }
  };

  deleteTemplate = async (req: Request, res: Response): Promise<void> => {
    try {
      const userId = (req as any).user.id;
      const ok = await this.examService.deleteTemplate(param(req.params.id), userId);
      if (!ok) { res.status(404).json({ error: 'Not found or not authorized' }); return; }
      res.json({ success: true });
    } catch (err) {
      res.status(500).json({ error: 'Failed to delete template' });
    }
  };

  // ─── Questions ────────────────────────────────────────────────────────────

  listQuestions = async (req: Request, res: Response): Promise<void> => {
    try {
      const questions = await this.examService.listQuestions(param(req.params.examId));
      res.json(questions);
    } catch (err) {
      res.status(500).json({ error: 'Failed to list questions' });
    }
  };

  addQuestion = async (req: Request, res: Response): Promise<void> => {
    try {
      const userId = (req as any).user.id;
      const question = await this.examService.addQuestion(param(req.params.examId), userId, req.body);
      res.status(201).json(question);
    } catch (err) {
      res.status(500).json({ error: 'Failed to add question' });
    }
  };

  updateQuestion = async (req: Request, res: Response): Promise<void> => {
    try {
      const userId = (req as any).user.id;
      const question = await this.examService.updateQuestion(param(req.params.id), userId, req.body);
      if (!question) { res.status(404).json({ error: 'Not found or not authorized' }); return; }
      res.json(question);
    } catch (err) {
      res.status(500).json({ error: 'Failed to update question' });
    }
  };

  deleteQuestion = async (req: Request, res: Response): Promise<void> => {
    try {
      const userId = (req as any).user.id;
      const ok = await this.examService.deleteQuestion(param(req.params.id), userId);
      if (!ok) { res.status(404).json({ error: 'Not found or not authorized' }); return; }
      res.json({ success: true });
    } catch (err) {
      res.status(500).json({ error: 'Failed to delete question' });
    }
  };

  // ─── Sessions ─────────────────────────────────────────────────────────────

  startSession = async (req: Request, res: Response): Promise<void> => {
    try {
      const userId = (req as any).user.id;
      const { examTemplateId } = req.body;
      const session = await this.examService.startSession(userId, examTemplateId);
      res.status(201).json(session);
    } catch (err: any) {
      res.status(500).json({ error: err.message || 'Failed to start session' });
    }
  };

  getUserSessions = async (req: Request, res: Response): Promise<void> => {
    try {
      const userId = (req as any).user.id;
      const sessions = await this.examService.getUserSessions(userId);
      res.json(sessions);
    } catch (err) {
      res.status(500).json({ error: 'Failed to get sessions' });
    }
  };

  getSession = async (req: Request, res: Response): Promise<void> => {
    try {
      const userId = (req as any).user.id;
      const session = await this.examService.getSession(param(req.params.id), userId);
      if (!session) { res.status(404).json({ error: 'Not found' }); return; }
      res.json(session);
    } catch (err) {
      res.status(500).json({ error: 'Failed to get session' });
    }
  };

  getSessionWithQuestions = async (req: Request, res: Response): Promise<void> => {
    try {
      const userId = (req as any).user.id;
      const data = await this.examService.getSessionWithQuestions(param(req.params.id), userId);
      if (!data) { res.status(404).json({ error: 'Not found' }); return; }
      res.json(data);
    } catch (err) {
      res.status(500).json({ error: 'Failed to get session details' });
    }
  };

  submitAnswer = async (req: Request, res: Response): Promise<void> => {
    try {
      const userId = (req as any).user.id;
      const { questionId, userAnswer, timeTaken } = req.body;
      const session = await this.examService.submitAnswer(
        param(req.params.id), userId, questionId, userAnswer, timeTaken ?? 0,
      );
      if (!session) { res.status(404).json({ error: 'Session not found or already completed' }); return; }
      res.json(session);
    } catch (err) {
      res.status(500).json({ error: 'Failed to submit answer' });
    }
  };

  finishSession = async (req: Request, res: Response): Promise<void> => {
    try {
      const userId = (req as any).user.id;
      const { status } = req.body;
      const session = await this.examService.finishSession(param(req.params.id), userId, status || 'completed');
      if (!session) { res.status(404).json({ error: 'Session not found or already completed' }); return; }
      res.json(session);
    } catch (err) {
      res.status(500).json({ error: 'Failed to finish session' });
    }
  };
}
