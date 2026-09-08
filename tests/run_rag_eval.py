import asyncio
import json
import os
import sys
import time
from sqlalchemy.orm import Session

# Add backend directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import models
from database import engine
from rag_service import get_relevant_context
from groq_service import generate_ai_response

async def run_evaluation():
    print("=" * 80)
    print("CYBERLEARN LMS DAX ASSISTANT -- 30-TEST RAG EVALUATION BENCHMARK")
    print("=" * 80)

    eval_path = os.path.join(os.path.dirname(__file__), "rag_eval.json")
    with open(eval_path, "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    models.Base.metadata.create_all(bind=engine)

    # Setup demo user for db progress/enrollment testing
    with Session(engine) as db:
        test_user = db.query(models.User).filter(models.User.email == "student@cyberlearn.com").first()
        if not test_user:
            test_user = models.User(email="student@cyberlearn.com", name="Alex Learner", hashed_password=None)
            db.add(test_user)
            db.commit()
            db.refresh(test_user)

        existing_enr = db.query(models.Enrollment).filter(models.Enrollment.user_id == test_user.id).first()
        if not existing_enr:
            enr = models.Enrollment(user_id=test_user.id, course_id="course_network_sec", status="active")
            prog = models.UserProgress(
                user_id=test_user.id,
                course_id="course_network_sec",
                completed_modules=2,
                completed_labs=1,
                completion_percentage=40.0,
                assessment_score=80.0
            )
            db.add(enr)
            db.add(prog)
            db.commit()

        results = []
        total_retrieval_ms = 0.0
        total_gen_ms = 0.0

        for tc in test_cases:
            tc_id = tc["id"]
            query = tc["query"]
            category = tc.get("category", "general")
            expected_sources = tc.get("expected_sources", [])
            must_include = tc.get("must_include", [])

            t0 = time.perf_counter()
            context, sources, has_context, intent, confidence, doc_ids = await get_relevant_context(
                query=query,
                chat_history=tc.get("history", []),
                user=test_user,
                db=db
            )
            retrieval_ms = (time.perf_counter() - t0) * 1000.0
            total_retrieval_ms += retrieval_ms

            # LLM Generation
            answer, model_used, gen_ms = await generate_ai_response(
                user_text=query,
                chat_history=tc.get("history", []),
                context=context,
                intent=intent
            )
            total_gen_ms += gen_ms

            # Metric Calculations:
            # 1. Retrieval Recall / Precision
            if expected_sources:
                overlap = set(sources).intersection(set(expected_sources))
                precision = len(overlap) / len(sources) if sources else 0.0
                recall = len(overlap) / len(expected_sources) if expected_sources else 1.0
            else:
                precision = 1.0 if not has_context or not sources else 0.5
                recall = 1.0

            # 2. Content correctness check
            answer_lower = answer.lower()
            matched_keywords = [kw for kw in must_include if kw.lower() in answer_lower]
            correctness = (len(matched_keywords) / len(must_include)) if must_include else 1.0

            # 3. Grounding / Fallback check for out_of_scope
            if category in ("out_of_scope", "unverified_fact"):
                grounding_valid = ("not currently available in the cyberlearn knowledge base" in answer_lower or not has_context)
            else:
                grounding_valid = bool(has_context) if expected_sources else True

            passed = (correctness >= 0.6) and (recall >= 0.5 or not expected_sources) and grounding_valid

            results.append({
                "id": tc_id,
                "category": category,
                "query": query,
                "intent": intent,
                "confidence": confidence,
                "sources": sources,
                "precision": precision,
                "recall": recall,
                "correctness": correctness,
                "grounding_valid": grounding_valid,
                "retrieval_ms": round(retrieval_ms, 2),
                "gen_ms": round(gen_ms, 2),
                "passed": passed
            })

            status_symbol = "PASS" if passed else "WARN"
            print(f"[{status_symbol}] Test #{tc_id:02d} ({category:18s}): \"{query[:45]:45s}\" | Intent: {intent:20s} | {retrieval_ms:5.1f}ms + {gen_ms:5.1f}ms")
            await asyncio.sleep(0.8)

        # Summary statistics
        n = len(results)
        passed_count = sum(1 for r in results if r["passed"])
        avg_precision = sum(r["precision"] for r in results) / n
        avg_recall = sum(r["recall"] for r in results) / n
        avg_correctness = sum(r["correctness"] for r in results) / n
        avg_retrieval_ms = total_retrieval_ms / n
        avg_gen_ms = total_gen_ms / n

        print("\n" + "=" * 80)
        print("RAG EVALUATION METRICS REPORT")
        print("=" * 80)
        print(f"Total Test Cases Evaluated:   {n}")
        print(f"Tests Passed:                  {passed_count} / {n} ({passed_count/n*100:.1f}%)")
        print(f"Average Retrieval Precision:   {avg_precision * 100:.1f}%")
        print(f"Average Retrieval Recall:      {avg_recall * 100:.1f}%")
        print(f"Average Grounded Correctness:  {avg_correctness * 100:.1f}%")
        print(f"Average Retrieval Latency:     {avg_retrieval_ms:.2f} ms")
        print(f"Average Generation Latency:    {avg_gen_ms:.2f} ms")
        print(f"Average Total Latency:         {avg_retrieval_ms + avg_gen_ms:.2f} ms")
        print("=" * 80)

        # Save evaluation summary to json
        out_path = os.path.join(os.path.dirname(__file__), "rag_eval_results.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump({
                "summary": {
                    "total_tests": n,
                    "passed_tests": passed_count,
                    "pass_rate_pct": round(passed_count / n * 100, 2),
                    "avg_precision_pct": round(avg_precision * 100, 2),
                    "avg_recall_pct": round(avg_recall * 100, 2),
                    "avg_correctness_pct": round(avg_correctness * 100, 2),
                    "avg_retrieval_latency_ms": round(avg_retrieval_ms, 2),
                    "avg_generation_latency_ms": round(avg_gen_ms, 2),
                    "avg_total_latency_ms": round(avg_retrieval_ms + avg_gen_ms, 2)
                },
                "details": results
            }, f, indent=2)

if __name__ == "__main__":
    asyncio.run(run_evaluation())
