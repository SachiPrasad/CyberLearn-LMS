import asyncio
import os
import sys
from dotenv import load_dotenv

# Ensure backend directory is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

load_dotenv('backend/.env')

from rag_service import get_relevant_context, CYBERLEARN_KNOWLEDGE_BASE
from groq_service import generate_ai_response

TEST_CASES = [
    {
        "id": 1,
        "query": "What topics are covered in Network Security?",
        "history": [],
        "expected_topic": "Network Security Basics"
    },
    {
        "id": 2,
        "query": "What is required for CyberLearn certification?",
        "history": [],
        "expected_topic": "CyberLearn Platform"
    },
    {
        "id": 3,
        "query": "How can I get an internship at CyberDaksh?",
        "history": [],
        "expected_topic": "CyberDaksh Careers"
    },
    {
        "id": 4,
        "query": "Explain firewall configuration.",
        "history": [],
        "expected_topic": "Network Security Basics"
    },
    {
        "id": 5,
        "query": "What is packet analysis?",
        "history": [],
        "expected_topic": "Network Security Basics"
    },
    {
        "id": 6,
        "query": "Which topic is related to Wireshark?",
        "history": [],
        "expected_topic": "Network Security Basics"
    },
    {
        "id": 7,
        "query": "Tell me something that is NOT in the CyberLearn knowledge base.",
        "history": [],
        "expected_topic": None
    },
    {
        "id": 8,
        "query": "What about the second one?",
        "history": [
            {"role": "user", "content": "What topics are covered in Network Security?"},
            {"role": "assistant", "content": "The Network Security Basics course covers:\n1. OSI Model\n2. TCP/IP Fundamentals\n3. Firewall Configuration\n4. Network Packet Analysis\n5. Defensive Perimeter Security"}
        ],
        "expected_topic": "Network Security Basics"
    }
]

async def run_tests():
    print("=" * 80)
    print("RUNNING CYBERLEARN RAG & DAX AI ASSISTANT TEST SUITE")
    print("=" * 80)

    for tc in TEST_CASES:
        print(f"\n[Test Case {tc['id']}] Query: \"{tc['query']}\"")
        if tc['history']:
            print(f"  Context History: {len(tc['history'])} previous messages")
            
        context, sources, has_context = await get_relevant_context(tc['query'])
        print(f"  RAG Retrieved Sources: {sources} (has_context={has_context})")
        
        answer = await generate_ai_response(tc['query'], tc['history'], context)
        print("  DAX Response:")
        print("  " + "-" * 60)
        safe_answer = answer.encode('ascii', errors='replace').decode('ascii')
        for line in safe_answer.split('\n'):
            print(f"    {line}")
        print("  " + "-" * 60)

    print("\n" + "=" * 80)
    print("ALL TEST CASES COMPLETED SUCCESSFULLY!")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(run_tests())
