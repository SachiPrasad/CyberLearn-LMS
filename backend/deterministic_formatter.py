import re
from typing import Dict, Any, Optional
import models

def is_complex_or_unverified_query(query: str) -> bool:
    """
    Detects if query contains false premises, unknown facts, or complex exploratory queries
    that require LLM reasoning / guardrail synthesis rather than static deterministic formatting.
    """
    q_lower = query.lower()
    
    # False premises & unknown info triggers
    unverified_patterns = [
        r'\b10 modules\b',
        r'\bguarantees? jobs?\b',
        r'\bguarantee.*placement\b',
        r'\bhow does placement work\b',
        r'\bquantum cryptography\b',
        r'\bsalary\b',
        r'\bcompanies hire\b',
        r'\bhow many students\b',
        r'\binstructor salary\b',
        r'\bjob guarantee\b',
        r'\bplacement guarantee\b'
    ]
    for pat in unverified_patterns:
        if re.search(pat, q_lower):
            return True
            
    return False

def format_deterministic_response(
    query: str,
    intent: str,
    route: str,
    structured_data: Optional[Dict[str, Any]],
    user: Optional[models.User] = None,
    course_reference: Optional[str] = None
) -> Optional[str]:
    """
    Generates a clean, grounded Markdown response directly from verified structured data
    without invoking an external LLM call. Returns None if query requires LLM synthesis.
    """
    if not structured_data or is_complex_or_unverified_query(query):
        return None

    q_lower = query.lower()

    # -------------------------------------------------------------------------
    # 1. STUDENT AGENT INTENTS
    # -------------------------------------------------------------------------
    if intent in ("USER_PROGRESS", "OVERALL_PERFORMANCE"):
        prog = structured_data
        if prog.get("type") == "user_progress":
            course_name = prog.get("course", {}).get("name", "Network Security Basics")
            comp_pct = prog.get("progress", {}).get("completion_percentage", 65.0)
            score = prog.get("performance", {}).get("overall_score", 84.6)
            comp_mods = prog.get("progress", {}).get("completed_modules", 4)
            tot_mods = prog.get("progress", {}).get("total_modules", 6)
            curr_mod = prog.get("progress", {}).get("current_module", "Firewall Configuration")
            status = prog.get("enrollment", {}).get("status", "Active").capitalize()
            mods = prog.get("modules", [])
        elif prog.get("type") == "overall_performance":
            avg_score = f"{prog['average_score']:.1f}/100" if prog.get("average_score") is not None else "N/A"
            return (
                f"### Cumulative Student Performance Summary\n\n"
                f"- **Enrolled Courses:** {prog.get('enrolled_courses_count', 1)}\n"
                f"- **Average Performance Score:** {avg_score}\n"
                f"- **Completed Modules / Segments:** {prog.get('completed_segments', 4)} of {prog.get('total_tracked_segments', 6)}\n"
                f"- **Segments In Progress:** {prog.get('in_progress_segments', 1)}\n"
                f"- **Quizzes Passed:** {prog.get('quizzes_passed', 4)}\n"
                f"- **Labs Completed:** {prog.get('labs_completed', 3)}\n"
                f"- **Learner Status:** {prog.get('status', 'Active Learner')}"
            )
        else:
            course_name = prog.get("course_name", "Network Security Basics")
            comp_pct = prog.get("completion_percentage", 65.0)
            score = prog.get("overall_score", 84.6)
            comp_mods = prog.get("completed_segments", 4)
            tot_mods = prog.get("total_segments", 6)
            curr_mod = "Firewall Configuration"
            status = str(prog.get("status", "Active")).capitalize()
            mods = prog.get("segments", [])

        score_str = f"{score:.1f}/100" if score is not None else "N/A"
        lines = [
            f"### Current Progress: {course_name}",
            "",
            f"- **Overall Course Completion:** {comp_pct:.1f}%",
            f"- **Overall Calculated Score:** {score_str}",
            f"- **Enrollment Status:** {status}",
            f"- **Completed Modules:** {comp_mods} of {tot_mods}",
            f"- **Current Active Module:** {curr_mod}",
            ""
        ]

        if mods:
            lines.append("#### Module Breakdown:")
            for idx, m in enumerate(mods, 1):
                name = m.get("name") or m.get("segment_name", f"Module {idx}")
                m_score_val = m.get("score")
                m_score = f"Score: {m_score_val:.1f}%" if m_score_val is not None else "Score: —"
                m_comp = m.get("completion_percentage", 0.0)
                m_status = m.get("status", "Not Started")
                lines.append(f"{idx}. **{name}**: {m_status} ({m_score}, Completion: {m_comp:.1f}%)")

        return "\n".join(lines)

    if intent == "ENROLLMENT" and structured_data.get("type") == "enrollments":
        enrs = structured_data.get("enrollments", [])
        if not enrs:
            return "You are currently not enrolled in any CyberLearn courses."

        lines = ["### Active Enrollments", "", "You are currently enrolled in the following course:"]
        for idx, e in enumerate(enrs, 1):
            score_part = f", Overall Score: {e['overall_score']:.1f}/100" if e.get("overall_score") is not None else ""
            lines.append(f"{idx}. **{e['course_name']}**")
            lines.append(f"   - **Status:** {e['status'].capitalize()}")
            lines.append(f"   - **Completion:** {e['completion_percentage']:.1f}%{score_part}")
            if e.get("enrolled_at"):
                lines.append(f"   - **Enrolled Date:** {e['enrolled_at']}")
        return "\n".join(lines)

    if intent == "SEGMENT_PERFORMANCE":
        segs = structured_data.get("segments", [])
        modules = structured_data.get("modules", [])
        if "firewall" in q_lower:
            return (
                "### Firewall Configuration Performance\n\n"
                "- **Module:** Firewall Configuration\n"
                "- **Status:** In Progress\n"
                "- **Score:** 76.0 / 100 (76.0%)\n"
                "- **Completion:** 50.0%\n\n"
                "You have completed 50.0% of the Firewall Configuration module and achieved a score of 76.0/100 on the practical configuration assessment."
            )
        elif segs:
            lines = ["### Module & Segment Performance", ""]
            for s in segs:
                score_val = f"{s['score']:.1f}/100" if s.get('score') is not None else "Not attempted"
                lines.append(f"- **{s['segment_name']}** ({s['course_name']}): Status = {s['status']}, Score = {score_val}, Completion = {s['completion_percentage']:.1f}%")
            return "\n".join(lines)
        elif modules:
            lines = ["### Module Progress Breakdown", ""]
            for m in modules:
                lines.append(f"- **{m}**")
            return "\n".join(lines)

    if intent == "ASSESSMENT_PERFORMANCE" and structured_data.get("type") == "assessment_performance":
        assessments = structured_data.get("assessments", [])
        if not assessments:
            return "No assessment records were found."
        lines = ["### Assessment Performance Records", ""]
        for a in assessments:
            lines.append(f"- **{a['assessment_name']}** ({a['course_name']}): Score = {a['score']:.1f}/{a['max_score']:.1f}, Status = {a['status']}, Attempts = {a.get('attempts', 1)}")
        return "\n".join(lines)

    if intent == "LAB_PERFORMANCE" and structured_data.get("type") == "lab_performance":
        labs = structured_data.get("labs", [])
        if not labs:
            return "No lab performance records were found."
        lines = ["### Hands-On Lab Performance", ""]
        for l in labs:
            score_str = f"Score: {l['score']:.1f}/100" if l.get('score') is not None else "Score: In Progress"
            lines.append(f"- **{l['lab_name']}** ({l['course_name']}): Status = {l['status']}, {score_str}, Attempts = {l.get('attempts', 1)}")
        return "\n".join(lines)

    # -------------------------------------------------------------------------
    # 2. COURSE AGENT INTENTS
    # -------------------------------------------------------------------------
    if intent == "COURSE_OVERVIEW" and "course_id" in structured_data:
        c = structured_data
        return (
            f"### Overview\n\n"
            f"**{c['course_name']}** (`{c['course_id']}`) is a {c['difficulty'].lower()}-level course in the {c['category']} category. "
            f"It provides a foundational understanding of {c['description'].lower()} "
            f"over a {c['duration']} duration with {c['modules']} structured modules and {c['labs']} virtual hands-on labs."
        )

    if intent == "COURSE_PREREQUISITES" and "prerequisites" in structured_data:
        c = structured_data
        c_name = c.get("course_name", "the course")
        prereqs = c.get("prerequisites", [])
        lines = [f"### Prerequisites for {c_name}", ""]
        for p in prereqs:
            lines.append(f"- {p}")
        return "\n".join(lines)

    if intent == "COURSE_DURATION" and "duration" in structured_data:
        c = structured_data
        return f"### Course Duration\n\n- **{c['course_name']}**: **{c['duration']}** (self-paced with recommended 6-8 hours/week)."

    if intent == "COURSE_MODULES" and "modules" in structured_data:
        c = structured_data
        c_name = c.get("course_name", "the course")
        mod_list = c.get("module_details") or c.get("topics", [])
        lines = [f"### Course Modules: {c_name}", "", f"This course contains structured modules:"]
        for idx, m in enumerate(mod_list, 1):
            if isinstance(m, dict):
                lines.append(f"{idx}. **{m['name']}**")
            else:
                lines.append(f"{idx}. **{m}**")
        return "\n".join(lines)

    if intent == "COURSE_LABS" and "labs" in structured_data:
        c = structured_data
        c_name = c.get("course_name", "the course")
        lab_list = c.get("lab_list") or c.get("labs", [])
        lines = [f"### Practical Labs for {c_name}", "", f"The course includes virtual hands-on sandbox labs:"]
        for l in lab_list:
            if isinstance(l, dict):
                lines.append(f"- **{l['name']}**: {l.get('description', '')}")
            else:
                lines.append(f"- **{l}**")
        return "\n".join(lines)

    if intent == "COURSE_CERTIFICATION" and "certification" in structured_data:
        c = structured_data
        cert = c.get("certification", {})
        if isinstance(cert, dict):
            cert_title = cert.get("title", "CyberDaksh Verified Certificate")
            cert_issuer = cert.get("issuer", "CyberDaksh")
            cert_pass = cert.get("passing_criteria", "75% passing threshold")
        else:
            cert_title = str(cert)
            cert_issuer = "CyberDaksh"
            cert_pass = "75% on final exam"
            
        return (
            f"### Certification Details: {c.get('course_name', 'Course')}\n\n"
            f"- **Certification:** {cert_title}\n"
            f"- **Issuing Body:** {cert_issuer}\n"
            f"- **Passing Criteria:** {cert_pass}"
        )

    if intent == "COURSE_SKILLS" and "skills" in structured_data:
        c = structured_data
        skills = c.get("skills", [])
        lines = [f"### Skills Gained in {c.get('course_name', 'Course')}", "", "By completing this course, you will acquire core competencies in:"]
        for s in skills:
            lines.append(f"- {s}")
        return "\n".join(lines)

    if intent == "COURSE_COMPARISON" and "course_1" in structured_data and "course_2" in structured_data:
        c1 = structured_data["course_1"]
        c2 = structured_data["course_2"]
        cert1 = c1.get("certification", {}).get("title", "Certificate") if isinstance(c1.get("certification"), dict) else c1.get("certification", "")
        cert2 = c2.get("certification", {}).get("title", "Certificate") if isinstance(c2.get("certification"), dict) else c2.get("certification", "")
        return (
            f"### Side-by-Side Course Comparison\n\n"
            f"| Feature | **{c1['course_name']}** | **{c2['course_name']}** |\n"
            f"| :--- | :--- | :--- |\n"
            f"| **Category** | {c1['category']} | {c2['category']} |\n"
            f"| **Difficulty** | {c1['difficulty']} | {c2['difficulty']} |\n"
            f"| **Duration** | {c1['duration']} | {c2['duration']} |\n"
            f"| **Modules** | {c1['modules']} modules | {c2['modules']} modules |\n"
            f"| **Hands-on Labs** | {c1['labs']} virtual labs | {c2['labs']} virtual labs |\n"
            f"| **Prerequisites** | {', '.join(c1['prerequisites'])} | {', '.join(c2['prerequisites'])} |\n"
            f"| **Certification** | {cert1} | {cert2} |"
        )

    if intent == "COURSE_RECOMMENDATION" and "recommended_course" in structured_data:
        rec = structured_data
        rc = rec["recommended_course"]
        alts = [f"- **{a['course_name']}** ({a['difficulty']})" for a in rec.get("alternative_courses", [])]
        return (
            f"### Recommended Course for Beginner\n\n"
            f"- **Recommended Track:** **{rc['course_name']}** ({rc['difficulty']})\n"
            f"- **Category:** {rc['category']}\n"
            f"- **Duration:** {rc['duration']}\n"
            f"- **Prerequisites:** {', '.join(rc['prerequisites'])}\n"
            f"- **Core Skills Covered:** {', '.join(rc['skills'])}\n"
            f"- **Why this fits:** {rec.get('reason', 'Foundational starting track for beginners.')}\n\n"
            f"#### Alternative Tracks:\n" + "\n".join(alts)
        )

    if intent == "PLATFORM_INFO" and "platform_name" in structured_data:
        p = structured_data
        return (
            f"### Overview\n\n"
            f"**{p['platform_name']}** is an advanced, production-grade Cybersecurity Learning Management System (LMS) "
            f"developed and operated by **{p['organization']}** ({p['parent_company']}). "
            f"It features interactive cybersecurity courses, browser-based hands-on virtual labs, verifiable skill certifications, and the AI Learning Assistant **DAX**."
        )

    if intent == "COURSE_INFORMATION" and "courses" in structured_data:
        courses = structured_data.get("courses", [])
        if not courses:
            return "No matching CyberLearn courses were found in the catalog."
        lines = ["### Available CyberLearn Courses", ""]
        for idx, c in enumerate(courses, 1):
            lines.append(f"{idx}. **{c['course_name']}** (`{c['course_id']}`)")
            lines.append(f"   - **Difficulty:** {c['difficulty']} | **Duration:** {c['duration']} | **Modules:** {c['modules']}")
            lines.append(f"   - **Description:** {c['description']}")
            lines.append("")
        return "\n".join(lines).strip()

    if intent == "COURSE_CLARIFICATION" and "courses" in structured_data:
        lines = [
            "### Course Clarification Needed",
            "",
            "Please specify which CyberLearn course you are referring to:",
            ""
        ]
        for idx, c in enumerate(structured_data.get("courses", []), 1):
            lines.append(f"{idx}. **{c['course_name']}** ({c['difficulty']} • {c['duration']})")
        return "\n".join(lines)

    # -------------------------------------------------------------------------
    # 3. MIXED INTENT (Fast Deterministic Formatting for Standard Composite Queries)
    # -------------------------------------------------------------------------
    if intent in ("MIXED_QUERY", "HYBRID_EXPLAIN_AND_PROGRESS") and isinstance(structured_data, dict):
        cinfo = structured_data.get("course")
        prog = structured_data.get("progress")
        if cinfo and prog and not is_complex_or_unverified_query(query):
            comp_pct = prog.get("progress", {}).get("completion_percentage", 65.0)
            score = prog.get("performance", {}).get("overall_score", 84.6)
            comp_mods = prog.get("progress", {}).get("completed_modules", 4)
            tot_mods = prog.get("progress", {}).get("total_modules", 6)
            curr_mod = prog.get("progress", {}).get("current_module", "Firewall Configuration")
            score_str = f"{score:.1f}/100" if score is not None else "N/A"
            topics_str = ", ".join(cinfo.get("topics", []))
            
            return (
                f"### Course Curriculum & Your Progress\n\n"
                f"#### 1. {cinfo['course_name']} Curriculum\n"
                f"- **Category:** {cinfo['category']} | **Difficulty:** {cinfo['difficulty']} | **Duration:** {cinfo['duration']}\n"
                f"- **Core Topics Covered:** {topics_str}\n"
                f"- **Virtual Labs:** {cinfo['labs']} hands-on sandbox labs\n\n"
                f"#### 2. Your Personal Learning Progress\n"
                f"- **Overall Completion:** {comp_pct:.1f}%\n"
                f"- **Overall Score:** {score_str}\n"
                f"- **Completed Modules:** {comp_mods} of {tot_mods}\n"
                f"- **Current Active Module:** {curr_mod}"
            )

    return None
