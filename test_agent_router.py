import os
import sys
import json

# Add backend directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from rag.router import (
    route_query,
    DAXAgentRouter,
    ROUTE_STUDENT_AGENT,
    ROUTE_COURSE_AGENT,
    ROUTE_RAG,
    ROUTE_MIXED,
    ROUTE_GENERAL,
    ROUTE_OUT_OF_SCOPE,
    AGENT_STUDENT,
    AGENT_COURSE,
    AGENT_RAG
)

def test_dax_agent_router():
    print("=" * 80)
    print("TEST SUITE: TASK 4 DAX Lightweight Agent Router Verification")
    print("=" * 80)

    test_cases = [
        {
            "id": 1,
            "query": "What is my current progress?",
            "expected_route": ROUTE_STUDENT_AGENT,
            "expected_agents": [AGENT_STUDENT],
            "expected_auth": True
        },
        {
            "id": 2,
            "query": "What courses am I enrolled in?",
            "expected_route": ROUTE_STUDENT_AGENT,
            "expected_agents": [AGENT_STUDENT],
            "expected_auth": True
        },
        {
            "id": 3,
            "query": "What is my score in Firewall Configuration?",
            "expected_route": ROUTE_STUDENT_AGENT,
            "expected_agents": [AGENT_STUDENT],
            "expected_auth": True
        },
        {
            "id": 4,
            "query": "Tell me about Network Security Basics.",
            "expected_route": ROUTE_COURSE_AGENT,
            "expected_agents": [AGENT_COURSE],
            "expected_course": "Network Security Basics",
            "expected_auth": False
        },
        {
            "id": 5,
            "query": "What are the prerequisites for Network Security Basics?",
            "expected_route": ROUTE_COURSE_AGENT,
            "expected_agents": [AGENT_COURSE],
            "expected_course": "Network Security Basics",
            "expected_auth": False
        },
        {
            "id": 6,
            "query": "What courses are available?",
            "expected_route": ROUTE_COURSE_AGENT,
            "expected_agents": [AGENT_COURSE],
            "expected_auth": False
        },
        {
            "id": 7,
            "query": "What is a firewall?",
            "expected_route": ROUTE_RAG,
            "expected_agents": [AGENT_RAG],
            "expected_auth": False
        },
        {
            "id": 8,
            "query": "Explain Wireshark.",
            "expected_route": ROUTE_RAG,
            "expected_agents": [AGENT_RAG],
            "expected_auth": False
        },
        {
            "id": 9,
            "query": "Explain firewalls and tell me my score.",
            "expected_route": ROUTE_MIXED,
            "expected_agents": [AGENT_RAG, AGENT_STUDENT],
            "expected_auth": True
        },
        {
            "id": 10,
            "query": "Tell me what Network Security Basics teaches and how much I have completed.",
            "expected_route": ROUTE_MIXED,
            "expected_agents": [AGENT_COURSE, AGENT_STUDENT],
            "expected_course": "Network Security Basics",
            "expected_auth": True
        },
        {
            "id": 11,
            "query": "What is CyberLearn?",
            "expected_route": [ROUTE_GENERAL, ROUTE_COURSE_AGENT],
            "expected_auth": False
        },
        {
            "id": 12,
            "query": "Write a poem about cats.",
            "expected_route": ROUTE_OUT_OF_SCOPE,
            "expected_agents": [],
            "expected_auth": False
        }
    ]

    all_passed = True

    for tc in test_cases:
        decision = route_query(tc["query"])
        print(f"\n[TEST {tc['id']}] Query: \"{tc['query']}\"")
        print("  -> Decision:", json.dumps(decision, indent=2))

        # Check route
        exp_r = tc["expected_route"]
        if isinstance(exp_r, list):
            assert decision["route"] in exp_r, f"Expected route in {exp_r}, got {decision['route']}"
        else:
            assert decision["route"] == exp_r, f"Expected route {exp_r}, got {decision['route']}"

        # Check agents
        if "expected_agents" in tc:
            assert decision["agents"] == tc["expected_agents"], f"Expected agents {tc['expected_agents']}, got {decision['agents']}"

        # Check course reference if expected
        if "expected_course" in tc:
            assert decision["course_reference"] == tc["expected_course"], f"Expected course {tc['expected_course']}, got {decision['course_reference']}"

        # Check auth requirement
        assert decision["requires_authentication"] == tc["expected_auth"], f"Expected requires_authentication={tc['expected_auth']}, got {decision['requires_authentication']}"

        print(f"  [PASS] Test {tc['id']} passed!")

    print("\n" + "=" * 80)
    print("ALL 12 AGENT ROUTER UNIT TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 80)
    return True

if __name__ == "__main__":
    success = test_dax_agent_router()
    if not success:
        sys.exit(1)
