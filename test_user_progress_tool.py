import os
import sys
import json

# Add backend directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import models
from database import SessionLocal
from tools.agent_tools import get_user_progress, LMSAgentTools

def test_user_progress_tool():
    print("=" * 80)
    print("TEST: Verifying get_user_progress Backend LMS Tool (Task 2)")
    print("=" * 80)

    # 1. Test Demo Student Sachi Prasad (user_id = 4) without course_id
    print("\n[TEST 1] Calling get_user_progress(4)...")
    res1 = get_user_progress(4)
    print(json.dumps(res1, indent=2))

    assert res1.get("type") == "user_progress", f"Unexpected type: {res1.get('type')}"
    assert res1.get("user_id") == 4, f"Expected user_id 4, got {res1.get('user_id')}"
    assert res1.get("course", {}).get("name") == "Network Security Basics"
    assert res1.get("course", {}).get("course_id") == "course_network_sec"
    assert res1.get("enrollment", {}).get("status") == "active"
    assert res1.get("progress", {}).get("completion_percentage") == 65.0
    assert res1.get("progress", {}).get("completed_modules") == 4
    assert res1.get("progress", {}).get("total_modules") == 6
    assert res1.get("progress", {}).get("current_module") == "Firewall Configuration"
    assert res1.get("performance", {}).get("overall_score") == 84.6

    modules = res1.get("modules", [])
    assert len(modules) == 6, f"Expected 6 module records, got {len(modules)}"
    completed_mods = [m for m in modules if m.get("status") == "Completed"]
    in_progress_mods = [m for m in modules if m.get("status") == "In Progress"]
    not_started_mods = [m for m in modules if m.get("status") == "Not Started"]

    assert len(completed_mods) == 4, f"Expected 4 completed modules, got {len(completed_mods)}"
    assert len(in_progress_mods) == 1, f"Expected 1 in-progress module, got {len(in_progress_mods)}"
    assert len(not_started_mods) == 1, f"Expected 1 not-started module, got {len(not_started_mods)}"
    print("-> Test 1 Passed: Demo student progress successfully retrieved!")

    # 2. Test get_user_progress(4, "course_network_sec") with explicit course_id
    print("\n[TEST 2] Calling get_user_progress(4, 'course_network_sec')...")
    res2 = get_user_progress(4, "course_network_sec")
    assert res2.get("course", {}).get("course_id") == "course_network_sec"
    assert res2.get("progress", {}).get("completion_percentage") == 65.0
    assert len(res2.get("modules", [])) == 6
    print("-> Test 2 Passed: Explicit course_id filter retrieved identical course progress.")

    # 3. Test LMSAgentTools static method equivalence
    print("\n[TEST 3] Calling LMSAgentTools.get_user_progress(4, 'course_network_sec')...")
    res3 = LMSAgentTools.get_user_progress(4, "course_network_sec")
    assert res3 == res2
    print("-> Test 3 Passed: Static method LMSAgentTools.get_user_progress returns identical output.")

    # 4. Test Missing Data Edge Cases
    print("\n[TEST 4] Testing Missing Data & Security Edge Cases...")

    # Not enrolled course
    res_not_enrolled = get_user_progress(4, "course_ethical_hack")
    print("  - Not enrolled course:", res_not_enrolled)
    assert res_not_enrolled == {"type": "user_progress", "found": False, "reason": "not_enrolled"}

    # Non-existent course
    res_no_course = get_user_progress(4, "non_existent_course_id_123")
    print("  - Non-existent course:", res_no_course)
    assert res_no_course == {"type": "user_progress", "found": False, "reason": "course_not_found"}

    # Non-existent user
    res_no_user = get_user_progress(999999)
    print("  - Non-existent user:", res_no_user)
    assert res_no_user == {"type": "user_progress", "found": False, "reason": "user_not_found"}
    print("-> Test 4 Passed: All edge cases handled cleanly without fabricating data.")

    print("\n" + "=" * 80)
    print("ALL TESTS FOR get_user_progress PASSED WITH 100% SUCCESS!")
    print("=" * 80)
    return True

if __name__ == "__main__":
    success = test_user_progress_tool()
    if not success:
        sys.exit(1)
