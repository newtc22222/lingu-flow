import { Router } from 'express';
import { AuthController } from '../controllers/AuthController';

const router = Router();
const authController = new AuthController();

router.post('/register', authController.register);
router.post('/login', authController.login);
router.post('/guest', authController.guestLogin);
router.post('/google', authController.googleLogin);

export default router;
