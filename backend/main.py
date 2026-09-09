import os
import time
import uuid
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import logging
from sqlalchemy import text

import models
from database import engine, get_db
from auth_service import get_password_hash, verify_password, create_access_token, get_current_user, get_optional_current_user
from rag_service import get_relevant_context
from groq_service import generate_ai_response
from rag.router import route_query
from deterministic_formatter import format_deterministic_response

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables and perform column migrations
models.Base.metadata.create_all(bind=engine)

with engine.begin() as conn:
    migrations = [
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR DEFAULT 'student'",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS name VARCHAR",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at DATETIME",
        "ALTER TABLE courses ADD COLUMN IF NOT EXISTS difficulty VARCHAR DEFAULT 'Beginner'",
        "ALTER TABLE courses ADD COLUMN IF NOT EXISTS total_segments INTEGER DEFAULT 10",
        "ALTER TABLE courses ADD COLUMN IF NOT EXISTS total_modules INTEGER DEFAULT 6",
        "ALTER TABLE enrollments ADD COLUMN IF NOT EXISTS completion_percentage FLOAT DEFAULT 0.0",
        "ALTER TABLE enrollments ADD COLUMN IF NOT EXISTS overall_score FLOAT",
        "ALTER TABLE enrollments ADD COLUMN IF NOT EXISTS last_accessed DATETIME",
        "ALTER TABLE user_progress ADD COLUMN IF NOT EXISTS total_modules INTEGER DEFAULT 6",
        "ALTER TABLE user_progress ADD COLUMN IF NOT EXISTS current_module VARCHAR",
    ]
    for m in migrations:
        try:
            conn.execute(text(m))
        except Exception:
            try:
                simple_m = m.replace("IF NOT EXISTS ", "")
                conn.execute(text(simple_m))
            except Exception:
                pass

app = FastAPI(
    title="CyberLearn LMS API",
    description="Backend API for CyberLearn LMS and DAX AI Assistant operated by CyberDaksh.",
    version="2.1.0"
)

# Configure CORS
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]

frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    for u in frontend_url.split(","):
        u_clean = u.strip()
        if u_clean and u_clean not in origins:
            origins.append(u_clean)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Schemas ---
class UserCreate(BaseModel):
    name: Optional[str] = None
    email: str
    password: str

class GoogleAuthRequest(BaseModel):
    email: str
    name: Optional[str] = None
    picture: Optional[str] = None
    token: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str
    user: Optional[Dict[str, Any]] = None

class ChatRequest(BaseModel):
    message: str = Field(..., max_length=1000)
    chatHistory: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    conversationId: Optional[str] = None

class LatencyMetrics(BaseModel):
    retrieval_ms: float
    generation_ms: float
    total_ms: float

class StructuredChatResponse(BaseModel):
    answer: str
    sources: List[str] = Field(default_factory=list)
    intent: str
    route: Optional[str] = None
    agents_used: Optional[List[str]] = None
    confidence: float
    conversation_id: str
    request_id: str
    latency: LatencyMetrics
    model_used: str
    data: Optional[Dict[str, Any]] = None

# --- Routes ---

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "CyberLearn LMS DAX Production Assistant"}

@app.post("/api/auth/register", response_model=Token)
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    user_name = user.name or user.email.split('@')[0]
    new_user = models.User(email=user.email, name=user_name, role="student", hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    access_token = create_access_token(data={"sub": new_user.email})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {"id": new_user.id, "email": new_user.email, "name": new_user.name, "role": new_user.role}
    }

@app.post("/api/auth/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not user.hashed_password or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.email})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {"id": user.id, "email": user.email, "name": user.name or user.email.split('@')[0], "role": user.role}
    }

@app.post("/api/auth/google", response_model=Token)
def google_auth(auth_req: GoogleAuthRequest, db: Session = Depends(get_db)):
    if not auth_req.email:
        raise HTTPException(status_code=400, detail="Email is required")
    
    user = db.query(models.User).filter(models.User.email == auth_req.email).first()
    if not user:
        user_name = auth_req.name or auth_req.email.split('@')[0]
        user = models.User(email=auth_req.email, name=user_name, role="student", hashed_password=None)
        db.add(user)
        db.commit()
        db.refresh(user)
    elif auth_req.name and not user.name:
        user.name = auth_req.name
        db.commit()
        db.refresh(user)
        
    access_token = create_access_token(data={"sub": user.email})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {"id": user.id, "email": user.email, "name": user.name or user.email.split('@')[0], "role": user.role}
    }

@app.get("/api/auth/me")
def get_me(current_user: models.User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name or current_user.email.split('@')[0],
        "role": current_user.role
    }

@app.post("/api/ai/chat", response_model=StructuredChatResponse)
async def chat_endpoint(
    req: ChatRequest,
    current_user: Optional[models.User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    request_id = f"req_{uuid.uuid4().hex[:12]}"
    conv_id = req.conversationId or f"conv_{uuid.uuid4().hex[:12]}"
    total_start = time.perf_counter()

    try:
        # STEP 0: Empty Query Guard
        if not req.message or not req.message.strip():
            total_ms = (time.perf_counter() - total_start) * 1000.0
            return {
                "answer": "Please ask a question about CyberLearn courses, platform features, or your student progress.",
                "sources": [],
                "intent": "EMPTY_QUERY",
                "route": "GENERAL",
                "agents_used": [],
                "confidence": 1.0,
                "conversation_id": conv_id,
                "request_id": request_id,
                "latency": {
                    "retrieval_ms": 0.0,
                    "generation_ms": 0.0,
                    "total_ms": round(total_ms, 2)
                },
                "model_used": "dax-guard",
                "data": None
            }

        # STEP 1: DAX Agent Router Execution
        routing = route_query(req.message, req.chatHistory)
        route = routing.get("route", "RAG")
        intent = routing.get("intent", "COURSE_CONTENT")
        agents = routing.get("agents", [])
        requires_auth = routing.get("requires_authentication", False)
        confidence = routing.get("confidence", 0.95)
        course_ref = routing.get("course_reference")

        # STEP 2: Authentication Guard Check
        if requires_auth and not current_user:
            total_ms = (time.perf_counter() - total_start) * 1000.0
            logger.info(
                f"[{request_id}] route={route} intent={intent} agents={agents} latency={total_ms:.1f}ms status=unauthenticated"
            )
            return {
                "answer": "Please sign in to CyberLearn so I can access your personal learning information.",
                "sources": [],
                "intent": intent,
                "route": route,
                "agents_used": agents,
                "confidence": 1.0,
                "conversation_id": conv_id,
                "request_id": request_id,
                "latency": {
                    "retrieval_ms": 0.0,
                    "generation_ms": 0.0,
                    "total_ms": round(total_ms, 2)
                },
                "model_used": "dax-auth-guard",
                "data": None
            }

        # STEP 3: Out of Scope Guard Check
        if route == "OUT_OF_SCOPE":
            total_ms = (time.perf_counter() - total_start) * 1000.0
            logger.info(
                f"[{request_id}] route={route} intent={intent} agents=[] latency={total_ms:.1f}ms"
            )
            return {
                "answer": "I can help with CyberLearn courses, learning content, enrollment, progress, assessments, and other LMS-related questions.",
                "sources": [],
                "intent": "OUT_OF_SCOPE",
                "route": "OUT_OF_SCOPE",
                "agents_used": [],
                "confidence": confidence,
                "conversation_id": conv_id,
                "request_id": request_id,
                "latency": {
                    "retrieval_ms": 0.0,
                    "generation_ms": 0.0,
                    "total_ms": round(total_ms, 2)
                },
                "model_used": "dax-router",
                "data": None
            }

        # STEP 4: Capability Execution & Context Assembly
        retrieval_start = time.perf_counter()
        context, sources, has_context, resolved_intent, conf_score, doc_ids, structured_data = await get_relevant_context(
            query=req.message,
            chat_history=req.chatHistory,
            user=current_user,
            db=db,
            intent=intent,
            route=route
        )
        retrieval_ms = (time.perf_counter() - retrieval_start) * 1000.0

        # STEP 5: Fast Deterministic Grounding or Grounded Natural-Language Generation via Groq
        deterministic_ans = format_deterministic_response(
            query=req.message,
            intent=resolved_intent,
            route=route,
            structured_data=structured_data,
            user=current_user,
            course_reference=course_ref
        )
        if deterministic_ans:
            answer = deterministic_ans
            model_used = "dax-deterministic"
            gen_ms = 0.0
        else:
            answer, model_used, gen_ms = await generate_ai_response(
                user_text=req.message,
                chat_history=req.chatHistory,
                context=context,
                intent=resolved_intent
            )
        total_ms = (time.perf_counter() - total_start) * 1000.0

        # STEP 6: Structured Logging
        logger.info(
            f"[{request_id}] route={route} intent={resolved_intent} agents={agents} latency={total_ms:.1f}ms model='{model_used}'"
        )

        return {
            "answer": answer,
            "sources": sources if has_context else [],
            "intent": resolved_intent,
            "route": route,
            "agents_used": agents,
            "confidence": conf_score if conf_score is not None else confidence,
            "conversation_id": conv_id,
            "request_id": request_id,
            "latency": {
                "retrieval_ms": round(retrieval_ms, 2),
                "generation_ms": round(gen_ms, 2),
                "total_ms": round(total_ms, 2)
            },
            "model_used": model_used,
            "data": structured_data
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat error [{request_id}]: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="DAX AI service encountered an unexpected error. Please try again shortly."
        )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 5000))
    is_dev = os.getenv("ENVIRONMENT", "development").lower() == "development"
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=is_dev)
