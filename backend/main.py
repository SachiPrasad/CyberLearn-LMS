import os
import psycopg2
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import logging

from rag_service import get_relevant_context
from groq_service import generate_ai_response

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Configure CORS
frontend_url = os.getenv("FRONTEND_URL", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url] if frontend_url != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Test DB Connection on startup
@app.on_event("startup")
def test_db_connection():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        logger.warning("DATABASE_URL is not set. Skipping DB connection test.")
        return
        
    try:
        # Use psycopg2 to connect to PostgreSQL and get the server time
        conn = psycopg2.connect(db_url, sslmode="require")
        cur = conn.cursor()
        cur.execute("SELECT NOW();")
        server_time = cur.fetchone()[0]
        logger.info(f"PostgreSQL connected successfully! Server time: {server_time}")
        cur.close()
        conn.close()
    except Exception as e:
        logger.error(f"Database connection error (expected if DATABASE_URL is empty or incorrect): {e}")

class ChatRequest(BaseModel):
    message: str
    chatHistory: Optional[List[Dict[str, Any]]] = []

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/api/ai/chat")
async def chat_endpoint(req: ChatRequest):
    try:
        # 1. Retrieval
        context = await get_relevant_context(req.message)
        
        # 2. Generation
        answer = await generate_ai_response(req.message, req.chatHistory, context)
        
        return {"answer": answer}
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
