import re
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Route Constants
ROUTE_STUDENT_AGENT = "STUDENT_AGENT"
ROUTE_COURSE_AGENT = "COURSE_AGENT"
ROUTE_RAG = "RAG"
ROUTE_MIXED = "MIXED"
ROUTE_GENERAL = "GENERAL"
ROUTE_OUT_OF_SCOPE = "OUT_OF_SCOPE"

# Agent Names
AGENT_STUDENT = "STUDENT_AGENT"
AGENT_COURSE = "COURSE_AGENT"
AGENT_RAG = "RAG"

class DAXAgentRouter:
    """
    Lightweight, high-precision Agent Router for the DAX Assistant.
    Decides whether an inquiry should be handled by:
    - STUDENT_AGENT (Personal LMS / DB progress, enrollments, scores)
    - COURSE_AGENT (Course catalog, difficulty, syllabus, prerequisites, comparisons, recommendations)
    - RAG (General cybersecurity explanations & technical concepts)
    - MIXED (Multiple agents required)
    - GENERAL (Website & platform overview)
    - OUT_OF_SCOPE (Unrelated queries)
    """

    @classmethod
    def extract_course_reference(cls, query: str, chat_history: Optional[List[Dict[str, Any]]] = None) -> Optional[str]:
        """
        Extracts verified course entity reference from the user query without hallucination.
        Supports typos, natural phrasing, and multi-turn conversational history.
        """
        q = query.lower()

        # Direct name checks (including common abbreviations, typos, and phrasing variations)
        if re.search(r'\b(network security basics|netwrok security basics|the network security course|the security basics course|network security|netsec|networking basics)\b', q):
            return "Network Security Basics"
        if re.search(r'\b(ethical hacking & penetration testing|the ethical hacking course|ethical hacking fundamentals|ethical hacking|penetration testing|pentest)\b', q):
            if "fundamentals" in q:
                return "Ethical Hacking Fundamentals"
            return "Ethical Hacking & Penetration Testing"
        if re.search(r'\b(web application security|the web security course|the web application security course|web security|appsec)\b', q):
            return "Web Application Security"

        # Check for relative historical references (e.g. "What about the previous course?", "earlier course")
        if chat_history and len(chat_history) > 0:
            is_prev_course_ref = bool(re.search(r'\b(previous course|earlier course|first course|prior course)\b', q))
            if is_prev_course_ref:
                # Collect sequence of distinct courses mentioned by the user in history
                distinct_courses = []
                for msg in chat_history:
                    if msg.get("role") == "user":
                        content = msg.get("content", "") or msg.get("message", "")
                        if isinstance(content, str):
                            c = cls.extract_course_reference(content, chat_history=None)
                            if c and (not distinct_courses or distinct_courses[-1] != c):
                                distinct_courses.append(c)
                if len(distinct_courses) >= 2:
                    return distinct_courses[-2]
                elif len(distinct_courses) == 1:
                    return distinct_courses[0]

            # Check follow-up pronouns or follow-up aspect queries referencing the most recent course
            is_pronoun_followup = bool(re.search(
                r'\b(its|this course|that course|the course|it|the syllabus|the prerequisites|the labs|the certification|the duration|the skills|that one|which one|what will i learn|what do i learn|learn|curriculum|topics|tell me more|details|about it|before starting|prerequisites|modules|what are they)\b',
                q
            ))
            if is_pronoun_followup:
                # Check user prompts in reverse order first
                for msg in reversed(chat_history):
                    if msg.get("role") == "user":
                        content = msg.get("content", "") or msg.get("message", "")
                        if isinstance(content, str):
                            c_found = cls.extract_course_reference(content, chat_history=None)
                            if c_found:
                                return c_found
                for msg in reversed(chat_history):
                    content = msg.get("content", "") or msg.get("message", "")
                    if isinstance(content, str):
                        c_found = cls.extract_course_reference(content, chat_history=None)
                        if c_found:
                            return c_found

        return None

    @classmethod
    def route_query(cls, query: str, chat_history: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Analyzes the user query and produces a deterministic structured routing decision.
        """
        q = query.lower().strip()
        course_ref = cls.extract_course_reference(query, chat_history)

        # ---------------------------------------------------------------------
        # 1. Out of Scope Check
        # ---------------------------------------------------------------------
        out_of_scope_pattern = r'\b(weather|recipe|cooking|chocolate chip|stock market|bitcoin|crypto price|football|cricket score|fifa|world cup|poem|love poem|poetry|cats|dog breed|movie review|president|election|actor|celebrity)\b'
        if re.search(out_of_scope_pattern, q):
            return {
                "route": ROUTE_OUT_OF_SCOPE,
                "intent": "OUT_OF_SCOPE",
                "agents": [],
                "course_reference": course_ref,
                "requires_authentication": False,
                "confidence": 0.99
            }

        # ---------------------------------------------------------------------
        # 2. Aspect Detection
        # ---------------------------------------------------------------------

        # A. Personal Student Aspect
        # Must specifically refer to student learning metrics (first-person or student identifiers)
        has_first_person = bool(re.search(r'\b(my|me|i|i\'m|i am|mine|have i|did i|am i|user_id|student.*progress|progress of|score of|\'s progress|\'s score)\b', q))
        has_student_metric = bool(re.search(r'\b(progress|score|scores|grade|grades|enrolled|enrollment|courses am i|classes am i|performing|performance|completion|completed|finished|attempts|passed|certificate earned|studying|currently studying|working on|current module|which module am i|percentage|doing|how am i doing|which module am i on)\b', q))
        has_completed_modules_q = bool(re.search(r'\b(which modules have i|how much have i completed|what have i completed|did i complete|have i finished)\b', q))
        has_student_topic_score = bool(re.search(r'\b(my score in|score in.*module|grade in|my progress in)\b', q))
        has_enrollment_q = bool(re.search(r'\b(courses am i enrolled|enrolled in|my courses|my classes)\b', q))

        has_student_aspect = (has_first_person and (has_student_metric or has_completed_modules_q)) or has_student_topic_score or has_enrollment_q

        # B. General RAG Technical Knowledge Aspect
        # Questions asking for explanations, definitions, mechanisms of security concepts
        has_explain_verb = bool(re.search(r'\b(explain|what is a|what is an|how does|how to|why does|difference between|tell me what is|definition of)\b', q))
        has_tech_concept = bool(re.search(r'\b(firewall|firewalls|wireshark|intrusion detection|ids|ips|snort|suricata|phishing|network security|osi|tcp|udp|packet analysis|ddos|dos|encryption|cryptography|sqli|sql injection|xss|csrf|ssrf|buffer overflow|nmap|metasploit|meterpreter|dmz|acl|vpn|port scanning|reconnaissance)\b', q))
        
        has_rag_aspect = (has_explain_verb and has_tech_concept) or (bool(re.match(r'^(what is|explain)\b', q)) and has_tech_concept and not re.search(r'\b(cyberlearn|course|difficulty|prerequisite|module count|progress|score|grade)\b', q))

        # C. Course Catalog / Metadata Aspect (excluding pure personal enrollment queries)
        has_course_catalog_q = bool(re.search(r'\b(search.*course|find.*course|courses with|what courses are available|available courses|all courses|list of courses|catalog|courses available|courses do you offer|courses are offered|which courses are available|cyberlearn courses|which courses can i take|which courses|show me.*courses|courses does cyberlearn offer|what courses do you offer|what courses do you have|courses you offer|courses are available)\b', q))
        has_course_metadata_q = bool(re.search(r'\b(difficulty|how hard|prerequisite|prerequisites|how many modules|module count|total modules|topics covered|syllabus|curriculum|skills.*learn|what skills|what will i learn|labs included|what labs|practical labs|practical work|hands-on|exercises|certification is associated|certificate|certification|course status|duration of|how long is|how long does.*take|how much time|how long)\b', q))
        has_course_recommend_q = bool(re.search(r'\b(recommend|what course should|which course should|which one should|which one is best|where should i start|beginner course|suitable for.*beginner|which course is suitable|best for.*beginner|learning path|which cyberlearn course|interested in|want to learn|getting started|new to cybersecurity)\b', q))
        has_course_compare_q = bool(re.search(r'\b(compare|comparison|versus|\bvs\b|difference between.*course)\b', q))
        has_course_overview_q = bool(re.search(r'\b(tell me about|overview of|details of|about the course|information on|what does.*teach|tell me what.*teaches|what.*teaches|what.*covers|what will i learn)\b', q) and (course_ref is not None or "course" in q or "that" in q)) or (bool(re.match(r'^what is\b', q)) and bool(course_ref))

        has_course_aspect = (
            has_course_catalog_q or
            has_course_metadata_q or
            has_course_recommend_q or
            has_course_compare_q or
            has_course_overview_q
        ) and not (has_enrollment_q and not has_course_metadata_q and not has_course_overview_q)

        # Pure course queries about catalog courses should not be hijacked by generic RAG
        if has_course_aspect and not has_student_aspect and not (has_explain_verb and has_tech_concept and bool(re.search(r'\b(part of|included in|taught in)\b', q))):
            has_rag_aspect = False

        # D. General Platform Aspect
        has_general_platform = bool(re.search(r'\b(what is cyberlearn|about cyberlearn|platform offer|what does cyberlearn offer|what can you help|what does dax do|who are you|features does cyberlearn have|how does cyberlearn|what can i do on cyberlearn|how does the learning platform work|can students track.*progress|does cyberlearn provide)\b', q))

        # ---------------------------------------------------------------------
        # 3. Priority-Based Routing Resolution
        # Priority: 1. MIXED -> 2. STUDENT_AGENT -> 3. COURSE_AGENT -> 4. RAG -> 5. GENERAL
        # ---------------------------------------------------------------------

        # 1. MIXED ROUTE
        # Checks if inquiry spans multiple sources
        has_mixed_course_student = (has_course_aspect or bool(re.search(r'\b(teaches|covers|syllabus|curriculum|what is.*course|what are the prerequisites|modules)\b', q))) and has_student_aspect
        has_mixed_rag_student = has_rag_aspect and has_student_aspect
        has_mixed_rag_course = has_rag_aspect and bool(course_ref) and bool(re.search(r'\b(part of|included in|taught in)\b', q))

        if has_mixed_rag_student or has_mixed_course_student or has_mixed_rag_course:
            agents = []
            if has_rag_aspect:
                agents.append(AGENT_RAG)
            if has_course_aspect or bool(course_ref) or bool(re.search(r'\b(teaches|covers|syllabus|curriculum|course|part of|included in|prerequisites|modules)\b', q)):
                agents.append(AGENT_COURSE)
            if has_student_aspect:
                agents.append(AGENT_STUDENT)

            # Ensure uniqueness while preserving order
            unique_agents = []
            for a in agents:
                if a not in unique_agents:
                    unique_agents.append(a)

            if len(unique_agents) >= 2:
                return {
                    "route": ROUTE_MIXED,
                    "intent": "MIXED_QUERY",
                    "agents": unique_agents,
                    "course_reference": course_ref,
                    "requires_authentication": AGENT_STUDENT in unique_agents,
                    "confidence": 0.96
                }

        # 2. STUDENT_AGENT ROUTE
        if has_student_aspect:
            fine_intent = "USER_PROGRESS"
            if re.search(r'\b(enrolled|enrollment|my courses|my classes)\b', q):
                fine_intent = "ENROLLMENT"
            elif re.search(r'\b(quiz|exam|assessment|threat detection quiz)\b', q):
                fine_intent = "ASSESSMENT_PERFORMANCE"
            elif re.search(r'\b(lab|virtual lab|wireshark lab|firewall lab)\b', q):
                fine_intent = "LAB_PERFORMANCE"
            elif re.search(r'\b(score in|grade in|firewall configuration score|which modules)\b', q):
                fine_intent = "SEGMENT_PERFORMANCE"
            elif re.search(r'\b(performing overall|overall performance|average score)\b', q):
                fine_intent = "OVERALL_PERFORMANCE"

            return {
                "route": ROUTE_STUDENT_AGENT,
                "intent": fine_intent,
                "agents": [AGENT_STUDENT],
                "course_reference": course_ref,
                "requires_authentication": True,
                "confidence": 0.98
            }

        # 3. COURSE_AGENT ROUTE
        if has_course_aspect:
            fine_intent = "COURSE_INFORMATION"
            if has_course_catalog_q:
                fine_intent = "COURSE_INFORMATION"
            elif has_course_recommend_q:
                fine_intent = "COURSE_RECOMMENDATION"
            elif has_course_compare_q:
                fine_intent = "COURSE_COMPARISON"
            elif re.search(r'\b(module|modules|syllabus|curriculum|what will i learn)\b', q):
                fine_intent = "COURSE_MODULES"
            elif re.search(r'\b(prerequisite|prerequisites|prior|requirements before|what should i know)\b', q):
                fine_intent = "COURSE_PREREQUISITES"
            elif re.search(r'\b(how long|duration|weeks|how much time)\b', q):
                fine_intent = "COURSE_DURATION"
            elif re.search(r'\b(lab|labs|practical|hands-on|virtual lab|sandbox)\b', q):
                fine_intent = "COURSE_LABS"
            elif re.search(r'\b(certificate|certification|verified certificate)\b', q):
                fine_intent = "COURSE_CERTIFICATION"
            elif re.search(r'\b(skill|skills|what will i be able to do|outcomes)\b', q):
                fine_intent = "COURSE_SKILLS"
            elif has_course_overview_q or (bool(course_ref) and re.search(r'\b(what is|tell me about)\b', q)):
                fine_intent = "COURSE_OVERVIEW"

            return {
                "route": ROUTE_COURSE_AGENT,
                "intent": fine_intent,
                "agents": [AGENT_COURSE],
                "course_reference": course_ref,
                "requires_authentication": False,
                "confidence": 0.95
            }

        # 4. RAG ROUTE
        if has_rag_aspect:
            return {
                "route": ROUTE_RAG,
                "intent": "LEARNING_HELP",
                "agents": [AGENT_RAG],
                "course_reference": course_ref,
                "requires_authentication": False,
                "confidence": 0.94
            }

        # 5. GENERAL ROUTE
        if has_general_platform:
            return {
                "route": ROUTE_GENERAL,
                "intent": "PLATFORM_INFO",
                "agents": [AGENT_COURSE],
                "course_reference": None,
                "requires_authentication": False,
                "confidence": 0.95
            }

        # Conversational greetings or default fallback
        if re.match(r'^(hi|hello|hey|good morning|good evening|who are you)\b', q):
            return {
                "route": ROUTE_GENERAL,
                "intent": "GENERAL_CONVERSATION",
                "agents": [],
                "course_reference": None,
                "requires_authentication": False,
                "confidence": 0.99
            }

        # Default fallback to RAG curriculum search
        return {
            "route": ROUTE_RAG,
            "intent": "COURSE_CONTENT",
            "agents": [AGENT_RAG],
            "course_reference": course_ref,
            "requires_authentication": False,
            "confidence": 0.85
        }

# Global Router Function
def route_query(query: str, chat_history: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """Convenience functional wrapper for DAX Agent Router."""
    return DAXAgentRouter.route_query(query, chat_history=chat_history)
