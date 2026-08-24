# CyberLearn LMS Platform & AI Chatbot

A professional, fully-featured frontend for the CyberLearn LMS integrated with a Gemini-powered AI learning assistant.

## Features
- **Visual Integration:** Matches CyberLearn's lavender/purple branding and rounded UI components.
- **Authentication System:** Includes simulated Login and Registration flows using React Context and React Router. Protected routes ensure secure access to the dashboard.
- **Intelligent Fallback:** Implements a strict 4-stage fallback logic across Gemini Flash models.
- **Context Aware:** Designed to handle student/course context for personalized AI help based on the authenticated user.
- **Secure:** Uses environment variables and simulated API requests for easy backend replacement later.

## Setup Instructions

1. **Environment Variables:**
   Rename `.env.example` to `.env` in your root folder and add your keys:
   ```env
   VITE_GEMINI_API_KEY=your_gemini_key_here
   VITE_AUTH_API_URL=https://api.cyberdaksh.com/v1/auth
   VITE_AUTH_API_KEY=your_auth_secret
   ```

2. **Install Dependencies:**
   ```bash
   npm install
   ```

3. **Start Development Server:**
   ```bash
   npm run dev
   ```

## Architecture

- **`src/context/AuthContext.tsx`**: Manages the global session state (user details) and handles login/logout syncing with LocalStorage.
- **`src/services/auth.ts`**: Contains the simulated asynchronous authentication calls. *You will replace these mock functions with real `fetch` or `axios` calls to your backend later.*
- **`src/components/ProtectedRoute.tsx`**: A wrapper that forces unauthenticated users back to the `/login` screen.
- **`src/components/Chatbot.tsx`**: The isolated Gemini AI Assistant logic.
- **`src/pages/`**: Contains the `Login`, `Register`, and secure `Dashboard` screens.

## Gemini Fallback Logic
The AI system attempts to generate a response using models in this exact sequence:
1. `gemini-3.5-flash`
2. `gemini-2.5-flash`
3. `gemini-3.1-flash-lite`
4. `gemini-flash-latest`

If a model fails or is unavailable, the chatbot automatically moves to the next model. Only if all four models fail will the user see an error message.
