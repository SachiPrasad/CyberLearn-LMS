import re
import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Intent Enum Constants
INTENT_ENROLLMENT = "ENROLLMENT"
INTENT_USER_PROGRESS = "USER_PROGRESS"
INTENT_SEGMENT_PERFORMANCE = "SEGMENT_PERFORMANCE"
INTENT_ASSESSMENT_PERFORMANCE = "ASSESSMENT_PERFORMANCE"
INTENT_LAB_PERFORMANCE = "LAB_PERFORMANCE"
INTENT_OVERALL_PERFORMANCE = "OVERALL_PERFORMANCE"
INTENT_HYBRID_EXPLAIN_AND_PROGRESS = "HYBRID_EXPLAIN_AND_PROGRESS"

INTENT_COURSE_CONTENT = "COURSE_CONTENT"
INTENT_COURSE_INFORMATION = "COURSE_INFORMATION"
INTENT_LEARNING_HELP = "LEARNING_HELP"
INTENT_COURSE_RECOMMENDATION = "COURSE_RECOMMENDATION"
INTENT_CERTIFICATION = "CERTIFICATION"
INTENT_INTERNSHIP = "INTERNSHIP"
INTENT_FAQ = "FAQ"
INTENT_OUT_OF_SCOPE = "OUT_OF_SCOPE"
INTENT_GENERAL_CONVERSATION = "GENERAL_CONVERSATION"

# Stopwords
STOP_WORDS = {
    "a", "an", "the", "in", "on", "at", "to", "for", "of", "with", "by", "from",
    "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
    "do", "does", "did", "can", "could", "should", "would", "will", "shall",
    "i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us", "them",
    "my", "your", "his", "their", "our", "its", "what", "which", "who", "whom",
    "this", "that", "these", "those", "am", "tell", "explain", "give", "show", "please"
}

# Domain Synonyms
SYNONYMS = {
    "pentest": "penetration testing",
    "pentesting": "penetration testing",
    "ethical hacker": "ethical hacking",
    "hacker": "ethical hacking",
    "sqli": "sql injection",
    "xss": "cross-site scripting",
    "csrf": "cross-site request forgery",
    "ssrf": "server-side request forgery",
    "packet capture": "packet analysis wireshark",
    "pcap": "packet analysis wireshark",
    "traffic capture": "packet analysis wireshark",
    "sniffing": "packet analysis wireshark",
    "passing score": "certification requirements passing criteria",
    "certificate": "certification requirements",
    "intern": "internship eligibility",
    "job": "internship cyberdaksh career",
    "career": "internship cyberdaksh career",
    "syllabus": "topics covered curriculum modules",
    "curriculum": "topics covered modules",
    "modules": "course modules syllabus",
    "acl": "access control list firewall",
    "acls": "access control lists firewall",
    "firewalls": "firewall configuration stateful stateless",
    "dmz": "demilitarized zone perimeter security",
    "nmap": "reconnaissance nmap port scanning",
    "metasploit": "metasploit framework exploitation",
    "burp": "burp suite web application security"
}

class QueryProcessor:
    @staticmethod
    def normalize_text(text: str) -> str:
        """Lowercases and cleans punctuation."""
        text = text.lower()
        text = re.sub(r'[\r\n\t]+', ' ', text)
        text = re.sub(r'[^\w\s\-\.\/\@\#\%]', ' ', text)
        return text.strip()

    @classmethod
    def extract_keywords_and_phrases(cls, text: str) -> Tuple[List[str], List[str]]:
        """Extracts informative keywords and 2-gram/3-gram phrases."""
        normalized = cls.normalize_text(text)
        tokens = [w for w in normalized.split() if w and w not in STOP_WORDS]
        
        phrases = []
        words = normalized.split()
        for i in range(len(words) - 1):
            phrase2 = f"{words[i]} {words[i+1]}"
            phrases.append(phrase2)
            if i < len(words) - 2:
                phrase3 = f"{words[i]} {words[i+1]} {words[i+2]}"
                phrases.append(phrase3)
                
        return tokens, phrases

    @classmethod
    def detect_intent(cls, query: str) -> str:
        """Classifies the primary intent of the user inquiry with fine-grained personal vs general routing."""
        q = query.lower()

        # Check for Hybrid Intent: Technical Explanation + Personal LMS Performance
        # e.g., "Explain firewalls and tell me my score", "Explain IDS and tell me my progress"
        has_explain = bool(re.search(r'\b(explain|difference between|how does.*work)\b', q))
        has_personal_score = bool(re.search(r'\b(my score|my grade|my progress|how did i do|my performance|tell me my)\b', q))
        if has_explain and has_personal_score:
            return INTENT_HYBRID_EXPLAIN_AND_PROGRESS

        # 1. User Enrollments ("What courses am I enrolled in?")
        if re.search(r'\b(my.*courses|enrolled in|my.*classes|what am i learning|my.*enrollment|courses.*enrolled)\b', q):
            return INTENT_ENROLLMENT

        # 2. Overall Performance ("How am I performing overall?")
        if re.search(r'\b(performing overall|overall performance|my average score|overall progress|overall standing)\b', q):
            return INTENT_OVERALL_PERFORMANCE

        # 3. Quiz / Assessment Performance ("How did I perform in the Threat Detection quiz?", "my quiz score")
        if re.search(r'\b(quiz|exam|assessment)\b', q) and re.search(r'\b(my|i|score|perform|result|grade|passed)\b', q):
            return INTENT_ASSESSMENT_PERFORMANCE

        # 4. Lab Performance ("Have I completed the Firewall lab?", "my lab progress", "did i finish the lab")
        if re.search(r'\b(lab|virtual lab|hands-on)\b', q) and re.search(r'\b(my|i|have i|completed|finished|score|done)\b', q):
            return INTENT_LAB_PERFORMANCE

        # 5. Segment Performance ("What is my score in Firewalls?", "Which segments have I completed?", "Which segments are pending?")
        if re.search(r'\b(segment|segments|completed segments|pending segments|score in\b|grade in\b|my score in|my grade in|did i complete|have i finished)\b', q):
            return INTENT_SEGMENT_PERFORMANCE
        if re.search(r'\b(which.*segments|completed.*segments|pending.*segments)\b', q):
            return INTENT_SEGMENT_PERFORMANCE

        # 6. General Course / User Progress ("What is my progress?", "How much have I completed in Network Security?")
        if re.search(r'\b(my.*progress|how much have i completed|how much.*finished|my.*completion|am i passing|progress in.*course|progress in.*first|progress in.*second)\b', q):
            return INTENT_USER_PROGRESS

        # 7. Course Comparison ("Compare Network Security Basics and Ethical Hacking", "compare two courses")
        if re.search(r'\b(compare|comparison|versus|\bvs\b|difference between.*course)\b', q):
            return INTENT_COURSE_INFORMATION

        # 8. Course Catalog & Information Queries
        # e.g., "What courses are available?", "Tell me about Network Security Basics", "What is the difficulty of this course?"
        # "How many modules does this course have?", "What topics are covered?", "What labs are included?", "What prerequisites?"
        # "What skills will I learn?", "What is CyberLearn?", "What does the CyberLearn platform offer?"
        if re.search(r'\b(what courses|available courses|all courses|list of courses|catalog|what classes|courses available|courses do you offer|courses are offered)\b', q):
            return INTENT_COURSE_INFORMATION
        if re.search(r'\b(tell me about|what is|overview of)\b.*\b(course|network security|ethical hacking|web security|cyberlearn|security)\b', q):
            return INTENT_COURSE_INFORMATION
        if re.search(r'\b(difficulty|how hard|prerequisite|prerequisites|how many modules|module count|total modules|topics covered|syllabus|curriculum|skills.*learn|what skills|labs included|what labs|what certification|course status|how long|duration|how many weeks|weeks)\b', q):
            return INTENT_COURSE_INFORMATION
        if re.search(r'\b(what is cyberlearn|about cyberlearn|platform offer|what does cyberlearn offer|what is this website)\b', q):
            return INTENT_COURSE_INFORMATION

        # 9. Certification Policy
        if re.search(r'\b(certif|certificate|certified|passing grade|passing score|75%|earn certificate)\b', q):
            return INTENT_CERTIFICATION

        # 10. Internship & Career
        if re.search(r'\b(internship|intern|cyberdaksh job|hiring|career|apply for intern|85%)\b', q):
            return INTENT_INTERNSHIP

        # 11. Course Recommendations & Guidance
        if re.search(r'\b(recommend|what course should|which course should|where should i start|beginner course|suitable for a beginner|which course is suitable|learning path)\b', q):
            return INTENT_COURSE_RECOMMENDATION

        # 12. General Platform FAQ / Labs
        if re.search(r'\b(sandbox|browser lab|how does cyberlearn work|install software)\b', q):
            return INTENT_FAQ

        # 13. Out of Scope
        if re.search(r'\b(weather|recipe|cooking|chocolate chip|stock market|football|cricket score|movie review|president)\b', q):
            return INTENT_OUT_OF_SCOPE

        # 14. General conversational greetings
        if re.match(r'^(hi|hello|hey|good morning|good evening|who are you|what is your name)\b', q):
            return INTENT_GENERAL_CONVERSATION

        # 15. Learning Help & Explanations
        if re.search(r'\b(explain|how does|how to|why does|difference between)\b', q):
            return INTENT_LEARNING_HELP

        # Default to Course Content retrieval
        return INTENT_COURSE_CONTENT

    @classmethod
    def resolve_course_from_query_and_history(
        cls,
        query: str,
        chat_history: Optional[List[Dict[str, Any]]] = None,
        enrolled_course_ids: Optional[List[str]] = None
    ) -> Optional[str]:
        """
        Extracts or infers the target course ID from the user query and conversational history.
        e.g. 'Network Security Basics' -> 'course_network_sec'
             'first one' -> resolves from prior assistant message.
        """
        q = query.lower()

        # 1. Direct name checks and typos
        if re.search(r'\b(network security basics|netwrok security basics|the network security course|the security basics course|network security|network sec|netsec|networking basics)\b', q):
            return "course_network_sec"
        if re.search(r'\b(ethical hacking & penetration testing|the ethical hacking course|ethical hacking fundamentals|ethical hacking|penetration testing|pentest)\b', q):
            return "course_ethical_hack"
        if re.search(r'\b(web application security|the web security course|the web application security course|web security|appsec|owasp)\b', q):
            return "course_web_security"

        # 2. Check multi-turn and relative references using router's extraction logic
        from rag.router import DAXAgentRouter
        ref = DAXAgentRouter.extract_course_reference(query, chat_history)
        if ref:
            if "Network Security" in ref:
                return "course_network_sec"
            elif "Ethical Hacking" in ref:
                return "course_ethical_hack"
            elif "Web" in ref:
                return "course_web_security"

        # 3. Only default to enrolled course for personal student progress queries
        is_personal_query = bool(re.search(r'\b(my|me|i|i\'m|have i|did i|enrolled|progress|score|completed|grade)\b', q))
        if is_personal_query and enrolled_course_ids and len(enrolled_course_ids) == 1:
            return enrolled_course_ids[0]

        return None

    @classmethod
    def rewrite_query(cls, query: str, chat_history: Optional[List[Dict[str, Any]]] = None) -> str:
        """
        Rewrites conversational follow-up references using recent history.
        """
        q_norm = cls.normalize_text(query)

        # Apply synonym expansions
        for k, v in SYNONYMS.items():
            if re.search(rf'\b{re.escape(k)}\b', q_norm):
                q_norm += f" {v}"

        # Resolve follow-ups if history is provided
        if chat_history and len(chat_history) > 0:
            followup_match = re.search(r'\b(the second one|the first one|the third one|the last one|that course|which one|it|this)\b', query.lower())
            if followup_match:
                last_assistant_msg = next(
                    (m.get("content", "") for m in reversed(chat_history) if m.get("role") in ("assistant", "model")),
                    ""
                )
                if last_assistant_msg:
                    q_norm = f"{q_norm} {last_assistant_msg[:200]}"

        return q_norm
