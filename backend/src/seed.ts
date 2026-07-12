import mongoose from 'mongoose';
import Card from './models/Card';
import User from './models/User';

const MONGO_URI = process.env.MONGO_URI || 'mongodb://127.0.0.1:27017/linguflow';
const DUMMY_USER_ID = '64dfb1234567890123456789';

const seed = async () => {
  await mongoose.connect(MONGO_URI);
  console.log('Connected to DB');

  // Ensure user exists
  const existingUser = await User.findById(DUMMY_USER_ID);
  if (!existingUser) {
    await new User({
      _id: new mongoose.Types.ObjectId(DUMMY_USER_ID),
      username: 'MVP_User',
      email: 'test@linguflow.com',
      passwordHash: 'dummyhash',
    }).save();
  }

  // Add some sample cards
  await Card.deleteMany({}); // Clear existing

  const cards = [
    {
      userId: new mongoose.Types.ObjectId(DUMMY_USER_ID),
      front: '# ¿Cómo se dice "Hello" en español?\n\nPista: Empieza con H.',
      back: '## ¡Hola!\n\nSe pronuncia "O-la". La H es muda.',
    },
    {
      userId: new mongoose.Types.ObjectId(DUMMY_USER_ID),
      front: 'Translate this French phrase:\n\n> "Je ne sais pas"',
      back: '**"I do not know"**\n\n- Je: I\n- ne ... pas: not\n- sais: know (savoir)',
    },
    {
      userId: new mongoose.Types.ObjectId(DUMMY_USER_ID),
      front: 'What is the Hiragana for **"Ka"**?',
      back: '# か\n\nExample: かさ (kasa = umbrella)',
    }
  ];

  await Card.insertMany(cards);
  console.log('Inserted sample cards.');

  await mongoose.disconnect();
};

seed().catch(console.error);
