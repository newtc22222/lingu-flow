import app from '../backend/src/app';
import { connectDB } from '../backend/src/utils/db';

export default async (req: any, res: any) => {
  // Ensure the database connection is warm before handling the request
  await connectDB();
  
  // Vercel serverless function signature directly maps to Express app signature
  return app(req, res);
};
