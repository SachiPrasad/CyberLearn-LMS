import os
import httpx
from dotenv import load_dotenv

load_dotenv("backend/.env")

api_key = os.getenv("GROQ_API_KEY")
response = httpx.get(
    "https://api.groq.com/openai/v1/models",
    headers={"Authorization": f"Bearer {api_key}"}
)
for model in response.json().get("data", []):
    print(model["id"])
