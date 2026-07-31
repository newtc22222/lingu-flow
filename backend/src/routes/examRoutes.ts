import { Router } from 'express';
import { ExamController } from '../controllers/ExamController';
import { ExamService } from '../services/ExamService';

const router = Router();
const examService = new ExamService();
const examController = new ExamController(examService);

// ─── Exam Templates ───────────────────────────────────────────────────────────
router.get('/templates', examController.listTemplates);
router.get('/templates/:id', examController.getTemplate);
router.post('/templates', examController.createTemplate);
router.delete('/templates/:id', examController.deleteTemplate);

// ─── Questions ────────────────────────────────────────────────────────────────
router.get('/templates/:examId/questions', examController.listQuestions);
router.post('/templates/:examId/questions', examController.addQuestion);
router.put('/questions/:id', examController.updateQuestion);
router.delete('/questions/:id', examController.deleteQuestion);

// ─── Sessions ─────────────────────────────────────────────────────────────────
router.post('/sessions', examController.startSession);
router.get('/sessions', examController.getUserSessions);
router.get('/sessions/:id', examController.getSession);
router.get('/sessions/:id/details', examController.getSessionWithQuestions);
router.put('/sessions/:id/answer', examController.submitAnswer);
router.put('/sessions/:id/finish', examController.finishSession);

export default router;
