import os
import httpx
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GEMINI_MODELS = [
    "gemini-3.6-flash",
    "gemini-3.1-pro-preview",
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-1.5-flash",
    "gemini-1.5-flash-latest",
    "gemini-1.5-pro",
    "gemini-pro"
]

async def generate_ai_response(user_text: str, chat_history: list, context: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not configured in backend")
        
    # Remove the initial model greeting from chatHistory if it exists, to prevent API errors
    if chat_history and chat_history[0].get("role") == "model":
        chat_history = chat_history[1:]
        
    contents = [
        {"role": "user", "parts": [{"text": f"System context: You are CyberDaksh Learning Assistant. {context}"}]},
        {"role": "model", "parts": [{"text": "Understood. I am ready to help."}]}
    ]
    
    for msg in chat_history:
        role = "user" if msg.get("role") == "user" else "model"
        contents.append({"role": role, "parts": [{"text": msg.get("content", "")}]})
        
    contents.append({"role": "user", "parts": [{"text": user_text}]})
    
    async with httpx.AsyncClient() as client:
        for model_name in GEMINI_MODELS:
            try:
                logger.info(f"Attempting to reach: {model_name}...")
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
                
                response = await client.post(
                    url,
                    json={"contents": contents},
                    timeout=30.0
                )
                
                data = response.json()
                
                if response.status_code == 200:
                    candidates = data.get("candidates", [])
                    if candidates and candidates[0].get("content", {}).get("parts"):
                        return candidates[0]["content"]["parts"][0]["text"]
                else:
                    error_msg = data.get("error", {}).get("message", "Unknown error")
                    logger.error(f"Model {model_name} failed: {error_msg}")
                    
            except Exception as e:
                logger.error(f"Connection error for {model_name}: {str(e)}")
                
    raise RuntimeError("Failed to connect to AI after trying all fallback models.")
