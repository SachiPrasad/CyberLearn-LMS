import asyncio
import os
import sys
import httpx
from dotenv import load_dotenv

load_dotenv('backend/.env')

async def run_lms_verification():
    print("=" * 80)
    print("CYBERLEARN LMS DAX ASSISTANT -- DEMO LMS DATABASE & RAG TEST SUITE")
    print("=" * 80)

    base_url = "http://127.0.0.1:5000"

    async with httpx.AsyncClient(timeout=45.0) as client:
        # 1. Authenticate Demo Student
        print("\n[AUTH] Logging in as Demo Student (student@cyberlearn.demo)...")
        login_res = await client.post(
            f"{base_url}/api/auth/login",
            data={"username": "student@cyberlearn.demo", "password": "password123"}
        )
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        demo_token = login_res.json()["access_token"]
        headers_demo = {"Authorization": f"Bearer {demo_token}", "Content-Type": "application/json"}
        print(f"Logged in successfully! User ID: {login_res.json()['user']['id']}")

        # 2. Authenticate Student 2 (for IDOR verification)
        print("\n[AUTH] Logging in as Student 2 (student2@cyberlearn.demo)...")
        login2_res = await client.post(
            f"{base_url}/api/auth/login",
            data={"username": "student2@cyberlearn.demo", "password": "password123"}
        )
        assert login2_res.status_code == 200, f"Login 2 failed: {login2_res.text}"
        token2 = login2_res.json()["access_token"]
        headers_student2 = {"Authorization": f"Bearer {token2}", "Content-Type": "application/json"}
        print(f"Logged in as Student 2! User ID: {login2_res.json()['user']['id']}")

        # --- TEST CASES ---
        tests = [
            {
                "id": 1,
                "name": "Enrolled Courses",
                "query": "What courses am I enrolled in?",
                "expected_intent": "ENROLLMENT",
                "must_contain": ["Network Security Basics", "Ethical Hacking Fundamentals"],
                "must_have_empty_sources": True
            },
            {
                "id": 2,
                "name": "Course Progress (Network Security Basics)",
                "query": "What is my progress in Network Security Basics?",
                "expected_intent": "USER_PROGRESS",
                "must_contain": ["50", "82", "Network Security Basics"],
                "must_have_empty_sources": True
            },
            {
                "id": 3,
                "name": "Segment Score (Firewalls)",
                "query": "What is my score in Firewalls?",
                "expected_intent": "SEGMENT_PERFORMANCE",
                "must_contain": ["74", "Firewalls"],
                "must_have_empty_sources": True
            },
            {
                "id": 4,
                "name": "Completed Segments Filter",
                "query": "Which segments have I completed?",
                "expected_intent": "SEGMENT_PERFORMANCE",
                "must_contain": ["Network Fundamentals", "Network Threats", "Threat Detection"],
                "must_have_empty_sources": True
            },
            {
                "id": 5,
                "name": "Pending Segments Filter",
                "query": "Which segments are still pending?",
                "expected_intent": "SEGMENT_PERFORMANCE",
                "must_contain": ["Firewalls", "Intrusion Detection"],
                "must_have_empty_sources": True
            },
            {
                "id": 6,
                "name": "Quiz Assessment Performance",
                "query": "How did I perform in the Threat Detection quiz?",
                "expected_intent": "ASSESSMENT_PERFORMANCE",
                "must_contain": ["85"],
                "must_have_empty_sources": True
            },
            {
                "id": 7,
                "name": "Lab Performance",
                "query": "Have I completed the Firewall lab?",
                "expected_intent": "LAB_PERFORMANCE",
                "must_contain": ["In Progress", "75"],
                "must_have_empty_sources": True
            },
            {
                "id": 8,
                "name": "General RAG Technical Query",
                "query": "Explain what a firewall is.",
                "expected_intent": "LEARNING_HELP",
                "must_contain": ["firewall"],
                "must_have_empty_sources": False
            },
            {
                "id": 9,
                "name": "Hybrid RAG + Personal Score Query",
                "query": "Explain firewalls and tell me my score.",
                "expected_intent": "HYBRID_EXPLAIN_AND_PROGRESS",
                "must_contain": ["74", "firewall"],
                "must_have_empty_sources": False
            },
            {
                "id": 10,
                "name": "Multi-Turn Course Resolution",
                "query": "What is my progress in the first course?",
                "chat_history": [
                    {"role": "user", "content": "What courses am I enrolled in?"},
                    {"role": "assistant", "content": "You are enrolled in:\n1. Network Security Basics\n2. Ethical Hacking Fundamentals"}
                ],
                "expected_intent": "USER_PROGRESS",
                "must_contain": ["Network Security Basics", "50"],
                "must_have_empty_sources": True
            }
        ]

        passed = 0
        for t in tests:
            print(f"\n--- [TEST {t['id']}] {t['name']} ---")
            print(f"Query: \"{t['query']}\"")
            payload = {
                "message": t["query"],
                "chatHistory": t.get("chat_history", [])
            }
            res = await client.post(f"{base_url}/api/ai/chat", headers=headers_demo, json=payload)
            assert res.status_code == 200, f"Error {res.status_code}: {res.text}"
            data = res.json()

            intent = data.get("intent")
            sources = data.get("sources", [])
            answer = data.get("answer", "")
            has_data = bool(data.get("data"))

            print(f"Intent: {intent} (Expected: {t['expected_intent']})")
            print(f"Sources: {sources}")
            print(f"Has Structured Data: {has_data}")
            print(f"Latency: {data.get('latency', {}).get('total_ms')}ms")
            preview = answer[:200].replace('\n', ' ')
            print(f"Answer: {preview}...")

            # Check assertions
            intent_match = (intent == t["expected_intent"]) or (t["expected_intent"] in ("COURSE_CONTENT", "LEARNING_HELP") and intent in ("COURSE_CONTENT", "LEARNING_HELP"))
            assert intent_match, f"Intent mismatch! Got {intent}, expected {t['expected_intent']}"

            if t["must_have_empty_sources"]:
                assert len(sources) == 0, f"Expected empty sources for personal query, but got {sources}"
            else:
                assert len(sources) > 0, f"Expected RAG sources for technical query, but got none"

            for kw in t["must_contain"]:
                assert kw.lower() in answer.lower(), f"Expected keyword '{kw}' not found in answer!"

            print(f"[PASS] Test {t['id']} passed successfully!")
            passed += 1

        # 11. IDOR Isolation Test: Student 2 queries their enrollments
        print("\n--- [TEST 11] IDOR Isolation Verification ---")
        res2 = await client.post(
            f"{base_url}/api/ai/chat",
            headers=headers_student2,
            json={"message": "What courses am I enrolled in?"}
        )
        assert res2.status_code == 200
        data2 = res2.json()
        assert "Web Application Security" in data2["answer"], "Student 2 should only see Web Application Security!"
        assert "Network Security Basics" not in data2["answer"], "Student 2 should NOT see Student 1's courses!"
        print("[PASS] IDOR Protection Verified: Student 2 only receives their isolated records!")
        passed += 1

        # 12. Verification of Zero False Source Badges on Personal Queries
        print("\n--- [TEST 12] Zero False Source Badges on Personal Queries ---")
        p_res = await client.post(
            f"{base_url}/api/ai/chat",
            headers=headers_demo,
            json={"message": "What is my current course progress and score?"}
        )
        assert p_res.status_code == 200
        assert len(p_res.json().get("sources", [])) == 0, "Personal queries must have sources: []"
        print("[PASS] Zero False Source Badges Verified!")
        passed += 1

        print("\n" + "=" * 80)
        print(f"ALL {passed} / 12 LMS & RAG TESTS PASSED CLEANLY!")
        print("=" * 80)

if __name__ == "__main__":
    asyncio.run(run_lms_verification())
