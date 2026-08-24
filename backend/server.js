import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import { getRelevantContext } from './src/services/ragService.js';
import { generateAIResponse } from './src/services/geminiService.js';

dotenv.config();

const app = express();
const PORT = process.env.PORT || 5000;

// Enable CORS for frontend requests
app.use(
  cors({
    origin: true,
    credentials: true,
  })
);

app.use(express.json());

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

// Chat endpoint
app.post('/api/ai/chat', async (req, res) => {
  try {
    const { message, chatHistory } = req.body;

    // 1. Retrieval
    const context = await getRelevantContext(message);

    // 2. Generation
    const answer = await generateAIResponse(message, chatHistory || [], context);

    res.json({ answer });
  } catch (error) {
    console.error('Chat error:', error);
    res.status(500).json({ error: error.message || 'AI service failed' });
  }
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`Server running on port ${PORT}`);
});
