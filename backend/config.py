import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

class RAGConfig:
    # Groq Model Configuration
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    DEFAULT_GROQ_MODEL: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    
    # Verified Available Production Groq Models
    GROQ_FALLBACK_MODELS: List[str] = [
        os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
        "openai/gpt-oss-20b"
    ]
    
    # Retrieval Hyperparameters (Configurable & Documented)
    # TOP_K_RETRIEVAL: Retrieve top 15 initial candidates during hybrid search
    TOP_K_RETRIEVAL: int = int(os.getenv("TOP_K_RETRIEVAL", 15))
    
    # TOP_K_CONTEXT: Re-rank and send only top 3-5 high-confidence chunks to LLM
    TOP_K_CONTEXT: int = int(os.getenv("TOP_K_CONTEXT", 4))
    
    # MIN_RELEVANCE_SCORE: Minimum relevance threshold to avoid hallucinations on unrelated queries
    MIN_RELEVANCE_SCORE: float = float(os.getenv("MIN_RELEVANCE_SCORE", 2.5))
    
    # LLM Settings
    LLM_TEMPERATURE: float = 0.2  # Low temperature for factual precision
    LLM_MAX_TOKENS: int = 768
    LLM_TIMEOUT_SECONDS: float = 10.0
    
    # Security & Guardrails
    MAX_QUERY_LENGTH: int = 1000
    MAX_CHAT_HISTORY_TURNS: int = 8

config = RAGConfig()
