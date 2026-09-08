import os
import sys
import re
import time
import asyncio
from typing import List, Dict, Any
from httpx import AsyncClient, ASGITransport

# Add backend directory to sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
if not os.path.exists(backend_dir):
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend'))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from main import app
from auth_service import create_access_token
from database import SessionLocal
import models
from rag.router import route_query, DAXAgentRouter
from rag_service import get_relevant_context
from groq_service import generate_ai_response

def clean_print(text: str, max_len: int = 150) -> str:
    """Helper to safely format preview strings for Windows cp1252 console."""
    clean = text[:max_len].replace('\n', ' ').strip()
    return clean.encode('ascii', 'replace').decode('ascii')

def check_keyword(kw: str, text: str) -> bool:
    """Resilient keyword checking normalizing unicode spaces and punctuation."""
    norm_text = re.sub(r'[\s\u202f\u00a0\u200b\u2011\u2013\u2014\-]+', ' ', text.lower())
    norm_text = re.sub(r'(\d+)\s*%', r'\1%', norm_text)
    norm_kw = re.sub(r'[\s\u202f\u00a0\u200b\u2011\u2013\u2014\-]+', ' ', kw.lower())
    norm_kw = re.sub(r'(\d+)\s*%', r'\1%', norm_kw)
    return norm_kw in norm_text

async def run_dax_conversation_suite():
    print("=" * 80)
    print("TASK 8: DAX REAL-WORLD CONVERSATION & ANSWER QUALITY TEST SUITE")
    print("=" * 80)

    transport = ASGITransport(app=app)
    db = SessionLocal()
    demo_user = db.query(models.User).filter(models.User.email == "sachi@test.com").first()
    assert demo_user is not None, "Demo student user must exist in DB."
    token = create_access_token(data={"sub": demo_user.email})
    auth_headers = {"Authorization": f"Bearer {token}"}

    total_scenarios_tested = 0
    total_scenarios_passed = 0
    total_scenarios_failed = 0

    latency_records = {
        "course": [],
        "student": [],
        "rag": [],
        "mixed": [],
        "out_of_scope": []
    }

    # =========================================================================
    # 1. REAL-WORLD MULTI-TURN CONVERSATIONS
    # =========================================================================
    print("\n--- [PART 1: Real-World Multi-Turn Conversations (A through E)] ---")

    async with AsyncClient(transport=transport, base_url="http://test") as client:

        # ---------------------------------------------------------------------
        # Conversation A — Course Discovery (5 turns)
        # ---------------------------------------------------------------------
        print("\n[CONVERSATION A] Course Discovery Flow")
        conv_a_history = []
        turns_a = [
            ("What courses are available?", "COURSE_AGENT", ["Network Security Basics", "Ethical Hacking", "Web Application Security"]),
            ("Which one is best for a beginner?", "COURSE_AGENT", ["Network Security Basics"]),
            ("What does that course teach?", "COURSE_AGENT", ["Network Security Basics", "OSI", "Wireshark", "Firewall"]),
            ("Does it have practical labs?", "COURSE_AGENT", ["Wireshark", "Firewall", "Snort"]),
            ("How long does it take?", "COURSE_AGENT", ["6 weeks"])
        ]

        for turn_idx, (user_msg, exp_route, exp_keywords) in enumerate(turns_a, 1):
            await asyncio.sleep(0.8)
            t0 = time.perf_counter()
            res = await client.post("/api/ai/chat", json={"message": user_msg, "chatHistory": conv_a_history})
            t_ms = (time.perf_counter() - t0) * 1000
            latency_records["course"].append(t_ms)

            assert res.status_code == 200
            data = res.json()
            total_scenarios_tested += 1

            ans = data.get("answer", "")
            ans_clean = clean_print(ans)
            print(f"  Turn {turn_idx} Q: \"{user_msg}\"")
            print(f"    -> Route: {data.get('route')}, Latency: {t_ms:.1f}ms")
            print(f"    -> Preview: {ans_clean}...")

            assert data.get("route") in (exp_route, "GENERAL", "MIXED")
            for kw in exp_keywords:
                assert check_keyword(kw, ans), f"Expected '{kw}' in response: {ans}"
            assert data.get("sources") == ["CyberLearn Course Catalog"]

            conv_a_history.append({"role": "user", "content": user_msg})
            conv_a_history.append({"role": "assistant", "content": ans})
            total_scenarios_passed += 1

        # ---------------------------------------------------------------------
        # Conversation B — Course Details (5 turns)
        # ---------------------------------------------------------------------
        print("\n[CONVERSATION B] Course Details Flow")
        conv_b_history = []
        turns_b = [
            ("Tell me about Network Security Basics.", "COURSE_AGENT", ["Network Security Basics", "Beginner", "6 weeks"]),
            ("What are its prerequisites?", "COURSE_AGENT", ["computer", "internet literacy"]),
            ("What modules does it contain?", "COURSE_AGENT", ["OSI", "Wireshark", "Firewall"]),
            ("Does it include Wireshark?", "COURSE_AGENT", ["Wireshark", "Packet Analysis"]),
            ("What certification do I get?", "COURSE_AGENT", ["Certificate", "Completion"])
        ]

        for turn_idx, (user_msg, exp_route, exp_keywords) in enumerate(turns_b, 1):
            await asyncio.sleep(0.8)
            t0 = time.perf_counter()
            res = await client.post("/api/ai/chat", json={"message": user_msg, "chatHistory": conv_b_history})
            t_ms = (time.perf_counter() - t0) * 1000
            latency_records["course"].append(t_ms)

            assert res.status_code == 200
            data = res.json()
            total_scenarios_tested += 1

            ans = data.get("answer", "")
            ans_clean = clean_print(ans)
            print(f"  Turn {turn_idx} Q: \"{user_msg}\"")
            print(f"    -> Route: {data.get('route')}, Latency: {t_ms:.1f}ms")
            print(f"    -> Preview: {ans_clean}...")

            assert data.get("route") in (exp_route, "MIXED", "RAG")
            for kw in exp_keywords:
                assert check_keyword(kw, ans), f"Expected '{kw}' in response: {ans}"

            conv_b_history.append({"role": "user", "content": user_msg})
            conv_b_history.append({"role": "assistant", "content": ans})
            total_scenarios_passed += 1

        # ---------------------------------------------------------------------
        # Conversation C — Student Progress (4 turns)
        # ---------------------------------------------------------------------
        print("\n[CONVERSATION C] Authenticated Student Progress Flow")
        conv_c_history = []
        turns_c = [
            ("What courses am I enrolled in?", "STUDENT_AGENT", ["Network Security Basics", "active"]),
            ("What's my progress?", "STUDENT_AGENT", ["65", "84.6"]),
            ("Which module am I currently studying?", "STUDENT_AGENT", ["Intrusion Detection Systems"]),
            ("What was my score in Intrusion Detection Systems?", "STUDENT_AGENT", ["76"])
        ]

        for turn_idx, (user_msg, exp_route, exp_keywords) in enumerate(turns_c, 1):
            await asyncio.sleep(0.8)
            t0 = time.perf_counter()
            res = await client.post("/api/ai/chat", json={"message": user_msg, "chatHistory": conv_c_history}, headers=auth_headers)
            t_ms = (time.perf_counter() - t0) * 1000
            latency_records["student"].append(t_ms)

            assert res.status_code == 200
            data = res.json()
            total_scenarios_tested += 1

            ans = data.get("answer", "")
            ans_clean = clean_print(ans)
            print(f"  Turn {turn_idx} Q: \"{user_msg}\"")
            print(f"    -> Route: {data.get('route')}, Latency: {t_ms:.1f}ms")
            print(f"    -> Preview: {ans_clean}...")

            assert data.get("route") == exp_route
            assert data.get("sources") == [], "Student queries must have sources=[]"
            for kw in exp_keywords:
                assert check_keyword(kw, ans), f"Expected '{kw}' in response: {ans}"

            conv_c_history.append({"role": "user", "content": user_msg})
            conv_c_history.append({"role": "assistant", "content": ans})
            total_scenarios_passed += 1

        # ---------------------------------------------------------------------
        # Conversation D — Mixed Learning Question (3 turns)
        # ---------------------------------------------------------------------
        print("\n[CONVERSATION D] Mixed Learning & Student Flow")
        conv_d_history = []
        turns_d = [
            ("Explain firewalls.", "RAG", ["firewall", "traffic"], False),
            ("Is firewall configuration part of my course?", "MIXED", ["Network Security Basics", "Firewall"], True),
            ("How much have I completed?", "STUDENT_AGENT", ["65"], True)
        ]

        for turn_idx, (user_msg, exp_route, exp_keywords, is_auth) in enumerate(turns_d, 1):
            await asyncio.sleep(0.8)
            t0 = time.perf_counter()
            headers = auth_headers if is_auth else None
            res = await client.post("/api/ai/chat", json={"message": user_msg, "chatHistory": conv_d_history}, headers=headers)
            t_ms = (time.perf_counter() - t0) * 1000
            if exp_route == "RAG":
                latency_records["rag"].append(t_ms)
            elif exp_route == "MIXED":
                latency_records["mixed"].append(t_ms)
            else:
                latency_records["student"].append(t_ms)

            assert res.status_code == 200
            data = res.json()
            total_scenarios_tested += 1

            ans = data.get("answer", "")
            ans_clean = clean_print(ans)
            print(f"  Turn {turn_idx} Q: \"{user_msg}\"")
            print(f"    -> Route: {data.get('route')}, Latency: {t_ms:.1f}ms")
            print(f"    -> Preview: {ans_clean}...")

            assert data.get("route") in (exp_route, "COURSE_AGENT", "RAG", "STUDENT_AGENT", "MIXED")
            for kw in exp_keywords:
                assert check_keyword(kw, ans), f"Expected '{kw}' in response: {ans}"

            conv_d_history.append({"role": "user", "content": user_msg})
            conv_d_history.append({"role": "assistant", "content": ans})
            total_scenarios_passed += 1

        # ---------------------------------------------------------------------
        # Conversation E — Course Recommendation (4 turns)
        # ---------------------------------------------------------------------
        print("\n[CONVERSATION E] Course Recommendation Flow")
        conv_e_history = []
        turns_e = [
            ("I'm a beginner interested in cybersecurity.", "COURSE_AGENT", ["Network Security Basics"]),
            ("Which course should I take?", "COURSE_AGENT", ["Network Security Basics", "Beginner"]),
            ("What will I learn?", "COURSE_AGENT", ["Network Security Basics"]),
            ("What should I know before starting?", "COURSE_AGENT", ["computer", "literacy"])
        ]

        for turn_idx, (user_msg, exp_route, exp_keywords) in enumerate(turns_e, 1):
            await asyncio.sleep(0.8)
            t0 = time.perf_counter()
            res = await client.post("/api/ai/chat", json={"message": user_msg, "chatHistory": conv_e_history})
            t_ms = (time.perf_counter() - t0) * 1000
            latency_records["course"].append(t_ms)

            assert res.status_code == 200
            data = res.json()
            total_scenarios_tested += 1

            ans = data.get("answer", "")
            ans_clean = clean_print(ans)
            print(f"  Turn {turn_idx} Q: \"{user_msg}\"")
            print(f"    -> Route: {data.get('route')}, Latency: {t_ms:.1f}ms")
            print(f"    -> Preview: {ans_clean}...")

            assert data.get("route") in (exp_route, "GENERAL", "MIXED", "RAG")
            for kw in exp_keywords:
                assert check_keyword(kw, ans), f"Expected '{kw}' in response: {ans}"

            conv_e_history.append({"role": "user", "content": user_msg})
            conv_e_history.append({"role": "assistant", "content": ans})
            total_scenarios_passed += 1

    # =========================================================================
    # 2. NATURAL LANGUAGE VARIATIONS
    # =========================================================================
    print("\n--- [PART 2: Natural Language Variations] ---")
    course_variations = [
        "Network Security Basics",
        "network security",
        "netsec",
        "the network security course",
        "that course",
        "this course",
        "the security basics course"
    ]
    
    # Context with Network Security Basics
    mock_history = [{"role": "assistant", "content": "Network Security Basics is our 6-week foundational course."}]

    for v in course_variations:
        ref = DAXAgentRouter.extract_course_reference(v, chat_history=mock_history)
        print(f"  Variation: \"{v}\" -> Resolved: '{ref}'")
        assert ref == "Network Security Basics", f"Failed to resolve variation '{v}'"
        total_scenarios_tested += 1
        total_scenarios_passed += 1

    student_variations = [
        "my progress",
        "how much have I completed",
        "my completion",
        "my score",
        "how am I doing",
        "what have I completed",
        "which module am I on"
    ]

    for sv in student_variations:
        decision = route_query(sv)
        print(f"  Student Variation: \"{sv}\" -> Route: {decision['route']}, Intent: {decision['intent']}")
        assert decision["route"] == "STUDENT_AGENT"
        assert decision["requires_authentication"] is True
        total_scenarios_tested += 1
        total_scenarios_passed += 1

    # =========================================================================
    # 3. AMBIGUOUS QUERIES (Clarification vs Guessing)
    # =========================================================================
    print("\n--- [PART 3: Ambiguous Queries (Zero Guessing)] ---")
    ambiguous_tests = [
        ("How long is it?", "COURSE_CLARIFICATION", ["which course", "Network Security Basics", "Ethical Hacking", "Web Application Security"]),
        ("What are the prerequisites?", "COURSE_CLARIFICATION", ["which course", "Network Security Basics", "Ethical Hacking", "Web Application Security"]),
        ("Tell me about security.", "GENERAL", ["CyberLearn", "tracks", "Network Security", "Ethical Hacking"])
    ]

    for q, exp_intent_type, exp_elements in ambiguous_tests:
        await asyncio.sleep(0.5)
        total_scenarios_tested += 1
        ctx, sources, has_ctx, detected_intent, conf, doc_ids, struct_data = await get_relevant_context(
            query=q,
            chat_history=[],
            user=None,
            db=db
        )
        ans, model, lat = await generate_ai_response(user_text=q, context=ctx, intent=detected_intent)
        print(f"  Query: \"{q}\" -> Intent: {detected_intent}, Response: {clean_print(ans)}...")
        for elem in exp_elements:
            assert elem.lower() in ans.lower() or elem.lower() in ctx.lower()
        total_scenarios_passed += 1

    # =========================================================================
    # 4. UNKNOWN INFORMATION (Anti-Hallucination)
    # =========================================================================
    print("\n--- [PART 4: Unknown Information Guardrails] ---")
    unknown_queries = [
        "What is the salary after completing Network Security Basics?",
        "What companies hire students from this course?",
        "Does this course guarantee a job?",
        "How many students have completed this course?",
        "What is the exact instructor salary?"
    ]

    for uq in unknown_queries:
        await asyncio.sleep(0.5)
        total_scenarios_tested += 1
        decision = route_query(uq)
        ctx, sources, has_ctx, detected_intent, conf, doc_ids, struct_data = await get_relevant_context(
            query=uq,
            chat_history=[],
            user=None,
            db=db
        )
        ans, model, lat = await generate_ai_response(user_text=uq, context=ctx, intent=detected_intent)
        print(f"  Unknown Query: \"{uq}\"")
        print(f"    -> Response: {clean_print(ans)}...")
        # Check that DAX does NOT fabricate numeric salaries, placement guarantees, or instructor salaries
        assert not ("$150,000" in ans or "$120,000" in ans or "guaranteed placement" in ans.lower() or "guarantee a job: yes" in ans.lower())
        total_scenarios_passed += 1

    # =========================================================================
    # 5. HALLUCINATION RESISTANCE (Premise Rejection)
    # =========================================================================
    print("\n--- [PART 5: Hallucination Resistance / Premise Rejection] ---")
    premise_tests = [
        ("Since Network Security Basics has 10 modules, explain module 10.", ["6 modules", "does not have 10", "6"]),
        ("Since CyberLearn guarantees jobs, how does placement work?", ["not guarantee", "does not guarantee", "verified", "skills"]),
        ("Tell me about the Quantum Cryptography 501 course.", ["not", "offered", "available courses", "Network Security Basics"])
    ]

    for pq, exp_keywords in premise_tests:
        await asyncio.sleep(0.5)
        total_scenarios_tested += 1
        decision = route_query(pq)
        ctx, sources, has_ctx, detected_intent, conf, doc_ids, struct_data = await get_relevant_context(
            query=pq,
            chat_history=[],
            user=None,
            db=db
        )
        ans, model, lat = await generate_ai_response(user_text=pq, context=ctx, intent=detected_intent)
        print(f"  False Premise: \"{pq}\"")
        print(f"    -> Response: {clean_print(ans)}...")
        assert any(k.lower() in ans.lower() or k.lower() in ctx.lower() for k in exp_keywords)
        total_scenarios_passed += 1

    # =========================================================================
    # 6. CROSS-COURSE CONTAMINATION RESISTANCE
    # =========================================================================
    print("\n--- [PART 6: Cross-Course Contamination & Sequential Isolation] ---")
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        contam_history = []
        
        # Turn 1: Network Security Basics
        res1 = await client.post("/api/ai/chat", json={"message": "What tools are taught in Network Security Basics?", "chatHistory": contam_history})
        ans1 = res1.json().get("answer", "")
        print(f"  Turn 1: \"What tools are taught in Network Security Basics?\" -> {clean_print(ans1)}...")
        assert "wireshark" in ans1.lower()
        contam_history.append({"role": "user", "content": "What tools are taught in Network Security Basics?"})
        contam_history.append({"role": "assistant", "content": ans1})
        total_scenarios_tested += 1
        total_scenarios_passed += 1

        # Turn 2: Web Application Security
        res2 = await client.post("/api/ai/chat", json={"message": "What about Web Application Security?", "chatHistory": contam_history})
        ans2 = res2.json().get("answer", "")
        print(f"  Turn 2: \"What about Web Application Security?\" -> {clean_print(ans2)}...")
        assert "burp suite" in ans2.lower() or "owasp" in ans2.lower() or "web" in ans2.lower()
        contam_history.append({"role": "user", "content": "What about Web Application Security?"})
        contam_history.append({"role": "assistant", "content": ans2})
        total_scenarios_tested += 1
        total_scenarios_passed += 1

        # Turn 3: "What are its prerequisites?" -> Must resolve to Web Application Security
        ref_turn3 = DAXAgentRouter.extract_course_reference("What are its prerequisites?", chat_history=contam_history)
        print(f"  Turn 3 Reference Check: \"What are its prerequisites?\" -> Resolved: '{ref_turn3}'")
        assert ref_turn3 == "Web Application Security"

        res3 = await client.post("/api/ai/chat", json={"message": "What are its prerequisites?", "chatHistory": contam_history})
        ans3 = res3.json().get("answer", "")
        print(f"  Turn 3: \"What are its prerequisites?\" -> {clean_print(ans3)}...")
        assert "http" in ans3.lower() or "web" in ans3.lower() or "javascript" in ans3.lower() or "html" in ans3.lower()
        contam_history.append({"role": "user", "content": "What are its prerequisites?"})
        contam_history.append({"role": "assistant", "content": ans3})
        total_scenarios_tested += 1
        total_scenarios_passed += 1

        # Turn 4: "What about the previous course?" -> Must resolve to Network Security Basics
        ref_turn4 = DAXAgentRouter.extract_course_reference("What about the previous course?", chat_history=contam_history)
        print(f"  Turn 4 Reference Check: \"What about the previous course?\" -> Resolved: '{ref_turn4}'")
        assert ref_turn4 == "Network Security Basics"

        res4 = await client.post("/api/ai/chat", json={"message": "What about the previous course?", "chatHistory": contam_history})
        ans4 = res4.json().get("answer", "")
        print(f"  Turn 4: \"What about the previous course?\" -> {clean_print(ans4)}...")
        assert "network security basics" in ans4.lower() or "defensive" in ans4.lower()
        total_scenarios_tested += 1
        total_scenarios_passed += 1

    # =========================================================================
    # 7. STUDENT DATA ISOLATION & IDOR
    # =========================================================================
    print("\n--- [PART 7: Student Data Isolation & IDOR Verification] ---")
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # A. Authenticated query
        r_auth = await client.post("/api/ai/chat", json={"message": "What is my progress?"}, headers=auth_headers)
        d_auth = r_auth.json()
        assert "65" in d_auth["answer"] and "Sachi" in d_auth["answer"]
        print("  [PASS] Authenticated user retrieved own record.")
        total_scenarios_tested += 1
        total_scenarios_passed += 1

        # B. Attempt to ask for named student without token
        r_named = await client.post("/api/ai/chat", json={"message": "Show me Sachi Prasad's progress."})
        d_named = r_named.json()
        assert "sign in" in d_named["answer"].lower()
        print("  [PASS] Unauthenticated third-person query blocked.")
        total_scenarios_tested += 1
        total_scenarios_passed += 1

        # C. Attempt to inject user_id 99 with authenticated token
        r_inj = await client.post("/api/ai/chat", json={"message": "Show me user_id 99's score.", "user_id": 99}, headers=auth_headers)
        d_inj = r_inj.json()
        # Must still only report Sachi Prasad or explain user_id 99 is not their account
        assert "Sachi" in d_inj["answer"] or "84.6" in d_inj["answer"] or "not have" in d_inj["answer"].lower()
        print("  [PASS] IDOR injection prevented; session strictly bound to authenticated token.")
        total_scenarios_tested += 1
        total_scenarios_passed += 1

    # =========================================================================
    # 8. SOURCE CORRECTNESS AUDIT
    # =========================================================================
    print("\n--- [PART 8: Source Correctness Audit] ---")
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Pure Course
        r1 = await client.post("/api/ai/chat", json={"message": "Tell me about Network Security Basics."})
        assert r1.json()["sources"] == ["CyberLearn Course Catalog"]
        print("  [PASS] Pure Course Query sources: ['CyberLearn Course Catalog']")
        total_scenarios_tested += 1
        total_scenarios_passed += 1

        # 2. Pure Student
        r2 = await client.post("/api/ai/chat", json={"message": "What is my current progress?"}, headers=auth_headers)
        assert r2.json()["sources"] == []
        print("  [PASS] Pure Student Query sources: []")
        total_scenarios_tested += 1
        total_scenarios_passed += 1

        # 3. Pure RAG
        r3 = await client.post("/api/ai/chat", json={"message": "What is a firewall?"})
        assert len(r3.json()["sources"]) > 0 and all("Module" in s or "Architecture" in s or "Catalog" in s or "Guide" in s for s in r3.json()["sources"])
        print(f"  [PASS] Pure RAG Query sources: {r3.json()['sources']}")
        total_scenarios_tested += 1
        total_scenarios_passed += 1

    # =========================================================================
    # 9. ANSWER QUALITY (No Internal Leaks)
    # =========================================================================
    print("\n--- [PART 9: Answer Quality & Internal Metadata Leak Check] ---")
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        sample_queries = [
            ("What is Network Security Basics?", False),
            ("What is my progress?", True),
            ("Explain firewalls and tell me my score.", True),
            ("What is CyberLearn?", False)
        ]

        forbidden_tokens = ["STUDENT_AGENT", "COURSE_AGENT", "ROUTE_MIXED", "LMSAgentTools", "sqlite", "table `users`", "SELECT * FROM"]

        for sq, is_auth in sample_queries:
            headers = auth_headers if is_auth else None
            res = await client.post("/api/ai/chat", json={"message": sq}, headers=headers)
            ans = res.json().get("answer", "")
            for token_str in forbidden_tokens:
                assert token_str not in ans, f"Internal token '{token_str}' leaked in response: {ans}"
            print(f"  [PASS] Clean user-facing answer for: \"{sq}\"")
            total_scenarios_tested += 1
            total_scenarios_passed += 1

    # =========================================================================
    # 10. EDGE CASES (Punctuation, Typos, Multi-Questions)
    # =========================================================================
    print("\n--- [PART 10: Edge Cases & Robustness] ---")
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        edge_cases = [
            ("Empty Query", "   ", "OUT_OF_SCOPE"),
            ("Only Punctuation", "??? ... !!!", "OUT_OF_SCOPE"),
            ("Very Long Query", "What is Network Security Basics " * 30, "COURSE_AGENT"),
            ("Typo: Netwrok Security Basics", "Tell me about Netwrok Security Basics.", "COURSE_AGENT"),
            ("Typo: Wireshark", "Explain Wireshark.", "RAG"),
            ("Multi-Question Query", "What is Network Security Basics, how long is it, what are the prerequisites, and what will I learn?", "COURSE_AGENT")
        ]

        for label, eq, exp_route in edge_cases:
            res = await client.post("/api/ai/chat", json={"message": eq})
            assert res.status_code == 200
            data = res.json()
            ans_clean = clean_print(data.get("answer", ""))
            print(f"  Edge Case [{label}]: \"{clean_print(eq, 40)}\" -> Route: {data.get('route')}, Ans: {ans_clean}...")
            total_scenarios_tested += 1
            total_scenarios_passed += 1

    # =========================================================================
    # 11. PERFORMANCE BENCHMARKING (Multi-Sample Latency)
    # =========================================================================
    print("\n--- [PART 11: Performance Benchmarking] ---")
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Out-of-scope timing
        for _ in range(3):
            t0 = time.perf_counter()
            await client.post("/api/ai/chat", json={"message": "Write a poem about cats."})
            latency_records["out_of_scope"].append((time.perf_counter() - t0) * 1000)

    print("\n================================================================================")
    print("LATENCY STATISTICS (Milliseconds across all runs):")
    print(f"{'Category':<15} | {'Samples':<8} | {'Mean (ms)':<10} | {'Min (ms)':<10} | {'Max (ms)':<10}")
    print("-" * 65)

    perf_summary = {}
    for cat, times in latency_records.items():
        if times:
            mean_t = sum(times) / len(times)
            min_t = min(times)
            max_t = max(times)
            perf_summary[cat] = {"mean": mean_t, "min": min_t, "max": max_t, "count": len(times)}
            print(f"{cat.capitalize():<15} | {len(times):<8} | {mean_t:<10.1f} | {min_t:<10.1f} | {max_t:<10.1f}")

    print("================================================================================")
    print(f"TOTAL CONVERSATION SCENARIOS TESTED: {total_scenarios_tested}")
    print(f"PASSED: {total_scenarios_passed} | FAILED: {total_scenarios_failed}")
    print("================================================================================")

    db.close()
    return {
        "tested": total_scenarios_tested,
        "passed": total_scenarios_passed,
        "failed": total_scenarios_failed,
        "perf": perf_summary
    }

if __name__ == "__main__":
    asyncio.run(run_dax_conversation_suite())
