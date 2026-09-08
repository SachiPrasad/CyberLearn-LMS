import logging
import re
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session
import models
from config import config
from knowledge.ingestion import kb_pipeline
from rag.query_processor import (
    QueryProcessor,
    INTENT_ENROLLMENT,
    INTENT_USER_PROGRESS,
    INTENT_SEGMENT_PERFORMANCE,
    INTENT_ASSESSMENT_PERFORMANCE,
    INTENT_LAB_PERFORMANCE,
    INTENT_OVERALL_PERFORMANCE,
    INTENT_HYBRID_EXPLAIN_AND_PROGRESS,
    INTENT_COURSE_CONTENT,
    INTENT_COURSE_INFORMATION,
    INTENT_COURSE_RECOMMENDATION,
    INTENT_LEARNING_HELP,
    INTENT_OUT_OF_SCOPE,
    INTENT_GENERAL_CONVERSATION
)
from rag.retrieval import hybrid_retriever
from rag.reranker import reranker
from rag.context_builder import context_builder
from tools.agent_tools import lms_tools

logger = logging.getLogger(__name__)

CYBERLEARN_KNOWLEDGE_BASE = kb_pipeline.get_all_documents()

async def get_relevant_context(
    query: str,
    chat_history: Optional[List[Dict[str, Any]]] = None,
    user: Optional[models.User] = None,
    db: Optional[Session] = None,
    intent: Optional[str] = None,
    route: Optional[str] = None,
    top_k: int = config.TOP_K_RETRIEVAL,
    min_score_threshold: float = config.MIN_RELEVANCE_SCORE
) -> Tuple[str, List[str], bool, str, float, List[str], Optional[Dict[str, Any]]]:
    """
    Production Multi-Stage LMS & RAG Pipeline:
    1. Query Preprocessing & Normalization
    2. Intent Classification (Personal LMS DB query vs General Curriculum RAG vs Hybrid)
    3. Secure Database Querying (strictly authenticated user_id, IDOR protected)
    4. RAG Retrieval & Context Assembly for general knowledge
    5. Clean separation: Personal queries have sources=[] to avoid attaching false RAG docs.

    Returns:
        - context_str: Verified context for generation
        - sources: List of source document names (empty for pure DB queries)
        - has_relevant_context: Boolean flag
        - intent: Detected intent
        - confidence: Confidence score
        - doc_ids: List of document IDs used
        - structured_data: JSON structured payload for frontend card rendering
    """
    # 1. Query Normalization & Input Validation
    normalized_q = QueryProcessor.normalize_text(query[:config.MAX_QUERY_LENGTH])
    if not normalized_q:
        return "NO_CYBERLEARN_CONTEXT_FOUND", [], False, INTENT_GENERAL_CONVERSATION, 0.0, [], None

    # 2. Intent Detection (use router intent if supplied)
    if not intent:
        intent = QueryProcessor.detect_intent(query)
    logger.info(f"LMS/RAG Pipeline: Active intent '{intent}' (route='{route}') for query: '{query[:60]}...'")

    # Get enrolled course IDs for course resolution
    enrolled_ids = []
    if user and db:
        user_enrollments = db.query(models.Enrollment).filter(models.Enrollment.user_id == user.id).all()
        enrolled_ids = [e.course_id for e in user_enrollments]

    # Resolve course if query or context specifies one
    resolved_course_id = QueryProcessor.resolve_course_from_query_and_history(
        query=query,
        chat_history=chat_history,
        enrolled_course_ids=enrolled_ids
    )

    # =========================================================================
    # PERSONAL LMS DATABASE INTENTS (Sources MUST be empty, Zero RAG Docs)
    # =========================================================================

    if intent == INTENT_ENROLLMENT:
        if user and db:
            enr_res = lms_tools.get_user_enrollments(user.id, db)
            enrs = enr_res.get("enrollments", [])
            if enrs:
                lines = [
                    f"{idx+1}. **{e['course_name']}** (Status: {e['status']}, Completion: {e['completion_percentage']}%, Overall Score: {e['overall_score'] or 'N/A'}/100)"
                    for idx, e in enumerate(enrs)
                ]
                ctx = (
                    "<verified_cyberlearn_context>\n"
                    f"AUTHENTICATED ENROLLMENTS FOR STUDENT {user.name or user.email}:\n"
                    + "\n".join(lines) + "\n"
                    "Instructions: Present the active enrolled courses clearly to the student. Do not invent any courses.\n"
                    "</verified_cyberlearn_context>"
                )
                return ctx, [], True, intent, 1.0, ["db_enrollments"], enr_res
            else:
                ctx = (
                    "<verified_cyberlearn_context>\n"
                    f"Student {user.name or user.email} is currently not enrolled in any courses.\n"
                    "</verified_cyberlearn_context>"
                )
                return ctx, [], True, intent, 0.95, ["db_enrollments"], enr_res

    if intent == INTENT_USER_PROGRESS:
        if user and db:
            # If a specific course was resolved
            if resolved_course_id:
                prog = lms_tools.get_course_progress(user.id, resolved_course_id, db)
                if prog:
                    seg_lines = [
                        f"  - Segment {s['segment_number']}: {s['segment_name']} -> Status: {s['status']}, Score: {s['score'] if s['score'] is not None else '—'}/100, Completion: {s['completion_percentage']}%"
                        for s in prog["segments"]
                    ]
                    ctx = (
                        "<verified_cyberlearn_context>\n"
                        f"STUDENT PROGRESS RECORD FOR: {prog['course_name']} (Student: {user.name or user.email})\n"
                        f"- Overall Course Completion: {prog['completion_percentage']}%\n"
                        f"- Overall Calculated Score: {prog['overall_score']}/100\n"
                        f"- Status: {prog['status']}\n"
                        f"- Completed Segments: {prog['completed_segments']} of {prog['total_segments']}\n"
                        f"- Last Activity Date: {prog['last_accessed']}\n"
                        "Segment Breakdown:\n"
                        + "\n".join(seg_lines) + "\n"
                        "Instructions: Report the student's exact course progress, completion percentage, overall score, and segment statuses from this record. Do NOT hallucinate different scores.\n"
                        "</verified_cyberlearn_context>"
                    )
                    return ctx, [], True, intent, 1.0, ["db_user_progress"], prog

            # If user has multiple courses and didn't specify
            multi_prog = lms_tools.get_user_progress(user.id, db=db)
            courses = multi_prog.get("courses", [])
            if len(courses) == 1:
                prog = courses[0]
                seg_lines = [
                    f"  - Segment {s['segment_number']}: {s['segment_name']} -> Status: {s['status']}, Score: {s['score'] if s['score'] is not None else '—'}/100, Completion: {s['completion_percentage']}%"
                    for s in prog["segments"]
                ]
                ctx = (
                    "<verified_cyberlearn_context>\n"
                    f"STUDENT PROGRESS RECORD FOR: {prog['course_name']} (Student: {user.name or user.email})\n"
                    f"- Overall Course Completion: {prog['completion_percentage']}%\n"
                    f"- Overall Calculated Score: {prog['overall_score']}/100\n"
                    f"- Status: {prog['status']}\n"
                    f"- Completed Segments: {prog['completed_segments']} of {prog['total_segments']}\n"
                    f"- Last Activity Date: {prog['last_accessed']}\n"
                    "Segment Breakdown:\n"
                    + "\n".join(seg_lines) + "\n"
                    "</verified_cyberlearn_context>"
                )
                return ctx, [], True, intent, 1.0, ["db_user_progress"], prog
            elif len(courses) > 1:
                summary_lines = [
                    f"{idx+1}. **{c['course_name']}**: {c['completion_percentage']}% complete (Overall Score: {c['overall_score']}/100, {c['completed_segments']}/{c['total_segments']} segments completed, Last active: {c['last_accessed']})"
                    for idx, c in enumerate(courses)
                ]
                ctx = (
                    "<verified_cyberlearn_context>\n"
                    f"STUDENT ENROLLED COURSES PROGRESS OVERVIEW FOR {user.name or user.email}:\n"
                    + "\n".join(summary_lines) + "\n\n"
                    "Instructions: Summarize the progress across all enrolled courses and ask which specific course the student would like more details about.\n"
                    "</verified_cyberlearn_context>"
                )
                return ctx, [], True, intent, 0.98, ["db_user_progress"], multi_prog

    if intent == INTENT_SEGMENT_PERFORMANCE:
        if user and db:
            q_lower = query.lower()
            status_filter = None
            if re.search(r'\b(completed|finished|done)\b', q_lower) and not re.search(r'\b(pending|remaining|not started|incomplete)\b', q_lower):
                status_filter = "Completed"
            elif re.search(r'\b(pending|remaining|incomplete|not completed|still pending)\b', q_lower):
                status_filter = "pending"

            # Check ModuleProgress records (Task 1 model)
            target_kw = "Firewall" if "firewall" in q_lower else ("Intrusion Detection" if ("ids" in q_lower or "intrusion" in q_lower) else ("Wireshark" if "wireshark" in q_lower else ("Threat" if "threat" in q_lower else None)))
            mod_query = db.query(models.ModuleProgress).filter(models.ModuleProgress.user_id == user.id)
            if target_kw:
                mod_query = mod_query.filter(models.ModuleProgress.module_name.ilike(f"%{target_kw}%"))
            mod_records = mod_query.all()

            lines = []
            for m in mod_records:
                score_str = f"Score: {m.score}%" if m.score is not None else "Score: Not attempted yet"
                lines.append(f"- **Module: {m.module_name}**: Status = {m.module_status}, {score_str}, Completion = {m.completion_percentage}%")

            # Also check CourseSegment & StudentSegmentPerformance
            res = lms_tools.get_segment_performance(
                user_id=user.id,
                course_id=resolved_course_id,
                segment_name=target_kw,
                status_filter=status_filter,
                db=db
            )
            segs = res.get("segments", [])
            for s in segs:
                score_str = f"Score: {s['score']}/100" if s['score'] is not None else "Score: Not attempted yet"
                lines.append(f"- **Segment: {s['segment_name']}** ({s['course_name']}): Status = {s['status']}, {score_str}, Completion = {s['completion_percentage']}%, Attempts = {s['attempts']}")

            ctx = (
                "<verified_cyberlearn_context>\n"
                f"STUDENT MODULE & SEGMENT PERFORMANCE RECORDS FOR {user.name or user.email}:\n"
                + ("\n".join(lines) if lines else "No performance records matching the criteria were found.") + "\n\n"
                "Instructions: Clearly state the student's exact numerical score (e.g. Score: 76.0 / 100) separately from their completion percentage (e.g. 60.0% completion). Do NOT confuse score with completion percentage. State the score directly.\n"
                "</verified_cyberlearn_context>"
            )
            return ctx, [], True, intent, 1.0, ["db_segment_performance"], {"modules": [m.module_name for m in mod_records], "segments": segs}

    if intent == INTENT_ASSESSMENT_PERFORMANCE:
        if user and db:
            q_lower = query.lower()
            a_name = None
            if "threat detection" in q_lower:
                a_name = "Threat Detection"
            elif "network fundamentals" in q_lower:
                a_name = "Network Fundamentals"
            elif "network threats" in q_lower:
                a_name = "Network Threats"
            elif "firewall" in q_lower:
                a_name = "Firewall"
            elif "ids" in q_lower:
                a_name = "IDS"

            res = lms_tools.get_assessment_performance(user_id=user.id, assessment_name=a_name, db=db)
            assessments = res.get("assessments", [])
            lines = [
                f"- **{a['assessment_name']}** ({a['course_name']}): Score: {a['score']}/{a['max_score']}, Status: {a['status']}, Attempts: {a['attempts']}, Submitted: {a['submitted_at']}"
                for a in assessments
            ]
            ctx = (
                "<verified_cyberlearn_context>\n"
                f"STUDENT ASSESSMENT & QUIZ PERFORMANCE RECORDS FOR {user.name or user.email}:\n"
                + ("\n".join(lines) if lines else "No assessment submissions found for the specified topic.") + "\n"
                "Instructions: Answer with the student's exact quiz score, status, and attempt count from this record.\n"
                "</verified_cyberlearn_context>"
            )
            return ctx, [], True, intent, 1.0, ["db_assessments"], res

    if intent == INTENT_LAB_PERFORMANCE:
        if user and db:
            q_lower = query.lower()
            lab_kw = None
            if "firewall" in q_lower:
                lab_kw = "Firewall"
            elif "wireshark" in q_lower or "packet" in q_lower:
                lab_kw = "Wireshark"
            elif "snort" in q_lower or "ids" in q_lower:
                lab_kw = "Snort"
            elif "nmap" in q_lower:
                lab_kw = "Nmap"
            elif "recon" in q_lower:
                lab_kw = "Reconnaissance"

            res = lms_tools.get_lab_performance(user_id=user.id, lab_name=lab_kw, db=db)
            labs = res.get("labs", [])
            lines = [
                f"- **{l['lab_name']}** ({l['course_name']}): Status: {l['status']}, Score: {l['score'] or 'N/A'}/100, Attempts: {l['attempts']}, Completed At: {l['completed_at'] or 'In Progress'}"
                for l in labs
            ]
            ctx = (
                "<verified_cyberlearn_context>\n"
                f"STUDENT HANDS-ON LAB PERFORMANCE RECORDS FOR {user.name or user.email}:\n"
                + ("\n".join(lines) if lines else "No lab submission records matching the inquiry were found.") + "\n"
                "Instructions: Report whether the lab has been completed, its status, score, and attempts from these records.\n"
                "</verified_cyberlearn_context>"
            )
            return ctx, [], True, intent, 1.0, ["db_labs"], res

    if intent == INTENT_OVERALL_PERFORMANCE:
        if user and db:
            res = lms_tools.get_overall_performance(user_id=user.id, db=db)
            ctx = (
                "<verified_cyberlearn_context>\n"
                f"CUMULATIVE STUDENT PERFORMANCE SUMMARY FOR {user.name or user.email}:\n"
                f"- Enrolled Courses: {res['enrolled_courses_count']}\n"
                f"- Average Performance Score: {res['average_score']}/100\n"
                f"- Completed Segments: {res['completed_segments']} of {res['total_tracked_segments']}\n"
                f"- Segments In Progress: {res['in_progress_segments']}\n"
                f"- Quizzes Passed: {res['quizzes_passed']}\n"
                f"- Labs Completed: {res['labs_completed']}\n"
                "Instructions: Provide an encouraging, analytical overview of the student's cumulative learning performance across all enrolled courses.\n"
                "</verified_cyberlearn_context>"
            )
            return ctx, [], True, intent, 1.0, ["db_overall_performance"], res

    # =========================================================================
    # HYBRID & MIXED INTENTS (RAG Knowledge + Course Catalog + Personal LMS DB)
    # =========================================================================

    if intent in (INTENT_HYBRID_EXPLAIN_AND_PROGRESS, "MIXED_QUERY") or (
        bool(re.search(r'\b(explain|what is)\b', query.lower())) and bool(re.search(r'\b(my score|my progress|how much have i completed|what have i completed)\b', query.lower()))
    ) or (
        bool(re.search(r'\b(teaches|about the course)\b', query.lower())) and bool(re.search(r'\b(how much have i completed|what have i completed|my progress)\b', query.lower()))
    ):
        ctx_parts = []
        sources = []
        doc_ids = []
        structured_data = {}
        q_lower = query.lower()

        # 1. Technical explanation aspect (RAG)
        has_tech_explain = bool(re.search(r'\b(explain|what is|how does)\b.*\b(firewall|wireshark|intrusion|ids|ips|nmap|metasploit|sqli|xss|csrf|tcp|osi)\b', q_lower)) or bool(re.search(r'\b(explain firewalls|explain wireshark|what is a firewall)\b', q_lower))
        if has_tech_explain:
            rewritten = QueryProcessor.rewrite_query(query, chat_history)
            candidates = hybrid_retriever.retrieve(rewritten, top_k=top_k)
            selected_candidates, _, _ = reranker.rerank_and_threshold(
                candidates, top_k_context=config.TOP_K_CONTEXT, min_relevance_score=min_score_threshold
            )
            rag_context, rag_sources, r_doc_ids = context_builder.build_context(selected_candidates)
            if rag_context:
                ctx_parts.append(f"<knowledge_context>\n{rag_context}\n</knowledge_context>")
                for s in rag_sources:
                    if s not in sources:
                        sources.append(s)
                doc_ids.extend(r_doc_ids)

        # 2. Course catalog aspect (COURSE_AGENT)
        target_cid = resolved_course_id or "course_network_sec"
        has_course_q = bool(re.search(r'\b(teaches|curriculum|syllabus|part of|included in|network security|ethical hacking|web security)\b', q_lower))
        if has_course_q:
            cinfo = lms_tools.get_course_information(target_cid)
            if cinfo:
                course_text = (
                    f"<course_context>\n"
                    f"COURSE: {cinfo['course_name']} ({cinfo['course_id']})\n"
                    f"- Category: {cinfo['category']} | Difficulty: {cinfo['difficulty']} | Duration: {cinfo['duration']}\n"
                    f"- Description: {cinfo['description']}\n"
                    f"- Modules ({cinfo['modules']}): {', '.join(cinfo['topics'])}\n"
                    f"- Virtual Labs ({cinfo['labs']}): {', '.join(cinfo['lab_list'])}\n"
                    f"- Core Skills: {', '.join(cinfo['skills'])}\n"
                    f"</course_context>"
                )
                ctx_parts.append(course_text)
                if "CyberLearn Course Catalog" not in sources:
                    sources.append("CyberLearn Course Catalog")
                structured_data["course"] = cinfo

        # 3. Student LMS Progress / Score aspect (STUDENT_AGENT)
        if user and db:
            student_text_lines = []
            prog = lms_tools.get_user_progress(user.id, target_cid, db)
            if prog and prog.get("type") == "user_progress":
                student_text_lines.append(
                    f"STUDENT ENROLLMENT & PROGRESS FOR {user.name or user.email}:\n"
                    f"- Course: {prog['course']['name']}\n"
                    f"- Enrollment Status: {prog['enrollment']['status']}\n"
                    f"- Overall Course Completion: {prog['progress']['completion_percentage']}%\n"
                    f"- Completed Modules: {prog['progress']['completed_modules']} of {prog['progress']['total_modules']}\n"
                    f"- Current Module: {prog['progress']['current_module']}\n"
                    f"- Overall Score: {prog['performance']['overall_score']}%\n"
                    f"- Last Activity: {prog['progress']['last_activity']}"
                )
                structured_data["progress"] = prog

                # Specific module/segment breakdown
                topic_kw = "Firewall" if "firewall" in q_lower else ("Intrusion Detection" if ("ids" in q_lower or "intrusion" in q_lower) else ("Wireshark" if "wireshark" in q_lower else None))
                if topic_kw:
                    matching_mods = [m for m in prog.get("modules", []) if topic_kw.lower() in m["name"].lower()]
                    for m in matching_mods:
                        score_val = f"{m['score']}%" if m['score'] is not None else "Not started"
                        student_text_lines.append(f"- Personal Module Score for '{m['name']}': {score_val} (Status: {m['status']}, Completion: {m['completion_percentage']}%)")

            if student_text_lines:
                ctx_parts.append(
                    f"<student_lms_context>\n"
                    + "\n".join(student_text_lines) + "\n"
                    f"</student_lms_context>"
                )

        combined_ctx = (
            "\n\n".join(ctx_parts) + "\n\n"
            "<verified_cyberlearn_context>\n"
            "Instructions: Provide a clear, structured response synthesizing the verified knowledge, course metadata, and student personal records above.\n"
            "CRITICAL: If the user asked about course topics/curriculum AND their personal completion/score, you MUST explicitly include BOTH sections in your answer:\n"
            "1. Course Curriculum / Topics taught\n"
            "2. Student Personal Progress (including exact completion percentage %, completed modules, and scores from the verified student record).\n"
            "Do NOT invent scores or facts.\n"
            "</verified_cyberlearn_context>"
        )

        return combined_ctx, sources, True, intent, 0.98, doc_ids, structured_data

    # =========================================================================
    # COURSE INFORMATION & CATALOG INTENTS
    # =========================================================================

    if intent in (
        INTENT_COURSE_INFORMATION,
        "COURSE_OVERVIEW",
        "COURSE_MODULES",
        "COURSE_PREREQUISITES",
        "COURSE_DURATION",
        "COURSE_LABS",
        "COURSE_CERTIFICATION",
        "COURSE_SKILLS",
        "COURSE_COMPARISON",
        "COURSE_RECOMMENDATION",
        "PLATFORM_INFO"
    ) or route == "COURSE_AGENT":
        q_lower = query.lower()

        # 1. Course Comparison ("Compare Network Security Basics and Ethical Hacking", "Compare two available courses")
        if intent == "COURSE_COMPARISON" or re.search(r'\b(compare|comparison|versus|\bvs\b)\b', q_lower):
            c1 = "course_network_sec"
            c2 = "course_ethical_hack"
            if "web" in q_lower and ("ethical" in q_lower or "hacking" in q_lower):
                c1 = "course_ethical_hack"
                c2 = "course_web_security"
            elif "web" in q_lower and "network" in q_lower:
                c1 = "course_network_sec"
                c2 = "course_web_security"
            elif resolved_course_id:
                c1 = resolved_course_id
                c2 = "course_ethical_hack" if resolved_course_id != "course_ethical_hack" else "course_network_sec"

            comp = lms_tools.compare_courses(c1, c2)
            if comp and comp.get("valid_comparison", True):
                c1_data = comp["course_1"]
                c2_data = comp["course_2"]
                ctx = (
                    "<course_context>\n"
                    f"COURSE COMPARISON: {c1_data['course_name']} vs {c2_data['course_name']}\n\n"
                    f"1. **{c1_data['course_name']}** ({c1_data['course_id']}):\n"
                    f"   - Category: {c1_data['category']}\n"
                    f"   - Difficulty: {c1_data['difficulty']}\n"
                    f"   - Duration: {c1_data['duration']}\n"
                    f"   - Total Modules: {c1_data['modules']}\n"
                    f"   - Total Virtual Labs: {c1_data['labs']}\n"
                    f"   - Prerequisites: {', '.join(c1_data['prerequisites'])}\n"
                    f"   - Core Skills: {', '.join(c1_data['skills'])}\n\n"
                    f"2. **{c2_data['course_name']}** ({c2_data['course_id']}):\n"
                    f"   - Category: {c2_data['category']}\n"
                    f"   - Difficulty: {c2_data['difficulty']}\n"
                    f"   - Duration: {c2_data['duration']}\n"
                    f"   - Total Modules: {c2_data['modules']}\n"
                    f"   - Total Virtual Labs: {c2_data['labs']}\n"
                    f"   - Prerequisites: {', '.join(c2_data['prerequisites'])}\n"
                    f"   - Core Skills: {', '.join(c2_data['skills'])}\n\n"
                    "Instructions: Provide a clear, objective side-by-side comparison of these two courses based only on these verified attributes. Never invent courses.\n"
                    "</course_context>"
                )
                return ctx, ["CyberLearn Course Catalog"], True, "COURSE_COMPARISON", 1.0, ["catalog_comparison"], comp

        # 2. General Platform Query ("What is CyberLearn?", "What does the platform offer?")
        if intent == "PLATFORM_INFO" or re.search(r'\b(what is cyberlearn|about cyberlearn|platform offer|what does cyberlearn offer|what can i do on cyberlearn|how does cyberlearn|does cyberlearn provide|can students track|tell me about security|about security)\b', q_lower):
            pinfo = lms_tools.get_platform_info()
            feat_lines = [f"- {f}" for f in pinfo["key_features"]]
            track_lines = [f"- {t}" for t in pinfo["tracks"]]
            ctx = (
                "<course_context>\n"
                f"ABOUT CYBERLEARN LMS (Operated by {pinfo['operator']}):\n"
                f"{pinfo['description']}\n\n"
                "Key Platform Features & Offerings:\n"
                + "\n".join(feat_lines) + "\n\n"
                "Available Learning Tracks:\n"
                + "\n".join(track_lines) + "\n\n"
                "Instructions: Present CyberLearn's platform capabilities, learning tracks, and hands-on virtual labs accurately.\n"
                "</course_context>"
            )
            return ctx, ["CyberLearn Course Catalog"], True, "PLATFORM_INFO", 1.0, ["catalog_platform_info"], pinfo

        # 3. Available Courses / Catalog Search ("What courses are available?", "which courses can I take?", "show me all available courses", etc.)
        if not resolved_course_id and (
            intent == "COURSE_INFORMATION" or
            re.search(r'\b(search.*course|find.*course|courses with|what courses|available courses|all courses|list of courses|catalog|courses available|courses do you offer|courses are offered|which courses|courses can i take|show me.*courses|courses does cyberlearn offer|cyberlearn courses|courses you offer|courses are available)\b', q_lower)
        ):
            search_res = lms_tools.search_courses(query)
            courses = search_res.get("courses", [])
            lines = [
                f"{idx+1}. **{c['course_name']}** ({c['course_id']})\n"
                f"   - Category: {c['category']} | Difficulty: {c['difficulty']} | Duration: {c.get('duration', 'N/A')}\n"
                f"   - Modules: {c['modules']} | Virtual Labs: {c['labs']}\n"
                f"   - Description: {c['description']}\n"
                f"   - Skills: {', '.join(c['skills'])}"
                for idx, c in enumerate(courses)
            ]
            ctx = (
                "<course_context>\n"
                "OFFICIAL CYBERLEARN COURSE CATALOG:\n\n"
                + "\n\n".join(lines) + "\n\n"
                "Instructions: Present the list of all active CyberLearn courses clearly with their difficulty levels and key skills. Do not invent courses.\n"
                "</course_context>"
            )
            return ctx, ["CyberLearn Course Catalog"], True, "COURSE_INFORMATION", 1.0, ["catalog_all_courses"], search_res

        # 4. Course Recommendation Intent
        if intent == "COURSE_RECOMMENDATION" or re.search(r'\b(recommend|what course should|which course should|where should i start|beginner course|suitable for a beginner|which course is suitable|best for beginners|learning path|which cyberlearn course)\b', q_lower):
            rec = lms_tools.recommend_courses(criteria=query)
            rc = rec["recommended_course"]
            alts = [f"- **{a['course_name']}** ({a['difficulty']})" for a in rec.get("alternative_courses", [])]
            ctx = (
                "<course_context>\n"
                f"RECOMMENDED COURSE FOR LEARNER:\n"
                f"- Recommended Course: **{rc['course_name']}** ({rc['difficulty']})\n"
                f"- Category: {rc['category']}\n"
                f"- Duration: {rc['duration']}\n"
                f"- Prerequisites: {', '.join(rc['prerequisites'])}\n"
                f"- Key Skills Learned: {', '.join(rc['skills'])}\n"
                f"- Reason: {rec['reason']}\n\n"
                "Alternative CyberLearn Tracks:\n"
                + "\n".join(alts) + "\n\n"
                "Instructions: Provide a structured, tailored recommendation explaining why this course fits the student's background based only on verified metadata.\n"
                "</course_context>"
            )
            return ctx, ["CyberLearn Course Catalog"], True, "COURSE_RECOMMENDATION", 1.0, ["catalog_recommendation"], rec

        # 5. Granular Specific Course Information
        if not resolved_course_id:
            # Ambiguous query without specified course context
            ctx = (
                "<course_context>\n"
                "No specific CyberLearn course was specified in the query or conversation history.\n"
                "Active CyberLearn Courses:\n"
                "1. Network Security Basics (Beginner, 6 weeks, 6 modules)\n"
                "2. Ethical Hacking & Penetration Testing (Intermediate, 8 weeks, 8 modules)\n"
                "3. Web Application Security (Intermediate, 6 weeks, 6 modules)\n"
                "Instructions: Politely ask the user which course they would like to know about from the 3 active courses above. Do NOT assume or guess a specific course.\n"
                "</course_context>"
            )
            return ctx, ["CyberLearn Course Catalog"], True, "COURSE_CLARIFICATION", 0.95, ["catalog_ambiguous"], None

        target_cid = resolved_course_id
        cinfo = lms_tools.get_course_information(target_cid)

        if not cinfo:
            # Course not found in catalog
            ctx = (
                "<course_context>\n"
                f"The requested course is not found in the CyberLearn course catalog.\n"
                "Available CyberLearn Courses:\n"
                "1. Network Security Basics (Beginner, Defensive Security, 6 weeks)\n"
                "2. Ethical Hacking & Penetration Testing (Intermediate, Offensive Security, 8 weeks)\n"
                "3. Web Application Security (Intermediate, Application Security, 6 weeks)\n"
                "Instructions: Politely inform the user that the requested course is not currently offered and present the 3 available courses.\n"
                "</course_context>"
            )
            return ctx, ["CyberLearn Course Catalog"], True, "COURSE_INFORMATION", 0.95, ["catalog_not_found"], None

        # A. Modules / Syllabus Sub-Intent
        if intent == "COURSE_MODULES" or re.search(r'\b(module|modules|syllabus|curriculum|what will i learn|show me the syllabus|module list)\b', q_lower):
            mod_lines = []
            for m in cinfo.get("module_details", []):
                mod_lines.append(f"- **Module {m['module_number']}: {m['name']}**\n  {m['description']}")
            if not mod_lines:
                mod_lines = [f"- {t}" for t in cinfo.get("topics", [])]

            ctx = (
                "<course_context>\n"
                f"VERIFIED CURRICULUM SYLLABUS FOR: {cinfo['course_name']} ({cinfo['course_id']})\n"
                f"Total Modules: {cinfo['modules']}\n\n"
                + "\n\n".join(mod_lines) + "\n\n"
                "Instructions: Present the ordered syllabus and module breakdown accurately from this verified record.\n"
                "</course_context>"
            )
            return ctx, ["CyberLearn Course Catalog"], True, "COURSE_MODULES", 1.0, ["catalog_modules"], cinfo

        # B. Prerequisites Sub-Intent
        if intent == "COURSE_PREREQUISITES" or re.search(r'\b(prerequisite|prerequisites|prior|requirements before|what should i know|need prior)\b', q_lower):
            prereq_lines = [f"- {p}" for p in cinfo.get("prerequisites", [])]
            ctx = (
                "<course_context>\n"
                f"VERIFIED PREREQUISITES FOR: {cinfo['course_name']} ({cinfo['course_id']})\n"
                f"Difficulty Level: {cinfo['difficulty']}\n"
                "Prerequisites:\n"
                + "\n".join(prereq_lines) + "\n\n"
                "Instructions: State only the verified prerequisites for this course. Do NOT invent additional prerequisites.\n"
                "</course_context>"
            )
            return ctx, ["CyberLearn Course Catalog"], True, "COURSE_PREREQUISITES", 1.0, ["catalog_prerequisites"], cinfo

        # C. Duration Sub-Intent
        if intent == "COURSE_DURATION" or re.search(r'\b(how long|duration|weeks|how much time|time does this course take)\b', q_lower):
            ctx = (
                "<course_context>\n"
                f"VERIFIED DURATION FOR: {cinfo['course_name']} ({cinfo['course_id']})\n"
                f"- Duration: {cinfo['duration']}\n"
                f"- Total Modules: {cinfo['modules']}\n"
                f"- Total Virtual Labs: {cinfo['labs']}\n"
                "Instructions: Answer with the verified duration of the course.\n"
                "</course_context>"
            )
            return ctx, ["CyberLearn Course Catalog"], True, "COURSE_DURATION", 1.0, ["catalog_duration"], cinfo

        # D. Labs Sub-Intent
        if intent == "COURSE_LABS" or re.search(r'\b(lab|labs|practical|hands-on|virtual lab|sandbox|exercises)\b', q_lower):
            lab_lines = [f"- {l}" for l in cinfo.get("lab_list", [])]
            ctx = (
                "<course_context>\n"
                f"VERIFIED HANDS-ON VIRTUAL LABS FOR: {cinfo['course_name']} ({cinfo['course_id']})\n"
                f"Total Virtual Labs: {cinfo['labs']}\n"
                "Hands-On Lab Sandboxes:\n"
                + "\n".join(lab_lines) + "\n\n"
                "Instructions: Detail the verified hands-on virtual labs and sandbox exercises included with this course.\n"
                "</course_context>"
            )
            return ctx, ["CyberLearn Course Catalog"], True, "COURSE_LABS", 1.0, ["catalog_labs"], cinfo

        # E. Certification Sub-Intent
        if intent == "COURSE_CERTIFICATION" or re.search(r'\b(certificate|certification|verified certificate|credential)\b', q_lower):
            ctx = (
                "<course_context>\n"
                f"VERIFIED CERTIFICATION REQUIREMENTS FOR: {cinfo['course_name']} ({cinfo['course_id']})\n"
                f"- Certification: {cinfo['certification']}\n"
                f"- Issuer: CyberDaksh Verified Certificate Authority\n"
                "Instructions: State the exact certification criteria and passing threshold for this course.\n"
                "</course_context>"
            )
            return ctx, ["CyberLearn Course Catalog"], True, "COURSE_CERTIFICATION", 1.0, ["catalog_certification"], cinfo

        # F. Skills Sub-Intent
        if intent == "COURSE_SKILLS" or re.search(r'\b(skill|skills|what will i be able to do|outcomes|learning objectives)\b', q_lower):
            skill_lines = [f"- {s}" for s in cinfo.get("skills", [])]
            obj_lines = [f"- {o}" for o in cinfo.get("learning_objectives", [])]
            ctx = (
                "<course_context>\n"
                f"VERIFIED SKILLS & LEARNING OBJECTIVES FOR: {cinfo['course_name']} ({cinfo['course_id']})\n"
                "Core Skills Acquired:\n"
                + "\n".join(skill_lines) + "\n\n"
                "Learning Objectives:\n"
                + "\n".join(obj_lines) + "\n\n"
                "Instructions: Highlight the practical cybersecurity skills and learning outcomes the student will gain.\n"
                "</course_context>"
            )
            return ctx, ["CyberLearn Course Catalog"], True, "COURSE_SKILLS", 1.0, ["catalog_skills"], cinfo

        # G. General Course Overview
        topic_lines = [f"  - {t}" for t in cinfo.get("topics", [])]
        lab_lines = [f"  - {l}" for l in cinfo.get("lab_list", [])]
        obj_lines = [f"  - {o}" for o in cinfo.get("learning_objectives", [])]
        
        ctx = (
            "<course_context>\n"
            f"STRUCTURED COURSE DETAILS FOR: {cinfo['course_name']} ({cinfo['course_id']})\n"
            f"- Category: {cinfo['category']}\n"
            f"- Difficulty Level: {cinfo['difficulty']}\n"
            f"- Duration: {cinfo['duration']}\n"
            f"- Description: {cinfo['description']}\n"
            f"- Total Modules: {cinfo['modules']}\n"
            f"- Total Virtual Labs: {cinfo['labs']}\n"
            f"- Prerequisites: {', '.join(cinfo['prerequisites'])}\n"
            f"- Skills Covered: {', '.join(cinfo['skills'])}\n"
            f"- Certification: {cinfo['certification']}\n"
            f"- Course Status: {cinfo['course_status']}\n\n"
            "Learning Objectives:\n"
            + "\n".join(obj_lines) + "\n\n"
            "Curriculum Modules:\n"
            + "\n".join(topic_lines) + "\n\n"
            "Hands-On Virtual Labs:\n"
            + "\n".join(lab_lines) + "\n\n"
            "Instructions: Answer the question using this verified course specification. Do NOT invent prerequisites, duration, or module counts.\n"
            "</course_context>"
        )
        return ctx, ["CyberLearn Course Catalog"], True, "COURSE_OVERVIEW", 1.0, ["catalog_course_info"], cinfo

    # =========================================================================
    # GENERAL KNOWLEDGE RAG RETRIEVAL & COMBINED COURSE + RAG QUERIES
    # =========================================================================

    rewritten_query = QueryProcessor.rewrite_query(query, chat_history)
    candidates = hybrid_retriever.retrieve(rewritten_query, top_k=top_k)
    selected_candidates, confidence, has_context = reranker.rerank_and_threshold(
        candidates,
        top_k_context=config.TOP_K_CONTEXT,
        min_relevance_score=min_score_threshold
    )
    context_str, sources, doc_ids = context_builder.build_context(selected_candidates)

    # Check for Combined Course Catalog + Concept RAG (e.g. "Explain Wireshark and tell me whether it is part of Network Security Basics")
    if resolved_course_id:
        cinfo = lms_tools.get_course_information(resolved_course_id)
        if cinfo:
            course_summary = (
                f"\n<verified_cyberlearn_context>\n"
                f"COURSE CATALOG VERIFICATION FOR: {cinfo['course_name']}\n"
                f"- Course ID: {cinfo['course_id']}\n"
                f"- Modules ({cinfo['modules']}): {', '.join(cinfo['topics'])}\n"
                f"- Virtual Labs ({cinfo['labs']}): {', '.join(cinfo['lab_list'])}\n"
                f"- Skills: {', '.join(cinfo['skills'])}\n"
                f"</verified_cyberlearn_context>"
            )
            context_str = f"{context_str}\n{course_summary}"
            if "CyberLearn Course Catalog" not in sources:
                sources.append("CyberLearn Course Catalog")

    return context_str, sources, has_context, intent, confidence, doc_ids, None

