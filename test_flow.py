import httpx

base_url = "http://localhost:5000"

print("1. Registering user...")
resp = httpx.post(f"{base_url}/api/auth/register", json={"email": "test@example.com", "password": "password123"})
if resp.status_code == 400:
    print("User already exists, trying login...")
    resp = httpx.post(f"{base_url}/api/auth/login", data={"username": "test@example.com", "password": "password123"})

print("Status:", resp.status_code)
token = resp.json().get("access_token")
print("Token received!")

print("\n2. Testing Chat endpoint with Vector DB...")
chat_resp = httpx.post(
    f"{base_url}/api/ai/chat", 
    json={"message": "What is the requirement for a CyberLearn certification?"},
    headers={"Authorization": f"Bearer {token}"},
    timeout=30.0
)
print("Chat Status:", chat_resp.status_code)
print("Chat Response:", chat_resp.text.encode('ascii', errors='replace').decode('ascii'))
