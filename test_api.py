import httpx

response = httpx.post(
    "http://localhost:5000/api/ai/chat",
    json={"message": "How are you", "chatHistory": []},
    timeout=30.0
)
print("Status:", response.status_code)
print("Response:", response.text)
