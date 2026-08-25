import os
import httpx
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GROQ_MODELS = [
    "groq/compound",
    "qwen/qwen3.6-27b",
    "openai/gpt-oss-20b"
]

async def generate_ai_response(user_text: str, chat_history: list, context: str) -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is not configured in backend")
        
    # Format messages for Groq's OpenAI-compatible API
    messages = [
        {"role": "system", "content": f"You are CyberDaksh Learning Assistant. {context}"}
    ]
    
    for msg in chat_history:
        role = "user" if msg.get("role") == "user" else "assistant"
        messages.append({"role": role, "content": msg.get("content", "")})
        
    messages.append({"role": "user", "content": user_text})
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        for model_name in GROQ_MODELS:
            try:
                logger.info(f"Attempting to reach Groq model: {model_name}...")
                
                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers=headers,
                    json={
                        "model": model_name,
                        "messages": messages,
                        "temperature": 0.7
                    },
                    timeout=30.0
                )
                
                data = response.json()
                
                if response.status_code == 200:
                    choices = data.get("choices", [])
                    if choices and choices[0].get("message", {}).get("content"):
                        return choices[0]["message"]["content"]
                else:
                    error_msg = data.get("error", {}).get("message", "Unknown error")
                    logger.error(f"Groq model {model_name} failed: {error_msg}")
                    
            except Exception as e:
                logger.error(f"Connection error for Groq model {model_name}: {str(e)}")
                
    raise RuntimeError("Failed to connect to Groq AI after trying all fallback models.")
