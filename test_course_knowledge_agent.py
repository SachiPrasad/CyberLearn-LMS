import os
import sys
import asyncio

# Add backend directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from database import SessionLocal
import models
from tools.agent_tools import (
    search_courses,
    get_course_information,
    get_course_modules,
    get_course_prerequisites,
    get_course_duration,
    get_course_labs,
    get_course_certification,
    get_course_skills,
    recommend_courses,
    compare_courses,
    get_platform_info,
    lms_tools
)
from rag.router import route_query, DAXAgentRouter
from rag_service import get_relevant_context
from groq_service import generate_ai_response

async def run_task7_course_agent_tests():
    print("=" * 80)
    print("TEST SUITE: TASK 7 Complete Course & Platform Intelligence Verification")
    print("=" * 80)

    # -------------------------------------------------------------------------
    # PART 1: Unit Testing Granular Course Tools
    # -------------------------------------------------------------------------
    print("\n--- [PART 1: Unit Testing Granular Course Tools] ---")
    
    # 1. Course Overview
    c_info = get_course_information("course_network_sec")
    assert c_info["course_name"] == "Network Security Basics"
    assert c_info["difficulty"] == "Beginner"
    assert c_info["duration"] == "6 weeks"
    print("  [PASS] 1. get_course_information")

    # 2. Course Modules
    c_mods = get_course_modules("course_network_sec")
    assert c_mods["total_modules"] == 6
    assert len(c_mods["module_names"]) == 6
    assert "Module 1" in c_mods["module_names"][0]
    print("  [PASS] 2. get_course_modules")

    # 3. Prerequisites
    c_prereq = get_course_prerequisites("course_network_sec")
    assert len(c_prereq["prerequisites"]) >= 1
    assert "literacy" in c_prereq["prerequisites"][0].lower()
    print("  [PASS] 3. get_course_prerequisites")

    # 4. Duration
    c_dur = get_course_duration("course_network_sec")
    assert c_dur["duration"] == "6 weeks"
    print("  [PASS] 4. get_course_duration")

    # 5. Labs
    c_labs = get_course_labs("course_network_sec")
    assert c_labs["total_labs"] == 3
    assert any("Wireshark" in l for l in c_labs["lab_list"])
    print("  [PASS] 5. get_course_labs")

    # 6. Certification
    c_cert = get_course_certification("course_network_sec")
    assert "75%" in c_cert["certification"]
    assert "CyberDaksh" in c_cert["certification"]
    print("  [PASS] 6. get_course_certification")

    # 7. Skills
    c_skills = get_course_skills("course_network_sec")
    assert "Wireshark" in c_skills["skills"]
    assert len(c_skills["learning_objectives"]) >= 3
    print("  [PASS] 7. get_course_skills")

    # 8. Course Search
    s_res = search_courses("courses for networking")
    assert s_res["count"] >= 1
    assert s_res["courses"][0]["course_id"] == "course_network_sec"
    print("  [PASS] 8. search_courses")

    # 9. Course Comparison
    comp = compare_courses("course_network_sec", "course_ethical_hack")
    assert comp["valid_comparison"] is True
    assert comp["course_1"]["difficulty"] == "Beginner"
    assert comp["course_2"]["difficulty"] == "Intermediate"
    print("  [PASS] 9. compare_courses")

    # 10. Course Recommendation
    rec = recommend_courses("beginner looking for cyber foundation")
    assert rec["recommended_course"]["course_id"] == "course_network_sec"
    assert "beginner" in rec["reason"].lower()
    print("  [PASS] 10. recommend_courses")

    # 11. Platform Info
    p_info = get_platform_info()
    assert p_info["name"] == "CyberLearn LMS"
    assert p_info["operator"] == "CyberDaksh"
    print("  [PASS] 11. get_platform_info")

    # 12. Unknown Course
    unknown = get_course_information("course_quantum_crypto_999")
    assert unknown is None
    print("  [PASS] 12. Unknown course returns None cleanly")

    # 13. Comparison with non-existent course
    comp_invalid = compare_courses("course_network_sec", "non_existent_course")
    assert comp_invalid["valid_comparison"] is False
    print("  [PASS] 13. Comparison with non-existent course handled gracefully")

    # 14. Follow-up query course resolution
    history = [
        {"role": "user", "content": "What is Network Security Basics?"},
        {"role": "assistant", "content": "Network Security Basics is a 6-week beginner course..."}
    ]
    ref = DAXAgentRouter.extract_course_reference("What are its prerequisites?", chat_history=history)
    assert ref == "Network Security Basics"
    print("  [PASS] 14. Follow-up course pronoun resolution ('its' -> 'Network Security Basics')")

    # 15. Mixed Course + Student query routing
    mixed_route = route_query("What does Network Security Basics teach and how much have I completed?")
    assert mixed_route["route"] == "MIXED"
    assert "COURSE_AGENT" in mixed_route["agents"] and "STUDENT_AGENT" in mixed_route["agents"]
    print("  [PASS] 15. Mixed Course + Student query routing verified")

    # -------------------------------------------------------------------------
    # PART 2: End-to-End Context & AI Response Verification (All 15 Scenarios)
    # -------------------------------------------------------------------------
    print("\n--- [PART 2: Testing 15 End-to-End Course & Platform AI Scenarios] ---")

    test_scenarios = [
        ("1. What is Network Security Basics?", "COURSE_AGENT", "COURSE_OVERVIEW", "CyberLearn Course Catalog"),
        ("2. What modules are in Network Security Basics?", "COURSE_AGENT", "COURSE_MODULES", "CyberLearn Course Catalog"),
        ("3. What are the prerequisites for Network Security Basics?", "COURSE_AGENT", "COURSE_PREREQUISITES", "CyberLearn Course Catalog"),
        ("4. How long is Network Security Basics?", "COURSE_AGENT", "COURSE_DURATION", "CyberLearn Course Catalog"),
        ("5. Does Network Security Basics have labs?", "COURSE_AGENT", "COURSE_LABS", "CyberLearn Course Catalog"),
        ("6. What certification does Network Security Basics provide?", "COURSE_AGENT", "COURSE_CERTIFICATION", "CyberLearn Course Catalog"),
        ("7. What skills will I gain in Network Security Basics?", "COURSE_AGENT", "COURSE_SKILLS", "CyberLearn Course Catalog"),
        ("8. Search for courses with Wireshark.", "COURSE_AGENT", "COURSE_INFORMATION", "CyberLearn Course Catalog"),
        ("9. Compare Network Security Basics and Ethical Hacking.", "COURSE_AGENT", "COURSE_COMPARISON", "CyberLearn Course Catalog"),
        ("10. Which CyberLearn course should a beginner take?", "COURSE_AGENT", "COURSE_RECOMMENDATION", "CyberLearn Course Catalog"),
        ("11. What is CyberLearn?", "GENERAL", "PLATFORM_INFO", "CyberLearn Course Catalog"),
        ("12. Tell me about Quantum Cryptography 501.", "COURSE_AGENT", "COURSE_INFORMATION", "CyberLearn Course Catalog"),
        ("13. What courses are available?", "COURSE_AGENT", "COURSE_INFORMATION", "CyberLearn Course Catalog"),
        ("14. What are its prerequisites?", "COURSE_AGENT", "COURSE_PREREQUISITES", "CyberLearn Course Catalog"),  # with history
        ("15. What does Network Security Basics teach and how much have I completed?", "MIXED", "MIXED_QUERY", "CyberLearn Course Catalog")
    ]

    db = SessionLocal()
    demo_user = db.query(models.User).filter(models.User.email == "sachi@test.com").first()

    for idx, (q_raw, exp_route, exp_intent, exp_source) in enumerate(test_scenarios, 1):
        query = q_raw.split(". ", 1)[1]
        print(f"\n[SCENARIO {idx}] \"{query}\"")

        # Set chat history for scenario 14
        active_history = history if idx == 14 else []

        decision = route_query(query, chat_history=active_history)
        print(f"  - Router: route={decision['route']}, intent={decision['intent']}, course={decision.get('course_reference')}")

        ctx, sources, has_ctx, detected_intent, conf, doc_ids, struct_data = await get_relevant_context(
            query=query,
            chat_history=active_history,
            user=demo_user,
            db=db,
            intent=decision.get("intent"),
            route=decision.get("route")
        )

        answer, model_used, latency_ms = await generate_ai_response(
            user_text=query,
            chat_history=active_history,
            context=ctx,
            intent=detected_intent
        )

        answer_preview = answer[:100].replace('\n', ' ').encode('ascii', 'replace').decode('ascii')
        print(f"  - Groq ({model_used}, {latency_ms:.1f}ms): {answer_preview}...")

        assert has_ctx is True or len(ctx) > 0
        assert exp_source in sources

    db.close()
    print("\n" + "=" * 80)
    print("ALL 15 TASK 7 COURSE & PLATFORM INTELLIGENCE TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(run_task7_course_agent_tests())
