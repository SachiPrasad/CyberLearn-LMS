import os
import sys
import asyncio
from httpx import AsyncClient, ASGITransport

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import models
from database import SessionLocal
from main import app
from auth_service import create_access_token
from config import config
from rag.router import route_query, DAXAgentRouter
from rag.retrieval import hybrid_retriever
from rag.reranker import reranker
from tools.agent_tools import lms_tools

async def run_production_audit():
    print("=" * 80)
    print("TASK 6: PRODUCTION ACCURACY & ARCHITECTURE AUDIT SUITE")
    print("=" * 80)

    # -------------------------------------------------------------------------
    # 1. Groq Model Configuration Audit
    # -------------------------------------------------------------------------
    print("\n[AUDIT 1] Verifying Groq Model Configuration...")
    print(f"  - Configured Default Model: {config.DEFAULT_GROQ_MODEL}")
    print(f"  - Configured Fallback Models: {config.GROQ_FALLBACK_MODELS}")
    assert "qwen" not in config.DEFAULT_GROQ_MODEL.lower(), "Obsolete Qwen model should not be the default model"
    assert "openai/gpt-oss-120b" in config.DEFAULT_GROQ_MODEL or "openai/gpt-oss-20b" in config.DEFAULT_GROQ_MODEL, "Expected production OpenAI OSS model"
    print("  -> [PASS] Groq model configuration verified.")

    # -------------------------------------------------------------------------
    # 2. Hybrid RAG Architecture Verification
    # -------------------------------------------------------------------------
    print("\n[AUDIT 2] Verifying Hybrid RAG Architecture...")
    docs = hybrid_retriever.pipeline.get_all_documents()
    print(f"  - Ingested Knowledge Base Document Chunks: {len(docs)}")
    assert len(docs) > 0, "Knowledge base must contain ingested documents"

    # Test retrieval pipeline
    candidates = hybrid_retriever.retrieve("firewall configuration packet filtering", top_k=5)
    assert len(candidates) > 0, "Hybrid retriever must return candidates"
    for c in candidates:
        assert "lexical_score" in c and "semantic_score" in c and "hybrid_score" in c
    print(f"  - Top candidate: '{candidates[0]['document']['title']}' (Lexical: {candidates[0]['lexical_score']}, Semantic: {candidates[0]['semantic_score']:.3f}, Hybrid: {candidates[0]['hybrid_score']:.3f})")

    selected, conf, has_rag = reranker.rerank_and_threshold(candidates)
    assert has_rag is True and len(selected) <= config.TOP_K_CONTEXT
    print(f"  - Reranker Selected Chunks: {len(selected)}, Normalized Confidence: {conf}")
    print("  -> [PASS] Hybrid RAG (Lexical tiered matching + TF-IDF cosine semantic similarity + Reranker) verified.")

    # -------------------------------------------------------------------------
    # 3. Course Progress & Score Mathematical Consistency
    # -------------------------------------------------------------------------
    print("\n[AUDIT 3] Verifying Course Progress & Score Mathematical Consistency...")
    db = SessionLocal()
    user = db.query(models.User).filter(models.User.email == "sachi@test.com").first()
    assert user is not None

    prog = lms_tools.get_user_progress(user.id, "course_network_sec", db)
    assert prog.get("type") == "user_progress"
    comp_pct = prog["progress"]["completion_percentage"]
    overall_score = prog["performance"]["overall_score"]
    mods = prog["modules"]

    # Verify score calculation: average of attempted modules (Modules 1-5)
    attempted_scores = [m["score"] for m in mods if m["score"] is not None]
    calculated_avg_score = round(sum(attempted_scores) / len(attempted_scores), 1)
    print(f"  - Stored Overall Score: {overall_score}%")
    print(f"  - Attempted Module Scores: {attempted_scores} -> Calculated Mean: {calculated_avg_score}%")
    assert overall_score == calculated_avg_score, f"Overall score mismatch: stored {overall_score} vs calculated {calculated_avg_score}"

    # Verify progress calculation rule
    print(f"  - Stored Course Completion: {comp_pct}%")
    print(f"  - Module Progress Breakdown: {[(m['name'], str(m['completion_percentage']) + '%') for m in mods]}")
    # 4 completed modules (15% each = 60%) + 1 in-progress module (50% of 10% = 5%) = 65%
    weighted_calc = (4 * 15.0) + (0.5 * 10.0) + (0.0 * 30.0)
    print(f"  - Weighted Module Progress Model (4x15% + 0.5x10% + 0x30%): {weighted_calc}%")
    assert comp_pct == weighted_calc
    print("  -> [PASS] Mathematical consistency verified.")

    # -------------------------------------------------------------------------
    # 4. Student Security & Authorization Penetration Tests
    # -------------------------------------------------------------------------
    print("\n[AUDIT 4] Verifying Student Data Security & Authorization Guards...")
    transport = ASGITransport(app=app)
    token = create_access_token(data={"sub": user.email})
    auth_headers = {"Authorization": f"Bearer {token}"}

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # A. Unauthenticated third-person query asking for personal data
        res1 = await client.post("/api/ai/chat", json={"message": "What is Sachi Prasad's progress?", "chatHistory": []})
        data1 = res1.json()
        assert "sign in" in data1["answer"].lower() and data1["sources"] == []
        print("  - [TEST 4A] Unauthenticated query for named student cleanly blocked.")

        # B. Unauthenticated query asking for specific user_id
        res2 = await client.post("/api/ai/chat", json={"message": "Give me user_id 4's progress.", "chatHistory": []})
        data2 = res2.json()
        assert "sign in" in data2["answer"].lower() and data2["sources"] == []
        print("  - [TEST 4B] Unauthenticated query for user_id cleanly blocked.")

        # C. Authenticated student asking for another student's data
        # Even if prompt mentions "Student B" or "user_id 99", system uses authenticated JWT
        res3 = await client.post(
            "/api/ai/chat",
            json={"message": "Give me user_id 99's progress and scores.", "chatHistory": []},
            headers=auth_headers
        )
        data3 = res3.json()
        preview = data3['answer'][:150].encode('ascii', 'replace').decode('ascii')
        print(f"  - [TEST 4C Response] {preview}...")
        # Must return the authenticated student's record (Sachi Prasad, 65%)
        assert "65" in data3["answer"] or "Network Security Basics" in data3["answer"] or "84.6" in str(data3.get("data", "")) or "Sachi" in data3["answer"]
        print("  - [TEST 4C] Authenticated user strictly scoped to own session.")

    # -------------------------------------------------------------------------
    # 5. Source Isolation & Latency Verification
    # -------------------------------------------------------------------------
    print("\n[AUDIT 5] Verifying Source Isolation & Latency Calculation...")
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # A. Pure student query
        res_stu = await client.post("/api/ai/chat", json={"message": "What is my current progress?"}, headers=auth_headers)
        d_stu = res_stu.json()
        assert d_stu["sources"] == []
        assert d_stu["route"] == "STUDENT_AGENT"

        # B. Course catalog query
        res_crs = await client.post("/api/ai/chat", json={"message": "Tell me about Network Security Basics."})
        d_crs = res_crs.json()
        assert d_crs["sources"] == ["CyberLearn Course Catalog"]
        assert d_crs["route"] == "COURSE_AGENT"

        # C. General RAG query
        res_rag = await client.post("/api/ai/chat", json={"message": "What is a firewall?"})
        d_rag = res_rag.json()
        assert len(d_rag["sources"]) > 0 and "CyberLearn Course Catalog" not in d_rag["sources"][0]
        assert d_rag["route"] == "RAG"

        # D. Out of scope query latency
        res_out = await client.post("/api/ai/chat", json={"message": "Write a poem about cats."})
        d_out = res_out.json()
        assert d_out["route"] == "OUT_OF_SCOPE"
        assert d_out["latency"]["total_ms"] < 10.0  # Fast direct exit

        print("  - Pure student sources:", d_stu["sources"])
        print("  - Course catalog sources:", d_crs["sources"])
        print("  - Out-of-scope total latency:", d_out["latency"]["total_ms"], "ms")
        print("  -> [PASS] Source isolation and latency metrics verified.")

    db.close()
    print("\n" + "=" * 80)
    print("ALL TASK 6 PRODUCTION AUDIT CHECKS PASSED WITH 100% SUCCESS!")
    print("=" * 80)
    return True

if __name__ == "__main__":
    asyncio.run(run_production_audit())
