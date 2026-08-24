import dotenv from 'dotenv';
dotenv.config();

const GEMINI_MODELS = [
  "gemini-3.6-flash",
  "gemini-3.1-pro-preview",
  "gemini-2.5-flash",
  "gemini-2.5-pro",
  "gemini-1.5-flash",
  "gemini-1.5-flash-latest",
  "gemini-1.5-pro",
  "gemini-pro"
];

export const generateAIResponse = async (userText, chatHistory, context) => {
  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) {
    throw new Error("GEMINI_API_KEY is not configured in backend");
  }

  // Remove the initial model greeting from chatHistory if it exists, to prevent API errors
  const apiHistory = chatHistory.length > 0 && chatHistory[0].role === 'model' ? chatHistory.slice(1) : chatHistory;

  const contents = [
    { role: 'user', parts: [{ text: `System context: You are CyberDaksh Learning Assistant. ${context}` }] },
    // To satisfy alternating roles, we start with a user message (context), then an "ok" from the model
    { role: 'model', parts: [{ text: "Understood. I am ready to help." }] },
    ...apiHistory.map(m => ({ role: m.role === 'user' ? 'user' : 'model', parts: [{ text: m.content }] })),
    { role: 'user', parts: [{ text: userText }] }
  ];

  // Try each model in the fallback list
  for (const modelName of GEMINI_MODELS) {
    try {
      console.log(`Attempting to reach: ${modelName}...`);
      
      const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${modelName}:generateContent?key=${apiKey}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ contents })
      });

      const data = await response.json();

      if (response.ok && data.candidates?.[0]?.content?.parts?.[0]?.text) {
        return data.candidates[0].content.parts[0].text;
      } else {
        console.error(`Model ${modelName} failed:`, data.error?.message || "Unknown error");
      }
    } catch (err) {
      console.error(`Connection error for ${modelName}:`, err);
    }
  }

  throw new Error("Failed to connect to AI after trying all fallback models.");
};
