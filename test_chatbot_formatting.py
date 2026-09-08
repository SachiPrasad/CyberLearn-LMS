import asyncio
import os
import sys
import httpx
from dotenv import load_dotenv

load_dotenv('backend/.env')

TESTS = [
    "What topics are covered in Network Security?",
    "What practical work is included in Network Security?",
    "What are the certification requirements?",
    "Explain the OSI model in simple terms.",
    "Show me the modules in Network Security in a structured format.",
    "What courses am I enrolled in?"
]

async def test_api_chat():
    print("=" * 80)
    print("TESTING CHATBOT API RESPONSE FORMATTING")
    print("=" * 80)

    # 1. Login to get token
    async with httpx.AsyncClient() as client:
        login_res = await client.post(
            "http://127.0.0.1:5000/api/auth/login",
            data={"username": "student@cyberlearn.com", "password": "password123"}
        )
        if login_res.status_code != 200:
            # Register first
            reg_res = await client.post(
                "http://127.0.0.1:5000/api/auth/register",
                json={"email": "student@cyberlearn.com", "password": "password123", "name": "Alex Learner"}
            )
            token = reg_res.json()["access_token"]
        else:
            token = login_res.json()["access_token"]

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        for idx, q in enumerate(TESTS, 1):
            print(f"\n--- [TEST {idx}] Query: '{q}' ---")
            resp = await client.post(
                "http://127.0.0.1:5000/api/ai/chat",
                headers=headers,
                json={"message": q, "chatHistory": []},
                timeout=30.0
            )
            if resp.status_code == 200:
                data = resp.json()
                print(f"Status: {resp.status_code}")
                print(f"Intent: {data.get('intent')}")
                print(f"Sources: {data.get('sources')}")
                print(f"Latency: {data.get('latency', {}).get('total_ms')}ms")
                preview = data.get("answer", "")[:350].encode('ascii', errors='replace').decode('ascii')
                print("Answer Preview:\n" + preview + "\n...")
            else:
                print(f"Error {resp.status_code}: {resp.text}")

if __name__ == "__main__":
    asyncio.run(test_api_chat())
