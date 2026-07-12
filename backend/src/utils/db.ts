import mongoose from 'mongoose';

const MONGO_URI = process.env.MONGO_URI || 'mongodb://127.0.0.1:27017/linguflow';

let cachedDb: typeof mongoose | null = null;

export const connectDB = async () => {
  if (cachedDb) {
    console.log('Using cached database connection');
    return cachedDb;
  }

  try {
    const db = await mongoose.connect(MONGO_URI);
    cachedDb = db;
    console.log('Connected to MongoDB');
    
    // Attempt to sync indexes in the background (non-blocking)
    mongoose.syncIndexes().then(() => {
      console.log('Database indexes synchronized.');
    }).catch(err => {
      console.error('Warning: Failed to synchronize database indexes:', err.message);
    });

    return db;
  } catch (error) {
    console.error('Failed to connect to MongoDB:', error);
    throw error;
  }
};
