import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath('backend'))
from main import app
from httpx import AsyncClient, ASGITransport

queries = [
    "what courses are available?",
    "which courses can I take?",
    "show me all available courses",
    "what courses does CyberLearn offer?",
    "tell me about Network Security Basics"
]

async def test():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for q in queries:
            resp = await client.post("/api/ai/chat", json={"message": q})
            data = resp.json()
            print(f"QUERY: {q}")
            print(f"  ROUTE: {data.get('route')}")
            print(f"  INTENT: {data.get('intent')}")
            print(f"  AGENTS: {data.get('agents_used')}")
            print(f"  SOURCES: {data.get('sources')}")
            print(f"  MODEL: {data.get('model_used')}")
            print(f"  DATA COUNT: {data.get('data', {}).get('count') if data.get('data') else 'N/A'}")
            print(f"  ANSWER PREVIEW:\n{data.get('answer')[:150]}...")
            print("-" * 60)

if __name__ == "__main__":
    asyncio.run(test())
