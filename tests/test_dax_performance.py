import os
import sys
import time
import statistics
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

def calculate_stats(samples: List[float]) -> Dict[str, float]:
    """Calculates comprehensive statistics for latency benchmarking."""
    if not samples:
        return {"count": 0, "mean": 0.0, "median": 0.0, "min": 0.0, "max": 0.0, "p95": 0.0}
    sorted_samples = sorted(samples)
    count = len(sorted_samples)
    mean_val = statistics.mean(sorted_samples)
    median_val = statistics.median(sorted_samples)
    min_val = min(sorted_samples)
    max_val = max(sorted_samples)
    p95_idx = int(0.95 * count) - 1 if count >= 20 else count - 1
    p95_val = sorted_samples[max(0, p95_idx)]
    return {
        "count": count,
        "mean": round(mean_val, 2),
        "median": round(median_val, 2),
        "min": round(min_val, 2),
        "max": round(max_val, 2),
        "p95": round(p95_val, 2)
    }

async def run_dax_performance_benchmark():
    print("=" * 80)
    print("TASK 9: DAX PRODUCTION LATENCY BENCHMARK & PERFORMANCE AUDIT")
    print("=" * 80)

    transport = ASGITransport(app=app)
    db = SessionLocal()
    demo_user = db.query(models.User).filter(models.User.email == "sachi@test.com").first()
    assert demo_user is not None, "Demo student user must exist in DB."
    token = create_access_token(data={"sub": demo_user.email})
    auth_headers = {"Authorization": f"Bearer {token}"}

    results: Dict[str, List[float]] = {
        "course": [],
        "student": [],
        "rag": [],
        "mixed": [],
        "out_of_scope": []
    }

    # 10 Course Queries
    course_queries = [
        "What courses are available?",
        "Tell me about Network Security Basics.",
        "What are the prerequisites for Network Security Basics?",
        "How long is Network Security Basics?",
        "What modules are in Network Security Basics?",
        "Does Network Security Basics have labs?",
        "What certification does Network Security Basics provide?",
        "What skills will I gain in Network Security Basics?",
        "Compare Network Security Basics and Ethical Hacking.",
        "What is CyberLearn?"
    ]

    # 10 Student Queries (Authenticated)
    student_queries = [
        "What is my current progress?",
        "How much have I completed?",
        "What is my score in Firewall Configuration?",
        "What courses am I enrolled in?",
        "What is my completion percentage?",
        "Which module am I currently on?",
        "What have I completed so far?",
        "What is my overall score?",
        "Show my module progress.",
        "How am I doing in Network Security Basics?"
    ]

    # 10 RAG Queries (General Conceptual Cybersecurity)
    rag_queries = [
        "What is a firewall?",
        "Explain Wireshark.",
        "How does packet inspection work?",
        "What is the difference between IDS and IPS?",
        "What is SQL injection?",
        "Explain the OSI 7 layer model.",
        "What is cross-site scripting (XSS)?",
        "How do VPNs work?",
        "What is port scanning?",
        "What is a buffer overflow?"
    ]

    # 10 Mixed Queries (Combination RAG + Course + Student)
    mixed_queries = [
        "Explain firewalls and tell me my Firewall score.",
        "Tell me what Network Security Basics teaches and how much I have completed.",
        "Explain Wireshark and tell me whether it is part of my course.",
        "What is an IDS and what is my progress in that module?",
        "Explain SQL injection and is it in Web Application Security?",
        "Tell me about cryptography and what was my score in that module.",
        "What is Nmap and what course teaches it?",
        "Explain firewalls, tell me if it is in Network Security Basics, and show my progress.",
        "What is network defense and how much of my course have I completed?",
        "Explain packet sniffing and tell me what module teaches Wireshark."
    ]

    # 10 Out-of-Scope Queries
    out_of_scope_queries = [
        "Write a poem about cats.",
        "Who is the president of France?",
        "Give me a chocolate cake recipe.",
        "Write a python script for Bitcoin trading.",
        "Tell me a joke about airplanes.",
        "What is the weather in Tokyo today?",
        "How do I fix my car engine?",
        "Explain the plot of Inception.",
        "Translate hello to Japanese.",
        "What is the capital of Australia?"
    ]

    async with AsyncClient(transport=transport, base_url="http://test") as client:

        # ---------------------------------------------------------------------
        # 1. Benchmark Course Queries (10 samples)
        # ---------------------------------------------------------------------
        print("\n[1/5] Benchmarking Course Queries (10 requests)...")
        for idx, q in enumerate(course_queries, 1):
            t0 = time.perf_counter()
            resp = await client.post("/api/ai/chat", json={"message": q})
            dur_ms = (time.perf_counter() - t0) * 1000.0
            assert resp.status_code == 200, f"Failed course query: {q}"
            results["course"].append(dur_ms)
            print(f"  [{idx:02d}/10] Course: \"{q[:45]}\" -> {dur_ms:.1f}ms (model={resp.json().get('model_used')})")

        # ---------------------------------------------------------------------
        # 2. Benchmark Student Queries (10 samples)
        # ---------------------------------------------------------------------
        print("\n[2/5] Benchmarking Student Queries (10 requests)...")
        for idx, q in enumerate(student_queries, 1):
            t0 = time.perf_counter()
            resp = await client.post("/api/ai/chat", json={"message": q}, headers=auth_headers)
            dur_ms = (time.perf_counter() - t0) * 1000.0
            assert resp.status_code == 200, f"Failed student query: {q}"
            results["student"].append(dur_ms)
            print(f"  [{idx:02d}/10] Student: \"{q[:45]}\" -> {dur_ms:.1f}ms (model={resp.json().get('model_used')})")

        # ---------------------------------------------------------------------
        # 3. Benchmark Out-of-Scope Queries (10 samples)
        # ---------------------------------------------------------------------
        print("\n[3/5] Benchmarking Out-of-Scope Queries (10 requests)...")
        for idx, q in enumerate(out_of_scope_queries, 1):
            t0 = time.perf_counter()
            resp = await client.post("/api/ai/chat", json={"message": q})
            dur_ms = (time.perf_counter() - t0) * 1000.0
            assert resp.status_code == 200, f"Failed out-of-scope query: {q}"
            results["out_of_scope"].append(dur_ms)
            print(f"  [{idx:02d}/10] Out-of-Scope: \"{q[:45]}\" -> {dur_ms:.1f}ms (model={resp.json().get('model_used')})")

        # ---------------------------------------------------------------------
        # 4. Benchmark RAG Queries (10 samples)
        # ---------------------------------------------------------------------
        print("\n[4/5] Benchmarking RAG Queries (10 requests)...")
        for idx, q in enumerate(rag_queries, 1):
            t0 = time.perf_counter()
            resp = await client.post("/api/ai/chat", json={"message": q})
            dur_ms = (time.perf_counter() - t0) * 1000.0
            assert resp.status_code == 200, f"Failed RAG query: {q}"
            results["rag"].append(dur_ms)
            print(f"  [{idx:02d}/10] RAG: \"{q[:45]}\" -> {dur_ms:.1f}ms (model={resp.json().get('model_used')})")

        # ---------------------------------------------------------------------
        # 5. Benchmark Mixed Queries (10 samples)
        # ---------------------------------------------------------------------
        print("\n[5/5] Benchmarking Mixed Queries (10 requests)...")
        for idx, q in enumerate(mixed_queries, 1):
            t0 = time.perf_counter()
            resp = await client.post("/api/ai/chat", json={"message": q}, headers=auth_headers)
            dur_ms = (time.perf_counter() - t0) * 1000.0
            assert resp.status_code == 200, f"Failed mixed query: {q}"
            results["mixed"].append(dur_ms)
            print(f"  [{idx:02d}/10] Mixed: \"{q[:45]}\" -> {dur_ms:.1f}ms (model={resp.json().get('model_used')})")

    db.close()

    # -------------------------------------------------------------------------
    # Comprehensive Performance Report
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("TASK 9 LATENCY BENCHMARK REPORT (All measurements in Milliseconds):")
    print("=" * 80)
    print(f"{'Category':<15} | {'Count':<5} | {'Mean (ms)':<10} | {'Median (ms)':<11} | {'Min (ms)':<10} | {'Max (ms)':<10} | {'p95 (ms)':<10}")
    print("-" * 80)

    for cat in ["course", "student", "out_of_scope", "rag", "mixed"]:
        st = calculate_stats(results[cat])
        print(f"{cat.capitalize():<15} | {st['count']:<5} | {st['mean']:<10.1f} | {st['median']:<11.1f} | {st['min']:<10.1f} | {st['max']:<10.1f} | {st['p95']:<10.1f}")

    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(run_dax_performance_benchmark())
