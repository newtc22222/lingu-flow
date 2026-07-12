import app, { setupDummyUser } from './app';
import { connectDB } from './utils/db';

const PORT = process.env.PORT || 3000;

const startServer = async () => {
  try {
    await connectDB();
    await setupDummyUser();
    
    app.listen(PORT, () => {
      console.log(`Server running on http://localhost:${PORT}`);
    });
  } catch (error) {
    console.error('Failed to start server:', error);
    process.exit(1);
  }
};

startServer();
