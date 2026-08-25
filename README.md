# CyberLearn LMS Platform & AI Chatbot

A professional, fully-featured frontend for the CyberLearn LMS integrated with a blazing fast Groq-powered AI learning assistant and a Python FastAPI backend.

## Features
- **Modern Frontend:** React-based frontend matching CyberLearn's lavender/purple branding with protected routes and authentication.
- **FastAPI Backend:** A high-performance Python backend connecting the frontend to the database and AI services.
- **PostgreSQL Integration:** Backend connected to Render PostgreSQL for structured data management.
- **Groq AI Chatbot:** The assistant is powered by Groq (using Llama 3/Qwen models) for near-instant AI responses, replacing standard Gemini logic.
- **RAG Architecture:** The AI utilizes specific internal CyberLearn policies before defaulting to standard knowledge.

## Project Structure
```text
cyberlearn-lms/
├── src/                # React Frontend Code
├── backend/            # Python FastAPI Backend
│   ├── main.py         # Backend entry point
│   ├── groq_service.py # Groq AI integration
│   ├── rag_service.py  # Internal knowledge retrieval
│   └── requirements.txt
├── .env                # Root environment variables
└── README.md
```

## Setup Instructions

### 1. Backend Setup (FastAPI)
1. Navigate to the backend folder:
   ```bash
   cd backend
   ```
2. Create your `.env` file inside the `backend` folder:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   DATABASE_URL=your_render_postgresql_url
   FRONTEND_URL=http://localhost:5173
   PORT=5000
   ```
3. Install dependencies and start the server:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   uvicorn main:app --host 0.0.0.0 --port 5000
   ```
   *(The backend runs on `http://localhost:5000`)*

### 2. Frontend Setup (React)
1. Open a new terminal and stay in the root folder.
2. Create your `.env` file in the root folder:
   ```env
   VITE_API_URL=http://localhost:5000
   VITE_GOOGLE_CLIENT_ID=your_google_client_id
   ```
3. Install dependencies and start the dev server:
   ```bash
   npm install
   npm run dev
   ```
   *(The frontend runs on `http://localhost:5173`)*

## Deployment (Render)
This project is configured to be deployed on Render:
- **Backend**: Set as a "Python 3" Web Service pointing to the `backend` Root Directory. Build command is `pip install -r requirements.txt`, Start command is `uvicorn main:app --host 0.0.0.0 --port 10000`.
- **Frontend**: Set as a "Static Site" with Build command `npm run build` and Publish directory `dist`.
