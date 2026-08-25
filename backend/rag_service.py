CYBERDAKSH_DOCS = [
    {
        "topic": "certification",
        "content": "To get a CyberLearn certification, you must complete 100% of the course modules, finish all practical labs, and pass the final assessment with a minimum score of 75%."
    },
    {
        "topic": "internship",
        "content": "CyberDaksh offers internships to top-performing students who complete the Ethical Hacking or Web Security tracks with an 'A' grade."
    }
]

async def get_relevant_context(query: str) -> str:
    """
    SIMPLE RAG LOGIC:
    Checks if the user's query contains a topic we have docs for.
    """
    query_lower = query.lower()
    for doc in CYBERDAKSH_DOCS:
        if doc["topic"] in query_lower:
            return f"Use this specific info to answer: {doc['content']}"
            
    return "Answer as a general cybersecurity assistant."
