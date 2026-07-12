import { Request, Response } from 'express';
import User from '../models/User';
import bcrypt from 'bcryptjs';
import jwt from 'jsonwebtoken';
import { OAuth2Client } from 'google-auth-library';

const JWT_SECRET = process.env.JWT_SECRET || 'lingu_super_secret_key_123';
const GOOGLE_CLIENT_ID = process.env.GOOGLE_CLIENT_ID || 'DUMMY_CLIENT_ID'; // Placeholder for MVP

const client = new OAuth2Client(GOOGLE_CLIENT_ID);

export class AuthController {

  private getGuestIdFromToken(token: string): string | null {
    try {
      const decoded = jwt.verify(token, JWT_SECRET) as { userId: string };
      return decoded.userId;
    } catch {
      return null;
    }
  }

  guestLogin = async (req: Request, res: Response): Promise<void> => {
    try {
      const { guestToken } = req.body || {};

      if (guestToken) {
        const guestId = this.getGuestIdFromToken(guestToken);
        if (guestId) {
          const existingGuest = await User.findById(guestId);
          if (existingGuest && existingGuest.isGuest) {
            const token = jwt.sign({ userId: existingGuest._id }, JWT_SECRET, { expiresIn: '7d' });
            res.status(200).json({
              token,
              user: { id: existingGuest._id, isGuest: true }
            });
            return;
          }
        }
      }

      const user = new User({ isGuest: true });
      await user.save();

      const token = jwt.sign({ userId: user._id }, JWT_SECRET, { expiresIn: '7d' });

      res.status(201).json({
        token,
        user: { id: user._id, isGuest: true }
      });
    } catch (error: any) {
      res.status(500).json({ error: error.message });
    }
  };

  googleLogin = async (req: Request, res: Response): Promise<void> => {
    try {
      const { credential, guestToken } = req.body;
      if (!credential) {
        res.status(400).json({ error: 'Google credential is required' });
        return;
      }

      // Verify Google ID token
      // For development with dummy client ID, we might need a workaround or mock if we can't verify properly.
      // But we will implement the proper standard way.
      let payload;
      try {
        const ticket = await client.verifyIdToken({
          idToken: credential,
          audience: GOOGLE_CLIENT_ID,
        });
        payload = ticket.getPayload();
      } catch (err) {
        // Mock verification for MVP if real client ID isn't used
        if (GOOGLE_CLIENT_ID === 'DUMMY_CLIENT_ID') {
           payload = { sub: 'dummy_google_123', email: 'dummy@google.com', name: 'Google User' };
        } else {
          res.status(401).json({ error: 'Invalid Google token' });
          return;
        }
      }

      if (!payload) {
        res.status(401).json({ error: 'Invalid Google token payload' });
        return;
      }

      const { sub: googleId, email, name: username } = payload;

      let user = await User.findOne({ googleId });

      if (!user) {
        // User doesn't exist. Do we have a guest token to link?
        if (guestToken) {
          const guestId = this.getGuestIdFromToken(guestToken);
          if (guestId) {
            const guestUser = await User.findById(guestId);
            if (guestUser && guestUser.isGuest) {
              guestUser.googleId = googleId;
              guestUser.email = email;
              guestUser.username = username || `user_${googleId}`;
              guestUser.isGuest = false;
              await guestUser.save();
              user = guestUser;
            }
          }
        }

        if (!user) {
          // If still no user, check if email already registered via standard auth
          user = await User.findOne({ email });
          if (user) {
             user.googleId = googleId;
             user.isGuest = false;
             await user.save();
          } else {
             user = new User({
               googleId,
               email,
               username: username || `user_${googleId}`,
               isGuest: false
             });
             await user.save();
          }
        }
      }

      const token = jwt.sign({ userId: user._id }, JWT_SECRET, { expiresIn: '7d' });

      res.json({
        token,
        user: { id: user._id, username: user.username, email: user.email, isGuest: user.isGuest }
      });
    } catch (error: any) {
      res.status(500).json({ error: error.message });
    }
  };

  register = async (req: Request, res: Response): Promise<void> => {
    try {
      const { username, email, password, guestToken } = req.body;

      if (!username || !email || !password) {
        res.status(400).json({ error: 'Username, email, and password are required' });
        return;
      }

      const existingUser = await User.findOne({ $or: [{ email }, { username }] });
      if (existingUser) {
        res.status(409).json({ error: 'User already exists' });
        return;
      }

      const salt = await bcrypt.genSalt(10);
      const passwordHash = await bcrypt.hash(password, salt);

      let user;

      // Link guest account if token provided
      if (guestToken) {
        const guestId = this.getGuestIdFromToken(guestToken);
        if (guestId) {
          const guestUser = await User.findById(guestId);
          if (guestUser && guestUser.isGuest) {
            guestUser.username = username;
            guestUser.email = email;
            guestUser.passwordHash = passwordHash;
            guestUser.isGuest = false;
            await guestUser.save();
            user = guestUser;
          }
        }
      }

      if (!user) {
        user = new User({ username, email, passwordHash, isGuest: false });
        await user.save();
      }

      const token = jwt.sign({ userId: user._id }, JWT_SECRET, { expiresIn: '7d' });

      res.status(201).json({
        token,
        user: { id: user._id, username: user.username, email: user.email, isGuest: false }
      });
    } catch (error: any) {
      res.status(500).json({ error: error.message });
    }
  };

  login = async (req: Request, res: Response): Promise<void> => {
    try {
      const { email, password } = req.body;

      if (!email || !password) {
        res.status(400).json({ error: 'Email and password are required' });
        return;
      }

      const user = await User.findOne({ email });
      if (!user || !user.passwordHash) {
        res.status(401).json({ error: 'Invalid credentials' });
        return;
      }

      const isMatch = await bcrypt.compare(password, user.passwordHash);
      if (!isMatch) {
        res.status(401).json({ error: 'Invalid credentials' });
        return;
      }

      const token = jwt.sign({ userId: user._id }, JWT_SECRET, { expiresIn: '7d' });

      res.json({
        token,
        user: { id: user._id, username: user.username, email: user.email, isGuest: user.isGuest }
      });
    } catch (error: any) {
      res.status(500).json({ error: error.message });
    }
  };
}
