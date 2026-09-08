import os
import sys
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import models
from database import engine, Base
from auth_service import get_password_hash

def seed_database():
    """Repeatable, idempotent seed script for CyberLearn LMS demo data."""
    print("=" * 60, flush=True)
    print("Seeding CyberLearn LMS Demo Database...", flush=True)
    print("=" * 60, flush=True)

    # 1. Create all missing tables first
    Base.metadata.create_all(bind=engine)
    print("Schema synchronized.", flush=True)

    # 2. Safe column migrations for existing tables (one transaction per migration)
    migrations = [
        "ALTER TABLE users ADD COLUMN role VARCHAR DEFAULT 'student'",
        "ALTER TABLE users ADD COLUMN name VARCHAR",
        "ALTER TABLE users ADD COLUMN created_at DATETIME",
        "ALTER TABLE courses ADD COLUMN difficulty VARCHAR DEFAULT 'Beginner'",
        "ALTER TABLE courses ADD COLUMN total_segments INTEGER DEFAULT 10",
        "ALTER TABLE courses ADD COLUMN total_modules INTEGER DEFAULT 6",
        "ALTER TABLE enrollments ADD COLUMN completion_percentage FLOAT DEFAULT 0.0",
        "ALTER TABLE enrollments ADD COLUMN overall_score FLOAT",
        "ALTER TABLE enrollments ADD COLUMN last_accessed DATETIME",
        "ALTER TABLE user_progress ADD COLUMN total_modules INTEGER DEFAULT 6",
        "ALTER TABLE user_progress ADD COLUMN current_module VARCHAR",
    ]
    for m in migrations:
        try:
            with engine.begin() as conn:
                conn.execute(text(m))
        except Exception:
            pass

    with Session(engine) as db:
        # --- 3. Seed Users ---
        pwd_hash = get_password_hash("password123")
        users_to_seed = [
            {"email": "sachi@test.com", "name": "Sachi Prasad", "role": "student"},
            {"email": "student@cyberlearn.demo", "name": "Demo Student", "role": "student"},
            {"email": "student@cyberlearn.com", "name": "Alex Learner", "role": "student"},
            {"email": "student2@cyberlearn.demo", "name": "Jordan Smith", "role": "student"}
        ]

        seeded_users = {}
        for u in users_to_seed:
            user = db.query(models.User).filter(models.User.email == u["email"]).first()
            if not user:
                user = models.User(
                    email=u["email"],
                    name=u["name"],
                    role=u["role"],
                    hashed_password=pwd_hash,
                    created_at=datetime(2026, 8, 15, 10, 0)
                )
                db.add(user)
                db.commit()
                db.refresh(user)
            else:
                user.name = u["name"]
                user.role = u["role"]
                if not user.hashed_password:
                    user.hashed_password = pwd_hash
                db.commit()
            seeded_users[u["email"]] = user
        print(f"Users verified: {list(seeded_users.keys())}", flush=True)

        sachi_student = seeded_users["sachi@test.com"]
        primary_student = seeded_users["student@cyberlearn.demo"]
        alex_student = seeded_users["student@cyberlearn.com"]
        other_student = seeded_users["student2@cyberlearn.demo"]

        # --- 4. Seed Courses ---
        courses_data = [
            {
                "course_id": "course_network_sec",
                "title": "Network Security Basics",
                "category": "Defensive Security",
                "description": "Foundational network architecture, protocols, firewalls, and Wireshark packet analysis.",
                "difficulty": "Beginner",
                "total_segments": 10,
                "total_modules": 6,
                "total_labs": 3
            },
            {
                "course_id": "course_ethical_hack",
                "title": "Ethical Hacking Fundamentals",
                "category": "Offensive Security",
                "description": "Hands-on penetration testing, Nmap reconnaissance, Metasploit, and vulnerability assessment.",
                "difficulty": "Intermediate",
                "total_segments": 8,
                "total_modules": 8,
                "total_labs": 4
            },
            {
                "course_id": "course_web_security",
                "title": "Web Application Security",
                "category": "Application Security",
                "description": "OWASP Top 10 vulnerabilities, SQL Injection, XSS, CSRF, and Burp Suite analysis.",
                "difficulty": "Intermediate",
                "total_segments": 6,
                "total_modules": 6,
                "total_labs": 3
            }
        ]

        course_map = {}
        for c in courses_data:
            course = db.query(models.Course).filter(models.Course.course_id == c["course_id"]).first()
            if not course:
                course = models.Course(**c)
                db.add(course)
                db.commit()
                db.refresh(course)
            else:
                course.title = c["title"]
                course.description = c["description"]
                course.difficulty = c["difficulty"]
                course.total_segments = c["total_segments"]
                course.total_modules = c["total_modules"]
                db.commit()
            course_map[c["course_id"]] = course
        print("Courses verified.", flush=True)

        # --- 5. Seed Course Segments for Course 1 ---
        net_sec_segments = [
            (1, "Network Fundamentals", "Data transmission, topologies, OSI 7-layer model, and TCP/IP stack."),
            (2, "Network Threats", "Common vectors including eavesdropping, spoofing, Man-in-the-Middle, and DDoS."),
            (3, "Threat Detection", "Packet capture mechanisms, Wireshark filters, and anomalous traffic indicators."),
            (4, "Firewalls", "Stateful vs stateless inspection, packet filtering, DMZ concepts, and ACL rule sets."),
            (5, "Intrusion Detection Systems", "Signature-based and anomaly-based IDS/IPS, and Snort rule construction."),
            (6, "Secure Network Architecture", "Zero trust design principles, network segmentation, and VLAN isolation."),
            (7, "VPN and Encryption", "IPsec, TLS/SSL, tunneling protocols, and asymmetric/symmetric cryptography."),
            (8, "Network Monitoring", "SIEM integration, syslog aggregation, NetFlow telemetry, and baseline monitoring."),
            (9, "Security Assessment", "Vulnerability scanning, port auditing, and network configuration auditing."),
            (10, "Final Security Assessment", "Comprehensive end-of-course capstone assessment and hardening practical.")
        ]

        seg_map_net_sec = {}
        for num, name, desc in net_sec_segments:
            seg = db.query(models.CourseSegment).filter(
                models.CourseSegment.course_id == "course_network_sec",
                models.CourseSegment.segment_number == num
            ).first()
            if not seg:
                seg = models.CourseSegment(
                    course_id="course_network_sec",
                    segment_number=num,
                    segment_name=name,
                    description=desc
                )
                db.add(seg)
                db.commit()
                db.refresh(seg)
            else:
                seg.segment_name = name
                seg.description = desc
            seg_map_net_sec[num] = seg

        # --- 6. Seed Course Segments for Course 2 ---
        ethical_hack_segments = [
            (1, "Ethical Hacking Overview & Legal Framework", "Rules of engagement, scope definition, and ethics."),
            (2, "Reconnaissance & Footprinting", "Passive reconnaissance, OSINT gathering, whois, and DNS enumeration."),
            (3, "Network Scanning with Nmap", "Host discovery, SYN/TCP connect scans, and OS/service fingerprinting."),
            (4, "Vulnerability Assessment", "Identifying misconfigurations and CVSS vulnerability scoring."),
            (5, "Metasploit Exploitation", "Payload selection, auxiliary modules, and meterpreter sessions."),
            (6, "Password Cracking & Authentication", "Hash identification, brute-force attacks, and credential auditing."),
            (7, "Web Application Penetration Testing", "SQL injection, XSS, CSRF, and Burp Suite request tampering."),
            (8, "Final Penetration Testing Capstone", "Multi-stage CTF lab challenge and penetration testing report.")
        ]

        seg_map_ethical = {}
        for num, name, desc in ethical_hack_segments:
            seg = db.query(models.CourseSegment).filter(
                models.CourseSegment.course_id == "course_ethical_hack",
                models.CourseSegment.segment_number == num
            ).first()
            if not seg:
                seg = models.CourseSegment(
                    course_id="course_ethical_hack",
                    segment_number=num,
                    segment_name=name,
                    description=desc
                )
                db.add(seg)
                db.commit()
                db.refresh(seg)
            else:
                seg.segment_name = name
                seg.description = desc
            seg_map_ethical[num] = seg

        db.commit()
        print("Course segments verified.", flush=True)

        # --- 7. Seed Sachi Prasad Specific Demo Data ---
        print("Seeding demo student: Sachi Prasad (sachi@test.com)...", flush=True)
        s_id = sachi_student.id

        # Enrollment
        enr_sachi = db.query(models.Enrollment).filter(
            models.Enrollment.user_id == s_id,
            models.Enrollment.course_id == "course_network_sec"
        ).first()
        if not enr_sachi:
            enr_sachi = models.Enrollment(
                user_id=s_id,
                course_id="course_network_sec",
                status="active",
                enrolled_at=datetime(2026, 8, 16, 9, 0),
                completion_percentage=65.0,
                overall_score=84.6,
                last_accessed=datetime(2026, 9, 2, 14, 30)
            )
            db.add(enr_sachi)
        else:
            enr_sachi.status = "active"
            enr_sachi.completion_percentage = 65.0
            enr_sachi.overall_score = 84.6
            enr_sachi.last_accessed = datetime(2026, 9, 2, 14, 30)
        db.commit()

        # CourseProgress
        cp_sachi = db.query(models.CourseProgress).filter(
            models.CourseProgress.user_id == s_id,
            models.CourseProgress.course_id == "course_network_sec"
        ).first()
        if not cp_sachi:
            cp_sachi = models.CourseProgress(
                user_id=s_id,
                course_id="course_network_sec",
                completion_percentage=65.0,
                completed_modules=4,
                total_modules=6,
                current_module="Firewall Configuration",
                last_activity=datetime(2026, 9, 2, 14, 30)
            )
            db.add(cp_sachi)
        else:
            cp_sachi.completion_percentage = 65.0
            cp_sachi.completed_modules = 4
            cp_sachi.total_modules = 6
            cp_sachi.current_module = "Firewall Configuration"
            cp_sachi.last_activity = datetime(2026, 9, 2, 14, 30)
        db.commit()

        # UserProgress (backward compatibility)
        up_sachi = db.query(models.UserProgress).filter(
            models.UserProgress.user_id == s_id,
            models.UserProgress.course_id == "course_network_sec"
        ).first()
        if not up_sachi:
            up_sachi = models.UserProgress(
                user_id=s_id,
                course_id="course_network_sec",
                completed_modules=4,
                total_modules=6,
                current_module="Firewall Configuration",
                completed_labs=2,
                assessment_score=84.6,
                completion_percentage=65.0,
                last_activity=datetime(2026, 9, 2, 14, 30)
            )
            db.add(up_sachi)
        else:
            up_sachi.completed_modules = 4
            up_sachi.total_modules = 6
            up_sachi.current_module = "Firewall Configuration"
            up_sachi.completed_labs = 2
            up_sachi.assessment_score = 84.6
            up_sachi.completion_percentage = 65.0
            up_sachi.last_activity = datetime(2026, 9, 2, 14, 30)
        db.commit()

        # ModuleProgress (6 modules for Network Security Basics)
        sachi_modules = [
            ("Network Fundamentals & Architecture", "Completed", 100.0, 92.0, datetime(2026, 8, 20, 11, 30)),
            ("Network Threats & Vulnerabilities", "Completed", 100.0, 88.0, datetime(2026, 8, 23, 15, 45)),
            ("Packet Analysis with Wireshark", "Completed", 100.0, 85.0, datetime(2026, 8, 26, 14, 10)),
            ("Cryptography & Protocols", "Completed", 100.0, 82.0, datetime(2026, 8, 29, 16, 20)),
            ("Firewall Configuration", "In Progress", 50.0, 76.0, None),
            ("Intrusion Detection Systems & Capstone", "Not Started", 0.0, None, None),
        ]

        for mod_name, mod_status, comp_pct, score, comp_date in sachi_modules:
            mp = db.query(models.ModuleProgress).filter(
                models.ModuleProgress.user_id == s_id,
                models.ModuleProgress.course_id == "course_network_sec",
                models.ModuleProgress.module_name == mod_name
            ).first()
            if not mp:
                mp = models.ModuleProgress(
                    user_id=s_id,
                    course_id="course_network_sec",
                    module_name=mod_name,
                    module_status=mod_status,
                    completion_percentage=comp_pct,
                    score=score,
                    completed_at=comp_date,
                    last_activity=comp_date or datetime(2026, 9, 2, 14, 30)
                )
                db.add(mp)
            else:
                mp.module_status = mod_status
                mp.completion_percentage = comp_pct
                mp.score = score
                mp.completed_at = comp_date
                mp.last_activity = comp_date or datetime(2026, 9, 2, 14, 30)
        db.commit()

        # Seed Segment performances for Sachi (10 segments)
        sachi_seg_specs = [
            (1, "Completed", 92.0, 100.0, 1, datetime(2026, 8, 20)),
            (2, "Completed", 88.0, 100.0, 2, datetime(2026, 8, 23)),
            (3, "Completed", 85.0, 100.0, 1, datetime(2026, 8, 26)),
            (4, "Completed", 82.0, 100.0, 1, datetime(2026, 8, 29)),
            (5, "In Progress", 76.0, 60.0, 2, datetime(2026, 9, 1)),
            (6, "In Progress", 70.0, 30.0, 1, datetime(2026, 9, 2)),
            (7, "Not Started", None, 0.0, 0, None),
            (8, "Not Started", None, 0.0, 0, None),
            (9, "Not Started", None, 0.0, 0, None),
            (10, "Not Started", None, 0.0, 0, None),
        ]
        for seg_num, status, score, comp, atts, comp_date in sachi_seg_specs:
            seg_obj = seg_map_net_sec[seg_num]
            perf = db.query(models.StudentSegmentPerformance).filter(
                models.StudentSegmentPerformance.user_id == s_id,
                models.StudentSegmentPerformance.course_id == "course_network_sec",
                models.StudentSegmentPerformance.segment_id == seg_obj.id
            ).first()
            if not perf:
                perf = models.StudentSegmentPerformance(
                    user_id=s_id,
                    course_id="course_network_sec",
                    segment_id=seg_obj.id,
                    status=status,
                    score=score,
                    max_score=100.0,
                    completion_percentage=comp,
                    attempts=atts,
                    completed_at=comp_date,
                    last_accessed=comp_date or datetime(2026, 9, 2)
                )
                db.add(perf)
            else:
                perf.status = status
                perf.score = score
                perf.completion_percentage = comp
                perf.attempts = atts
                perf.completed_at = comp_date
        db.commit()

        # Seed Assessments for Sachi
        sachi_assessments = [
            ("Network Fundamentals Quiz", 1, "quiz", 92.0, 100.0, "Passed", datetime(2026, 8, 20)),
            ("Network Threats Assessment", 2, "quiz", 88.0, 100.0, "Passed", datetime(2026, 8, 23)),
            ("Wireshark Packet Analysis Practical", 3, "assignment", 85.0, 100.0, "Passed", datetime(2026, 8, 26)),
            ("Cryptography & Protocols Quiz", 4, "quiz", 82.0, 100.0, "Passed", datetime(2026, 8, 29)),
            ("Firewall Configuration Assessment", 4, "quiz", 76.0, 100.0, "In Progress", datetime(2026, 9, 1)),
            ("Comprehensive Network Security Final Exam", 10, "exam", 0.0, 100.0, "Not Started", None)
        ]

        for a_name, seg_num, a_type, score, max_score, status, sub_date in sachi_assessments:
            seg_id = seg_map_net_sec[seg_num].id
            assessment = db.query(models.Assessment).filter(
                models.Assessment.course_id == "course_network_sec",
                models.Assessment.assessment_name == a_name
            ).first()
            if not assessment:
                assessment = models.Assessment(
                    course_id="course_network_sec",
                    segment_id=seg_id,
                    assessment_name=a_name,
                    assessment_type=a_type,
                    max_score=max_score
                )
                db.add(assessment)
                db.commit()
                db.refresh(assessment)

            sa = db.query(models.StudentAssessment).filter(
                models.StudentAssessment.user_id == s_id,
                models.StudentAssessment.assessment_id == assessment.id
            ).first()
            if not sa:
                sa = models.StudentAssessment(
                    user_id=s_id,
                    course_id="course_network_sec",
                    assessment_id=assessment.id,
                    assessment_name=a_name,
                    score=score,
                    attempts=1 if score > 0 else 0,
                    status=status,
                    submitted_at=sub_date
                )
                db.add(sa)
            else:
                sa.score = score
                sa.status = status
                sa.course_id = "course_network_sec"
                sa.assessment_name = a_name
                sa.submitted_at = sub_date
        db.commit()
        print("Sachi Prasad demo data seeded successfully.", flush=True)

        # --- 8. Seed Other Demo Students (for compatibility & benchmarks) ---
        def seed_student_data(student_user):
            st_id = student_user.id

            net_perf_specs = [
                (1, "Completed", 92.0, 100.0, 1, datetime(2026, 8, 20)),
                (2, "Completed", 86.0, 100.0, 2, datetime(2026, 8, 23)),
                (3, "Completed", 85.0, 100.0, 1, datetime(2026, 8, 26)),
                (4, "In Progress", 74.0, 80.0, 2, datetime(2026, 8, 29)),
                (5, "In Progress", 78.0, 70.0, 2, datetime(2026, 8, 31)),
                (6, "In Progress", 81.0, 50.0, 1, datetime(2026, 9, 1)),
                (7, "Not Started", None, 0.0, 0, None),
                (8, "Not Started", None, 0.0, 0, None),
                (9, "Not Started", None, 0.0, 0, None),
                (10, "Not Started", None, 0.0, 0, None),
            ]

            total_comp_sum = sum(p[3] for p in net_perf_specs)
            overall_net_comp = round(total_comp_sum / len(net_perf_specs), 1)
            scored_vals = [p[2] for p in net_perf_specs if p[2] is not None]
            overall_net_score = round(sum(scored_vals) / len(scored_vals), 1) if scored_vals else 0.0

            enr1 = db.query(models.Enrollment).filter(
                models.Enrollment.user_id == st_id,
                models.Enrollment.course_id == "course_network_sec"
            ).first()
            if not enr1:
                enr1 = models.Enrollment(
                    user_id=st_id,
                    course_id="course_network_sec",
                    status="active",
                    enrolled_at=datetime(2026, 8, 16, 9, 0),
                    completion_percentage=overall_net_comp,
                    overall_score=overall_net_score,
                    last_accessed=datetime(2026, 9, 1, 14, 30)
                )
                db.add(enr1)
            else:
                enr1.completion_percentage = overall_net_comp
                enr1.overall_score = overall_net_score
                enr1.last_accessed = datetime(2026, 9, 1, 14, 30)

            for seg_num, status, score, comp, atts, comp_date in net_perf_specs:
                seg_obj = seg_map_net_sec[seg_num]
                perf = db.query(models.StudentSegmentPerformance).filter(
                    models.StudentSegmentPerformance.user_id == st_id,
                    models.StudentSegmentPerformance.course_id == "course_network_sec",
                    models.StudentSegmentPerformance.segment_id == seg_obj.id
                ).first()
                if not perf:
                    perf = models.StudentSegmentPerformance(
                        user_id=st_id,
                        course_id="course_network_sec",
                        segment_id=seg_obj.id,
                        status=status,
                        score=score,
                        max_score=100.0,
                        completion_percentage=comp,
                        attempts=atts,
                        completed_at=comp_date,
                        last_accessed=comp_date or datetime(2026, 8, 16)
                    )
                    db.add(perf)
                else:
                    perf.status = status
                    perf.score = score
                    perf.completion_percentage = comp
                    perf.attempts = atts
                    perf.completed_at = comp_date

            eth_perf_specs = [
                (1, "Completed", 95.0, 100.0, 1, datetime(2026, 8, 22)),
                (2, "Completed", 90.0, 100.0, 1, datetime(2026, 8, 25)),
                (3, "In Progress", 78.0, 60.0, 1, datetime(2026, 8, 28)),
                (4, "In Progress", 72.0, 40.0, 1, datetime(2026, 8, 30)),
                (5, "Not Started", None, 0.0, 0, None),
                (6, "Not Started", None, 0.0, 0, None),
                (7, "Not Started", None, 0.0, 0, None),
                (8, "Not Started", None, 0.0, 0, None),
            ]

            total_eth_comp = sum(p[3] for p in eth_perf_specs)
            overall_eth_comp = round(total_eth_comp / len(eth_perf_specs), 1)
            eth_scores = [p[2] for p in eth_perf_specs if p[2] is not None]
            overall_eth_score = round(sum(eth_scores) / len(eth_scores), 1) if eth_scores else 0.0

            enr2 = db.query(models.Enrollment).filter(
                models.Enrollment.user_id == st_id,
                models.Enrollment.course_id == "course_ethical_hack"
            ).first()
            if not enr2:
                enr2 = models.Enrollment(
                    user_id=st_id,
                    course_id="course_ethical_hack",
                    status="active",
                    enrolled_at=datetime(2026, 8, 18, 11, 0),
                    completion_percentage=overall_eth_comp,
                    overall_score=overall_eth_score,
                    last_accessed=datetime(2026, 8, 30, 16, 15)
                )
                db.add(enr2)
            else:
                enr2.completion_percentage = overall_eth_comp
                enr2.overall_score = overall_eth_score
                enr2.last_accessed = datetime(2026, 8, 30, 16, 15)

            for seg_num, status, score, comp, atts, comp_date in eth_perf_specs:
                seg_obj = seg_map_ethical[seg_num]
                perf = db.query(models.StudentSegmentPerformance).filter(
                    models.StudentSegmentPerformance.user_id == st_id,
                    models.StudentSegmentPerformance.course_id == "course_ethical_hack",
                    models.StudentSegmentPerformance.segment_id == seg_obj.id
                ).first()
                if not perf:
                    perf = models.StudentSegmentPerformance(
                        user_id=st_id,
                        course_id="course_ethical_hack",
                        segment_id=seg_obj.id,
                        status=status,
                        score=score,
                        max_score=100.0,
                        completion_percentage=comp,
                        attempts=atts,
                        completed_at=comp_date,
                        last_accessed=comp_date or datetime(2026, 8, 18)
                    )
                    db.add(perf)
                else:
                    perf.status = status
                    perf.score = score
                    perf.completion_percentage = comp
                    perf.attempts = atts
                    perf.completed_at = comp_date

            up1 = db.query(models.UserProgress).filter(
                models.UserProgress.user_id == st_id,
                models.UserProgress.course_id == "course_network_sec"
            ).first()
            if not up1:
                up1 = models.UserProgress(
                    user_id=st_id,
                    course_id="course_network_sec",
                    completed_modules=3,
                    total_modules=6,
                    current_module="Firewalls",
                    completed_labs=1,
                    assessment_score=overall_net_score,
                    completion_percentage=overall_net_comp,
                    last_activity=datetime(2026, 9, 1, 14, 30)
                )
                db.add(up1)
            else:
                up1.completed_modules = 3
                up1.total_modules = 6
                up1.current_module = "Firewalls"
                up1.completed_labs = 1
                up1.assessment_score = overall_net_score
                up1.completion_percentage = overall_net_comp

        seed_student_data(primary_student)
        seed_student_data(alex_student)
        db.commit()

        # Other student for IDOR testing
        enr_other = db.query(models.Enrollment).filter(
            models.Enrollment.user_id == other_student.id,
            models.Enrollment.course_id == "course_web_security"
        ).first()
        if not enr_other:
            enr_other = models.Enrollment(
                user_id=other_student.id,
                course_id="course_web_security",
                status="active",
                enrolled_at=datetime(2026, 8, 25, 9, 0),
                completion_percentage=15.0,
                overall_score=70.0,
                last_accessed=datetime(2026, 8, 29, 10, 0)
            )
            db.add(enr_other)
            db.commit()

        # General assessments
        assessments_data = [
            ("course_network_sec", 1, "Network Fundamentals Quiz", "quiz", 100.0, 92.0, 1, "Passed"),
            ("course_network_sec", 2, "Network Threats Assessment", "quiz", 100.0, 86.0, 2, "Passed"),
            ("course_network_sec", 3, "Threat Detection Quiz", "quiz", 100.0, 85.0, 1, "Passed"),
            ("course_network_sec", 4, "Firewall Rules & ACL Quiz", "quiz", 100.0, 74.0, 2, "In Progress"),
            ("course_network_sec", 5, "IDS & IPS Concepts Quiz", "quiz", 100.0, 78.0, 2, "In Progress"),
            ("course_network_sec", 6, "DMZ & Subnetting Quiz", "quiz", 100.0, 81.0, 1, "In Progress"),
            ("course_network_sec", 10, "Final Security Assessment Comprehensive Exam", "exam", 100.0, None, 0, "Not Started"),
            ("course_ethical_hack", 1, "Legal & Ethical Standards Quiz", "quiz", 100.0, 95.0, 1, "Passed"),
            ("course_ethical_hack", 2, "OSINT & Passive Recon Quiz", "quiz", 100.0, 90.0, 1, "Passed"),
            ("course_ethical_hack", 3, "Nmap Flags & Scripting Engine Quiz", "quiz", 100.0, 78.0, 1, "In Progress"),
            ("course_ethical_hack", 4, "CVSS Scoring & Vulnerability Analysis Quiz", "quiz", 100.0, 72.0, 1, "In Progress"),
        ]

        for cid, seg_num, a_name, a_type, max_s, s_score, atts, s_status in assessments_data:
            seg_id = seg_map_net_sec[seg_num].id if cid == "course_network_sec" else seg_map_ethical[seg_num].id
            assessment = db.query(models.Assessment).filter(
                models.Assessment.course_id == cid,
                models.Assessment.assessment_name == a_name
            ).first()
            if not assessment:
                assessment = models.Assessment(
                    course_id=cid,
                    segment_id=seg_id,
                    assessment_name=a_name,
                    assessment_type=a_type,
                    max_score=max_s
                )
                db.add(assessment)
                db.commit()
                db.refresh(assessment)

            if s_score is not None:
                for target_user in [primary_student, alex_student]:
                    s_res = db.query(models.StudentAssessment).filter(
                        models.StudentAssessment.user_id == target_user.id,
                        models.StudentAssessment.assessment_id == assessment.id
                    ).first()
                    if not s_res:
                        s_res = models.StudentAssessment(
                            user_id=target_user.id,
                            course_id=cid,
                            assessment_id=assessment.id,
                            assessment_name=a_name,
                            score=s_score,
                            attempts=atts,
                            status=s_status,
                            submitted_at=datetime(2026, 8, 25)
                        )
                        db.add(s_res)
                    else:
                        s_res.score = s_score
                        s_res.attempts = atts
                        s_res.status = s_status
                        s_res.course_id = cid
                        s_res.assessment_name = a_name
        db.commit()

        # Seed Lab Performances
        labs_data = [
            ("course_network_sec", 3, "Wireshark Packet Analysis Lab", "Completed", 90.0, 1, datetime(2026, 8, 26)),
            ("course_network_sec", 4, "Virtual Firewall Configuration Lab", "In Progress", 75.0, 2, datetime(2026, 8, 29)),
            ("course_network_sec", 5, "Snort IDS Rule Deployment Lab", "In Progress", 70.0, 1, datetime(2026, 8, 31)),
            ("course_ethical_hack", 2, "Passive Reconnaissance Lab", "Completed", 92.0, 1, datetime(2026, 8, 25)),
            ("course_ethical_hack", 3, "Nmap Port Scanning Lab", "In Progress", 78.0, 1, datetime(2026, 8, 28)),
        ]

        for cid, seg_num, lab_name, status, score, atts, comp_date in labs_data:
            seg_id = seg_map_net_sec[seg_num].id if cid == "course_network_sec" else seg_map_ethical[seg_num].id
            for target_user in [sachi_student, primary_student, alex_student]:
                lab_perf = db.query(models.StudentLabPerformance).filter(
                    models.StudentLabPerformance.user_id == target_user.id,
                    models.StudentLabPerformance.course_id == cid,
                    models.StudentLabPerformance.lab_name == lab_name
                ).first()
                if not lab_perf:
                    lab_perf = models.StudentLabPerformance(
                        user_id=target_user.id,
                        course_id=cid,
                        segment_id=seg_id,
                        lab_name=lab_name,
                        status=status,
                        score=score,
                        attempts=atts,
                        completed_at=comp_date
                    )
                    db.add(lab_perf)
                else:
                    lab_perf.status = status
                    lab_perf.score = score
                    lab_perf.attempts = atts
                    lab_perf.completed_at = comp_date
        db.commit()

        print("=" * 60, flush=True)
        print("CyberLearn LMS Demo Database Seeding Completed Successfully!", flush=True)
        print("=" * 60, flush=True)

if __name__ == "__main__":
    seed_database()
