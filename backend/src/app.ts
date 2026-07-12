import express, { Request, Response } from 'express';
import cors from 'cors';
import mongoose from 'mongoose';
import { EventEmitter } from 'events';
import cardRoutes from './routes/cardRoutes';
import deckRoutes from './routes/deckRoutes';
import authRoutes from './routes/authRoutes';
import { authMiddleware } from './utils/authMiddleware';
import User from './models/User';

export const sseEmitter = new EventEmitter();

const app = express();

app.use(cors());
app.use(express.json());

// Routes
app.use('/api/auth', authRoutes);
app.use('/api/cards', authMiddleware, cardRoutes);
app.use('/api/decks', authMiddleware, deckRoutes);

// SSE Endpoint for Real-Time Updates
app.get('/api/events', (req: Request, res: Response) => {
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.flushHeaders();

  const onProgress = (data: any) => {
    res.write(`data: ${JSON.stringify(data)}\n\n`);
  };

  sseEmitter.on('progress', onProgress);

  // Keep connection alive
  const interval = setInterval(() => {
    res.write(': keepalive\n\n');
  }, 15000);

  req.on('close', () => {
    sseEmitter.off('progress', onProgress);
    clearInterval(interval);
  });
});

// Setup dummy user if not exists for MVP
const setupDummyUser = async () => {
  const userId = '64dfb1234567890123456789';
  const existingUser = await User.findById(userId);
  if (!existingUser) {
    const user = new User({
      _id: new mongoose.Types.ObjectId(userId),
      username: 'MVP_User',
      email: 'test@linguflow.com',
      passwordHash: 'dummyhash',
    });
    await user.save();
    console.log('Dummy user created for MVP.');
  }
};

const PORT = process.env.PORT || 3000;
const MONGO_URI = process.env.MONGO_URI || 'mongodb://127.0.0.1:27017/linguflow';

mongoose.connect(MONGO_URI)
  .then(async () => {
    console.log('Connected to MongoDB');
    await setupDummyUser();
    app.listen(PORT, () => {
      console.log(`Server running on http://localhost:${PORT}`);
    });
  })
  .catch(err => {
    console.error('Failed to connect to MongoDB:', err);
  });
