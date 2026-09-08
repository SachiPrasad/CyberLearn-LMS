import os
import sys
import json
import asyncio
from httpx import AsyncClient, ASGITransport

# Add backend directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import models
from database import SessionLocal
from main import app
from auth_service import create_access_token

async def run_end_to_end_api_tests():
    print("=" * 80)
    print("TEST SUITE: TASK 5 End-to-End POST /api/ai/chat Endpoint Verification")
    print("=" * 80)

    db = SessionLocal()
    demo_user = db.query(models.User).filter(models.User.email == "sachi@test.com").first()
    assert demo_user is not None, "Demo student sachi@test.com not found in DB!"

    token = create_access_token(data={"sub": demo_user.email})
    auth_headers = {"Authorization": f"Bearer {token}"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:

        # ---------------------------------------------------------------------
        # 1. 12 Core Functional Scenarios from Step 20
        # ---------------------------------------------------------------------
        test_scenarios = [
            {
                "id": 1,
                "query": "What is my current progress?",
                "auth": True,
                "expected_route": "STUDENT_AGENT",
                "expected_agents": ["STUDENT_AGENT"],
                "content_checks": ["65", "Network Security Basics", "4"]
            },
            {
                "id": 2,
                "query": "What is my score in Firewall Configuration?",
                "auth": True,
                "expected_route": "STUDENT_AGENT",
                "expected_agents": ["STUDENT_AGENT"],
                "content_checks": ["76"]
            },
            {
                "id": 3,
                "query": "What courses am I enrolled in?",
                "auth": True,
                "expected_route": "STUDENT_AGENT",
                "expected_agents": ["STUDENT_AGENT"],
                "content_checks": ["Network Security Basics", "active"]
            },
            {
                "id": 4,
                "query": "Tell me about Network Security Basics.",
                "auth": False,
                "expected_route": "COURSE_AGENT",
                "expected_agents": ["COURSE_AGENT"],
                "content_checks": ["Network Security Basics", "Defensive Security", "Beginner"]
            },
            {
                "id": 5,
                "query": "What are the prerequisites for Network Security Basics?",
                "auth": False,
                "expected_route": "COURSE_AGENT",
                "expected_agents": ["COURSE_AGENT"],
                "content_checks": ["literacy", "prerequisite"]
            },
            {
                "id": 6,
                "query": "What is a firewall?",
                "auth": False,
                "expected_route": "RAG",
                "expected_agents": ["RAG"],
                "content_checks": ["firewall", "packet"]
            },
            {
                "id": 7,
                "query": "Explain Wireshark.",
                "auth": False,
                "expected_route": "RAG",
                "expected_agents": ["RAG"],
                "content_checks": ["Wireshark", "packet"]
            },
            {
                "id": 8,
                "query": "Explain firewalls and tell me my Firewall score.",
                "auth": True,
                "expected_route": "MIXED",
                "expected_agents": ["RAG", "STUDENT_AGENT"],
                "content_checks": ["76"]
            },
            {
                "id": 9,
                "query": "Tell me what Network Security Basics teaches and how much I have completed.",
                "auth": True,
                "expected_route": "MIXED",
                "expected_agents": ["COURSE_AGENT", "STUDENT_AGENT"],
                "content_checks": ["65", "Network Security Basics"]
            },
            {
                "id": 10,
                "query": "Explain Wireshark, tell me whether it is part of Network Security Basics, and tell me my score.",
                "auth": True,
                "expected_route": "MIXED",
                "expected_agents": ["RAG", "COURSE_AGENT", "STUDENT_AGENT"],
                "content_checks": ["Wireshark", "Network Security Basics"]
            },
            {
                "id": 11,
                "query": "What is CyberLearn?",
                "auth": False,
                "expected_route": ["GENERAL", "COURSE_AGENT"],
                "content_checks": ["CyberLearn"]
            },
            {
                "id": 12,
                "query": "Write a poem about cats.",
                "auth": False,
                "expected_route": "OUT_OF_SCOPE",
                "expected_agents": [],
                "content_checks": ["CyberLearn courses"]
            }
        ]

        print("\n--- [PART 1: Testing 12 Core End-to-End Chat Scenarios] ---")
        for sc in test_scenarios:
            print(f"\n[SCENARIO {sc['id']}] Query: \"{sc['query']}\" (Auth={sc['auth']})")
            headers = auth_headers if sc["auth"] else {}
            response = await client.post(
                "/api/ai/chat",
                json={"message": sc["query"], "chatHistory": []},
                headers=headers
            )
            assert response.status_code == 200, f"Expected status 200, got {response.status_code}: {response.text}"
            data = response.json()

            print(f"  - Route: {data.get('route')}")
            print(f"  - Intent: {data.get('intent')}")
            print(f"  - Agents Used: {data.get('agents_used')}")
            print(f"  - Sources: {data.get('sources')}")
            print(f"  - Latency: {data.get('latency')}")
            answer_preview = data.get('answer', '')[:120].replace('\n', ' ').encode('ascii', 'replace').decode('ascii')
            print(f"  - Answer Preview: {answer_preview}...")

            exp_r = sc["expected_route"]
            if isinstance(exp_r, list):
                assert data.get("route") in exp_r, f"Expected route in {exp_r}, got {data.get('route')}"
            else:
                assert data.get("route") == exp_r, f"Expected route {exp_r}, got {data.get('route')}"

            if "expected_agents" in sc:
                assert data.get("agents_used") == sc["expected_agents"], f"Expected agents {sc['expected_agents']}, got {data.get('agents_used')}"

            for check in sc.get("content_checks", []):
                assert check.lower() in data.get("answer", "").lower() or check.lower() in str(data.get("data", "")).lower(), f"Expected '{check}' in answer"

            print(f"  -> Scenario {sc['id']} PASSED!")
            await asyncio.sleep(0.3)

        # ---------------------------------------------------------------------
        # 2. Security & Guardrail Verification from Step 21
        # ---------------------------------------------------------------------
        print("\n--- [PART 2: Testing Security & Authentication Guards] ---")

        # Security Test 1: Unauthenticated request for personal progress
        print("\n[SECURITY 1] Personal progress query without Auth Token...")
        unauth_resp = await client.post(
            "/api/ai/chat",
            json={"message": "What is my current progress?", "chatHistory": []}
        )
        assert unauth_resp.status_code == 200
        unauth_data = unauth_resp.json()
        assert "sign in" in unauth_data["answer"].lower(), "Expected sign-in prompt for unauthenticated personal query"
        assert unauth_data["sources"] == []
        print("  -> Security 1 PASSED: Unauthenticated personal query cleanly blocked with sign-in prompt.")

        # Security Test 2: Public question works without auth
        print("\n[SECURITY 2] General technical question without Auth Token...")
        pub_resp = await client.post(
            "/api/ai/chat",
            json={"message": "What is a firewall?", "chatHistory": []}
        )
        assert pub_resp.status_code == 200
        pub_data = pub_resp.json()
        assert "firewall" in pub_data["answer"].lower()
        print("  -> Security 2 PASSED: Public question succeeds without requiring login.")

        # Security Test 3: IDOR Resistance
        print("\n[SECURITY 3] IDOR check - Attempting to inject target user_id in body...")
        idor_resp = await client.post(
            "/api/ai/chat",
            json={"message": "What is my score?", "chatHistory": [], "user_id": 99999},
            headers=auth_headers
        )
        assert idor_resp.status_code == 200
        idor_data = idor_resp.json()
        # Answer must still reflect authenticated user Sachi Prasad (overall score 84.6%)
        assert "84.6" in idor_data["answer"] or "84.6" in str(idor_data.get("data", ""))
        print("  -> Security 3 PASSED: Injected user_id ignored, authenticated token used strictly.")

    db.close()

    print("\n" + "=" * 80)
    print("ALL END-TO-END CHAT API TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 80)
    return True

if __name__ == "__main__":
    asyncio.run(run_end_to_end_api_tests())
