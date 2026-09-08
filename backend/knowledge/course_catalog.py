from typing import List, Dict, Any, Optional
import re

# Verified CyberLearn LMS Course Catalog
# Sourced from official CyberLearn curriculum, database models, and knowledge base
COURSE_CATALOG: Dict[str, Dict[str, Any]] = {
    "course_network_sec": {
        "course_id": "course_network_sec",
        "course_name": "Network Security Basics",
        "aliases": ["network security", "network sec", "netsec", "networking basics", "network security basics", "network security fundamentals"],
        "description": "Foundational network architecture, protocols, firewalls, and Wireshark packet analysis.",
        "category": "Defensive Security",
        "difficulty": "Beginner",
        "duration": "6 weeks",
        "prerequisites": [
            "Basic computer and internet literacy; no prior security experience required"
        ],
        "total_modules": 6,
        "total_segments": 10,
        "total_labs": 3,
        "skills": [
            "Network Security",
            "Wireshark",
            "Firewalls",
            "Threat Detection",
            "Packet Analysis",
            "TCP/IP & OSI",
            "DMZ Architecture",
            "VPN & Encryption"
        ],
        "module_names": [
            "Module 1: OSI & TCP/IP Reference Models",
            "Module 2: Firewall Configuration & Access Control Lists",
            "Module 3: Network Packet Analysis with Wireshark",
            "Module 4: Defensive Perimeter Security & DMZ Architecture",
            "Module 5: Intrusion Detection & Network Monitoring",
            "Module 6: Capstone Security Assessment & Incident Response"
        ],
        "module_details": [
            {
                "module_number": 1,
                "name": "OSI & TCP/IP Reference Models",
                "description": "7 layers of the OSI model, 4 layers of TCP/IP, packet encapsulation/decapsulation, protocol data units (PDUs), port addressing (TCP/UDP), IP routing, and core protocols (HTTP/S, DNS, ARP, ICMP, SSH).",
                "topics": ["OSI 7 Layers", "TCP/IP Stack", "Encapsulation", "TCP vs UDP", "DNS & ARP Operations"]
            },
            {
                "module_number": 2,
                "name": "Firewall Configuration & Access Control Lists",
                "description": "Firewall architectures, stateful vs stateless packet filtering, connection state tracking, Access Control Lists (ACLs) rules, and Next-Generation Firewalls (NGFW) with Deep Packet Inspection (DPI).",
                "topics": ["Stateful Packet Inspection", "ACL Rule Synthesis", "NGFW Capabilities", "Deep Packet Inspection"]
            },
            {
                "module_number": 3,
                "name": "Network Packet Analysis with Wireshark",
                "description": "Live traffic capture in browser sandboxes, protocol header decoding, display filter syntax, and identifying anomalies (SYN floods, ARP spoofing, cleartext credentials).",
                "topics": ["Live Packet Capture", "Wireshark Display Filters", "SYN Flood Detection", "ARP Spoofing Identification"]
            },
            {
                "module_number": 4,
                "name": "Defensive Perimeter Security & DMZ Architecture",
                "description": "Demilitarized Zone (DMZ) design for public servers, subnet isolation, IDS/IPS integration, IPsec/OpenVPN virtual private networks, and secure gateway routing.",
                "topics": ["DMZ Network Isolation", "IDS/IPS Deployment", "IPsec & OpenVPN", "Secure Gateway Routing"]
            },
            {
                "module_number": 5,
                "name": "Intrusion Detection & Network Monitoring",
                "description": "Signature-based and anomaly-based detection using Snort and Suricata, rule writing, alert management, and network security monitoring.",
                "topics": ["Snort Rule Writing", "Suricata Alert Tuning", "Network Telemetry", "Signature vs Anomaly Detection"]
            },
            {
                "module_number": 6,
                "name": "Capstone Security Assessment & Incident Response",
                "description": "End-to-end practical assessment simulating enterprise network breach analysis, log correlation, perimeter defense hardening, and incident response reporting.",
                "topics": ["Breach Investigation", "Log Correlation", "Perimeter Hardening", "Incident Response Reporting"]
            }
        ],
        "topics": [
            "Module 1: OSI & TCP/IP Reference Models (7 layers, encapsulation, routing, protocols)",
            "Module 2: Firewall Configuration & Access Control Lists (Stateful/Stateless filtering, NGFW, DPI)",
            "Module 3: Network Packet Analysis with Wireshark (Traffic capture, display filters, anomaly detection)",
            "Module 4: Defensive Perimeter Security & DMZ Architecture (DMZ isolation, IDS/IPS, VPNs)",
            "Module 5: Intrusion Detection & Network Monitoring (Snort, Suricata, log analysis)",
            "Module 6: Capstone Security Assessment & Incident Response"
        ],
        "labs": [
            "Wireshark Packet Analysis Sandbox Lab",
            "Virtual Firewall & ACL Configuration Lab",
            "Snort IDS Rule Deployment Lab"
        ],
        "certification": "CyberLearn Verified Certificate of Completion from CyberDaksh (Requires 100% module completion, all labs, and >=75% on final assessment)",
        "course_status": "Active",
        "learning_objectives": [
            "Master OSI and TCP/IP architectural models and protocol encapsulation",
            "Configure stateless and stateful firewall ACLs to protect enterprise perimeters",
            "Capture and decode live network packets using Wireshark to detect cyber threats",
            "Design secure DMZ network perimeters and deploy Snort intrusion detection rules"
        ]
    },
    "course_ethical_hack": {
        "course_id": "course_ethical_hack",
        "course_name": "Ethical Hacking & Penetration Testing",
        "aliases": ["ethical hacking", "penetration testing", "pentest", "pentesting", "offensive security", "ethical hacking fundamentals"],
        "description": "Hands-on offensive cybersecurity training covering penetration testing methodologies, vulnerability discovery, reconnaissance, and exploitation frameworks.",
        "category": "Offensive Security",
        "difficulty": "Intermediate",
        "duration": "8 weeks",
        "prerequisites": [
            "Network Security Basics or equivalent networking and Linux command-line fundamentals"
        ],
        "total_modules": 8,
        "total_segments": 8,
        "total_labs": 4,
        "skills": [
            "Ethical Hacking",
            "Penetration Testing",
            "Nmap",
            "Metasploit",
            "Reconnaissance & OSINT",
            "Vulnerability Assessment",
            "Privilege Escalation",
            "Kali Linux Tools"
        ],
        "module_names": [
            "Module 1: Reconnaissance & Footprinting",
            "Module 2: System Exploitation & Metasploit Framework",
            "Module 3: Network Scanning & Host Discovery with Nmap",
            "Module 4: Vulnerability Assessment & CVSS Scoring with OpenVAS",
            "Module 5: Password Cracking & Authentication Attacks",
            "Module 6: Web & Service Exploitation Techniques",
            "Module 7: Privilege Escalation",
            "Module 8: Professional Penetration Testing Reporting & Capstone CTF"
        ],
        "module_details": [
            {
                "module_number": 1,
                "name": "Reconnaissance & Footprinting",
                "description": "Passive and active reconnaissance, OSINT gathering, WHOIS lookups, DNS enumeration, search engine dorking, and certificate transparency logs.",
                "topics": ["OSINT Gathering", "WHOIS & DNS Enumeration", "Search Engine Dorking", "Certificate Logs"]
            },
            {
                "module_number": 2,
                "name": "System Exploitation & Metasploit Framework",
                "description": "Metasploit exploit modules, auxiliary scanners, Meterpreter payloads, handlers, buffer overflows, and remote code execution concepts.",
                "topics": ["Metasploit Framework", "Meterpreter Payloads", "Buffer Overflows", "Remote Code Execution"]
            },
            {
                "module_number": 3,
                "name": "Network Scanning & Host Discovery with Nmap",
                "description": "Nmap scanning techniques (SYN, ACK, UDP, Idle scans), OS fingerprinting, service version detection, and NSE script automation.",
                "topics": ["SYN & UDP Scanning", "OS Fingerprinting", "NSE Script Automation", "Service Version Detection"]
            },
            {
                "module_number": 4,
                "name": "Vulnerability Assessment & CVSS Scoring with OpenVAS",
                "description": "Automated vulnerability scanning, vulnerability triage, false positive elimination, and CVSS v3.1 severity rating calculation.",
                "topics": ["OpenVAS Scanner", "Vulnerability Triage", "CVSS v3.1 Scoring", "Risk Prioritization"]
            },
            {
                "module_number": 5,
                "name": "Password Cracking & Authentication Attacks",
                "description": "Online and offline password cracking with Hydra and John the Ripper, password spraying, rainbow tables, and authentication bypasses.",
                "topics": ["Hydra Online Attacks", "John the Ripper Hash Cracking", "Password Spraying", "MFA Bypasses"]
            },
            {
                "module_number": 6,
                "name": "Web & Service Exploitation Techniques",
                "description": "Attacking network services (SMB, SSH, FTP, RDP), default credential exploitation, and service misconfiguration chaining.",
                "topics": ["SMB & SSH Attacks", "Default Credentials", "Service Exploits", "Misconfiguration Chaining"]
            },
            {
                "module_number": 7,
                "name": "Privilege Escalation",
                "description": "Linux privilege escalation (sudo rights, SUID binaries, cron jobs) and Windows privilege escalation (token manipulation, DLL hijacking, unquoted service paths).",
                "topics": ["Linux SUID & Sudo Escalation", "Windows Token Manipulation", "DLL Hijacking", "Kernel Exploits"]
            },
            {
                "module_number": 8,
                "name": "Professional Penetration Testing Reporting & Capstone CTF",
                "description": "Writing enterprise penetration test executive summaries and technical remediation reports, followed by a multi-stage Capture-the-Flag (CTF) practical exam.",
                "topics": ["Executive Reporting", "Remediation Roadmaps", "Multi-stage CTF Challenge", "Ethics & Rules of Engagement"]
            }
        ],
        "topics": [
            "Module 1: Reconnaissance & Footprinting (OSINT, WHOIS, DNS enumeration, search engine dorking)",
            "Module 2: System Exploitation & Metasploit Framework (Exploits, Meterpreter payloads, post-exploitation)",
            "Module 3: Network Scanning & Host Discovery with Nmap",
            "Module 4: Vulnerability Assessment & CVSS Scoring with OpenVAS",
            "Module 5: Password Cracking & Authentication Attacks (Hydra, John the Ripper)",
            "Module 6: Web & Service Exploitation Techniques",
            "Module 7: Privilege Escalation (Linux sudo/SUID, Windows token manipulation)",
            "Module 8: Professional Penetration Testing Reporting & Capstone CTF"
        ],
        "labs": [
            "Passive Reconnaissance & OSINT Lab",
            "Nmap Network Scanning & Fingerprinting Lab",
            "Metasploit Exploitation Sandbox Lab",
            "Multi-stage CTF Penetration Testing Challenge"
        ],
        "certification": "CyberLearn Verified Certificate of Completion from CyberDaksh (Eligible for CyberDaksh Security Engineering Internship with >=85% overall average)",
        "course_status": "Active",
        "learning_objectives": [
            "Conduct structured passive and active reconnaissance against target infrastructure",
            "Execute vulnerability assessments and score risk using the CVSS framework",
            "Perform controlled exploitation and privilege escalation using Kali Linux and Metasploit",
            "Author professional penetration test executive reports and remediation guides"
        ]
    },
    "course_web_security": {
        "course_id": "course_web_security",
        "course_name": "Web Application Security",
        "aliases": ["web security", "web application security", "appsec", "owasp", "web pentesting"],
        "description": "Modern application threats, OWASP Top 10 vulnerabilities, API security, and secure coding practices.",
        "category": "Application Security",
        "difficulty": "Intermediate",
        "duration": "6 weeks",
        "prerequisites": [
            "Basic web development fundamentals (HTML, JavaScript, HTTP) and basic SQL knowledge"
        ],
        "total_modules": 6,
        "total_segments": 6,
        "total_labs": 3,
        "skills": [
            "Web Application Security",
            "OWASP Top 10",
            "Burp Suite",
            "SQL Injection Mitigation",
            "XSS Mitigation",
            "CSRF Protection",
            "API Security",
            "Secure Coding"
        ],
        "module_names": [
            "Module 1: OWASP Top 10 & SQL Injection",
            "Module 2: Cross-Site Scripting (XSS) & CSRF",
            "Module 3: Broken Authentication & Session Management",
            "Module 4: Server-Side Request Forgery (SSRF) & Security Misconfigurations",
            "Module 5: REST API Security & JWT Vulnerabilities",
            "Module 6: Secure Code Review & Defensive Remediation"
        ],
        "module_details": [
            {
                "module_number": 1,
                "name": "OWASP Top 10 & SQL Injection",
                "description": "In-band (Union, Error-based), Blind (Boolean, Time-based), and Out-of-band SQLi. Defensive mitigation via Parameterized Queries (Prepared Statements) and ORMs.",
                "topics": ["In-band & Blind SQLi", "Database Exfiltration", "Parameterized Queries", "Prepared Statements"]
            },
            {
                "module_number": 2,
                "name": "Cross-Site Scripting (XSS) & CSRF",
                "description": "Stored, Reflected, and DOM-based XSS attacks. Remediation with context-aware output encoding and Content Security Policy (CSP). CSRF token defense and SameSite cookies.",
                "topics": ["Stored & Reflected XSS", "DOM-based XSS", "Content Security Policy (CSP)", "CSRF Tokens & SameSite"]
            },
            {
                "module_number": 3,
                "name": "Broken Authentication & Session Management",
                "description": "Session fixation, weak session IDs, password reset vulnerabilities, credential stuffing, and OAuth 2.0 / SSO misconfigurations.",
                "topics": ["Session Fixation", "JWT Tampering", "Credential Stuffing", "OAuth 2.0 Security"]
            },
            {
                "module_number": 4,
                "name": "Server-Side Request Forgery (SSRF) & Security Misconfigurations",
                "description": "SSRF exploiting internal microservices and cloud metadata endpoints (AWS 169.254.169.254). Mitigations using IP allowlisting and network segmentation.",
                "topics": ["SSRF Cloud Exploitation", "Metadata Endpoint Protection", "Security Headers", "CORS Misconfigurations"]
            },
            {
                "module_number": 5,
                "name": "REST API Security & JWT Vulnerabilities",
                "description": "Broken Object Level Authorization (BOLA), mass assignment, rate limiting, and JWT signature bypass vulnerabilities.",
                "topics": ["BOLA / IDOR in APIs", "JWT None Algorithm", "Rate Limiting & Throttling", "API Authentication"]
            },
            {
                "module_number": 6,
                "name": "Secure Code Review & Defensive Remediation",
                "description": "Static Application Security Testing (SAST), manual secure code review, input sanitization, and defensive engineering workflows.",
                "topics": ["SAST Tooling", "Code Review Workflows", "Input Sanitization", "Defensive Architecture"]
            }
        ],
        "topics": [
            "Module 1: OWASP Top 10 & SQL Injection (In-band, Blind, Out-of-band SQLi, Parameterized queries)",
            "Module 2: Cross-Site Scripting (XSS) & CSRF (Stored, Reflected, DOM XSS, CSP, SameSite cookies)",
            "Module 3: Broken Authentication & Session Management",
            "Module 4: Server-Side Request Forgery (SSRF) & Security Misconfigurations",
            "Module 5: REST API Security & JWT Vulnerabilities",
            "Module 6: Secure Code Review & Defensive Remediation"
        ],
        "labs": [
            "Burp Suite HTTP Interception & Proxy Lab",
            "SQL Injection Exploitation & Defense Lab",
            "XSS Sanitization & Content Security Policy (CSP) Lab"
        ],
        "certification": "CyberLearn Verified Certificate of Completion from CyberDaksh (Requires 100% completion, all labs, and >=75% on final assessment)",
        "course_status": "Active",
        "learning_objectives": [
            "Intercept, inspect, and manipulate HTTP/S traffic using Burp Suite",
            "Identify, exploit, and remediate OWASP Top 10 vulnerabilities including SQLi and XSS",
            "Secure REST APIs against Broken Object Level Authorization (BOLA) and JWT attacks",
            "Implement defensive engineering controls including CSP, prepared statements, and secure sessions"
        ]
    }
}

# Platform Overview Facts
PLATFORM_INFO = {
    "name": "CyberLearn LMS",
    "operator": "CyberDaksh",
    "description": "CyberLearn is an advanced, production-grade Cybersecurity Learning Management System (LMS) developed and operated by CyberDaksh. It provides interactive cybersecurity curriculum tracks, dedicated browser-based virtual lab sandboxes, personalized AI learning assistance through DAX, cryptographically verified certificates of completion, and direct internship career pathways with CyberDaksh security engineering teams.",
    "key_features": [
        "Structured Cybersecurity Tracks: Defensive Security, Offensive Security (Penetration Testing), and Application Security",
        "Cloud Virtual Lab Sandboxes: Browser-based virtual containers pre-installed with Wireshark, Nmap, Metasploit, Burp Suite, and Snort",
        "DAX AI Assistant: Context-aware AI tutor answering platform questions, course information, technical cybersecurity queries, and personal LMS progress",
        "Verified Digital Certificates: Cryptographically verifiable certificates of completion issued by CyberDaksh upon achieving >=75% on the final assessment",
        "CyberDaksh Internship Pathways: Top-performing learners achieving >=85% grade average qualify for security engineering internships and direct mentorship"
    ],
    "tracks": [
        "Defensive Security Track: Network Security Basics (Beginner, 6 weeks)",
        "Offensive Security Track: Ethical Hacking & Penetration Testing (Intermediate, 8 weeks)",
        "Application Security Track: Web Application Security (Intermediate, 6 weeks)"
    ]
}

def resolve_course_id(query_or_name: str) -> Optional[str]:
    """Resolves a course ID from query text, course name, or known aliases."""
    if not query_or_name:
        return None
    q = query_or_name.lower().strip()
    if q in COURSE_CATALOG:
        return q
    for cid, c in COURSE_CATALOG.items():
        if q == c["course_name"].lower() or cid == q:
            return cid
        for alias in c["aliases"]:
            if alias in q:
                return cid
    return None

def get_all_courses() -> List[Dict[str, Any]]:
    """Returns a list of all active courses in the catalog."""
    return list(COURSE_CATALOG.values())

def get_course_information(course_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves full structured course information by course ID or name.
    """
    resolved_id = resolve_course_id(course_id)
    if not resolved_id or resolved_id not in COURSE_CATALOG:
        return None
    
    course = COURSE_CATALOG[resolved_id]
    return {
        "type": "course_information",
        "course_id": course["course_id"],
        "course_name": course["course_name"],
        "difficulty": course["difficulty"],
        "category": course["category"],
        "duration": course["duration"],
        "description": course["description"],
        "prerequisites": course["prerequisites"],
        "modules": course["total_modules"],
        "total_segments": course["total_segments"],
        "labs": course["total_labs"],
        "skills": course["skills"],
        "module_names": course.get("module_names", []),
        "module_details": course.get("module_details", []),
        "topics": course["topics"],
        "lab_list": course["labs"],
        "certification": course["certification"],
        "course_status": course["course_status"],
        "learning_objectives": course.get("learning_objectives", [])
    }

def get_course_modules(course_id: str) -> Optional[Dict[str, Any]]:
    """Tool: Retrieves verified ordered syllabus and module list for a course."""
    info = get_course_information(course_id)
    if not info:
        return None
    return {
        "type": "course_modules",
        "course_id": info["course_id"],
        "course_name": info["course_name"],
        "total_modules": info["modules"],
        "module_names": info["module_names"],
        "module_details": info["module_details"]
    }

def get_course_prerequisites(course_id: str) -> Optional[Dict[str, Any]]:
    """Tool: Retrieves verified prerequisites for a course."""
    info = get_course_information(course_id)
    if not info:
        return None
    return {
        "type": "course_prerequisites",
        "course_id": info["course_id"],
        "course_name": info["course_name"],
        "difficulty": info["difficulty"],
        "prerequisites": info["prerequisites"]
    }

def get_course_duration(course_id: str) -> Optional[Dict[str, Any]]:
    """Tool: Retrieves verified duration for a course."""
    info = get_course_information(course_id)
    if not info:
        return None
    return {
        "type": "course_duration",
        "course_id": info["course_id"],
        "course_name": info["course_name"],
        "duration": info["duration"],
        "total_modules": info["modules"],
        "total_labs": info["labs"]
    }

def get_course_labs(course_id: str) -> Optional[Dict[str, Any]]:
    """Tool: Retrieves verified hands-on virtual labs for a course."""
    info = get_course_information(course_id)
    if not info:
        return None
    return {
        "type": "course_labs",
        "course_id": info["course_id"],
        "course_name": info["course_name"],
        "total_labs": info["labs"],
        "lab_list": info["lab_list"]
    }

def get_course_certification(course_id: str) -> Optional[Dict[str, Any]]:
    """Tool: Retrieves verified certification requirements for a course."""
    info = get_course_information(course_id)
    if not info:
        return None
    return {
        "type": "course_certification",
        "course_id": info["course_id"],
        "course_name": info["course_name"],
        "certification": info["certification"]
    }

def get_course_skills(course_id: str) -> Optional[Dict[str, Any]]:
    """Tool: Retrieves verified skills and learning outcomes for a course."""
    info = get_course_information(course_id)
    if not info:
        return None
    return {
        "type": "course_skills",
        "course_id": info["course_id"],
        "course_name": info["course_name"],
        "skills": info["skills"],
        "learning_objectives": info["learning_objectives"]
    }

def search_courses(query: str) -> Dict[str, Any]:
    """
    Searches the course catalog for matching courses based on title, skills, difficulty, or keywords.
    Returns structured results with matching reason and relevance indicator.
    """
    q = query.lower().strip()
    matches = []

    for cid, c in COURSE_CATALOG.items():
        matched = False
        reasons = []

        # 1. Match title or alias
        if any(alias in q for alias in c["aliases"]) or c["course_name"].lower() in q:
            matched = True
            reasons.append("Matched course title / alias")

        # 2. Match difficulty
        if c["difficulty"].lower() in q:
            matched = True
            reasons.append(f"Matched difficulty level '{c['difficulty']}'")

        # 3. Match category
        if c["category"].lower() in q:
            matched = True
            reasons.append(f"Matched track category '{c['category']}'")

        # 4. Match skills
        matched_skills = [s for s in c["skills"] if s.lower() in q]
        if matched_skills:
            matched = True
            reasons.append(f"Matched skills: {', '.join(matched_skills)}")

        # 5. Match topics / tools
        matched_topics = [t for t in c["topics"] if any(k in t.lower() for k in q.split() if len(k) > 3)]
        if matched_topics and not matched:
            matched = True
            reasons.append("Matched curriculum topics")

        # 6. Match labs
        if "lab" in q or "hands-on" in q or "practical" in q or "sandbox" in q:
            matched = True
            reasons.append(f"Includes {c['total_labs']} hands-on virtual sandbox labs")

        if matched:
            matches.append({
                "course_id": c["course_id"],
                "course_name": c["course_name"],
                "difficulty": c["difficulty"],
                "category": c["category"],
                "duration": c["duration"],
                "description": c["description"],
                "modules": c["total_modules"],
                "labs": c["total_labs"],
                "skills": c["skills"],
                "matching_reason": "; ".join(reasons) if reasons else "Keyword match"
            })

    # If no specific keyword matched, return all available courses as catalog overview
    if not matches:
        matches = [
            {
                "course_id": c["course_id"],
                "course_name": c["course_name"],
                "difficulty": c["difficulty"],
                "category": c["category"],
                "duration": c["duration"],
                "description": c["description"],
                "modules": c["total_modules"],
                "labs": c["total_labs"],
                "skills": c["skills"],
                "matching_reason": "General catalog entry"
            }
            for c in COURSE_CATALOG.values()
        ]

    return {
        "type": "course_search",
        "query": query,
        "count": len(matches),
        "courses": matches
    }

def recommend_courses(criteria: Optional[str] = None, difficulty: Optional[str] = None) -> Dict[str, Any]:
    """
    Recommends courses based on student profile, target difficulty, or interest areas.
    Deterministic, zero-hallucination recommendation based on actual catalog records.
    """
    crit = (criteria or "").lower()
    diff = (difficulty or "").lower()

    if "beginner" in crit or diff == "beginner" or "start" in crit or "no experience" in crit or "entry" in crit or "foundation" in crit:
        rec_course = COURSE_CATALOG["course_network_sec"]
        reason = "Recommended for beginners because it introduces core networking protocols, architecture, firewalls, and Wireshark with no prior cybersecurity prerequisites."
    elif "ethical hacking" in crit or "pentest" in crit or "offensive" in crit or "red team" in crit or "exploitation" in crit:
        rec_course = COURSE_CATALOG["course_ethical_hack"]
        reason = "Recommended for offensive security and penetration testing career paths, covering Nmap, Metasploit, vulnerability assessment, and privilege escalation."
    elif "web" in crit or "appsec" in crit or "developer" in crit or "owasp" in crit or "application security" in crit:
        rec_course = COURSE_CATALOG["course_web_security"]
        reason = "Recommended for web developers and application security engineers, focusing on OWASP Top 10 vulnerabilities, SQL injection, XSS, and Burp Suite."
    else:
        rec_course = COURSE_CATALOG["course_network_sec"]
        reason = "Recommended foundational course on CyberLearn LMS providing essential networking and defensive security skills."

    return {
        "type": "course_recommendation",
        "recommended_course": {
            "course_id": rec_course["course_id"],
            "course_name": rec_course["course_name"],
            "difficulty": rec_course["difficulty"],
            "category": rec_course["category"],
            "duration": rec_course["duration"],
            "prerequisites": rec_course["prerequisites"],
            "modules": rec_course["total_modules"],
            "labs": rec_course["total_labs"],
            "skills": rec_course["skills"],
            "learning_objectives": rec_course.get("learning_objectives", [])
        },
        "reason": reason,
        "alternative_courses": [
            {"course_id": c["course_id"], "course_name": c["course_name"], "difficulty": c["difficulty"], "category": c["category"]}
            for cid, c in COURSE_CATALOG.items() if cid != rec_course["course_id"]
        ]
    }

def compare_courses(course_id_1: str, course_id_2: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Compares two courses side-by-side using verified catalog attributes.
    If course_id_2 is not provided or invalid, returns comparison against all alternatives or indicates lack of comparison target.
    """
    cid1 = resolve_course_id(course_id_1)
    if not cid1 or cid1 not in COURSE_CATALOG:
        return None

    c1 = COURSE_CATALOG[cid1]

    if course_id_2:
        cid2 = resolve_course_id(course_id_2)
        if not cid2 or cid2 not in COURSE_CATALOG or cid1 == cid2:
            return {
                "type": "course_comparison",
                "valid_comparison": False,
                "reason": f"The requested second course '{course_id_2}' is not available in the CyberLearn course catalog.",
                "course_1": {
                    "course_id": c1["course_id"],
                    "course_name": c1["course_name"],
                    "category": c1["category"],
                    "difficulty": c1["difficulty"],
                    "duration": c1["duration"],
                    "modules": c1["total_modules"],
                    "labs": c1["total_labs"],
                    "prerequisites": c1["prerequisites"],
                    "skills": c1["skills"]
                },
                "available_courses_for_comparison": [
                    {"course_id": c["course_id"], "course_name": c["course_name"]}
                    for cid, c in COURSE_CATALOG.items() if cid != cid1
                ]
            }
        c2 = COURSE_CATALOG[cid2]
    else:
        # Default second course to compare against
        other_cid = [c for c in COURSE_CATALOG if c != cid1][0]
        c2 = COURSE_CATALOG[other_cid]

    return {
        "type": "course_comparison",
        "valid_comparison": True,
        "course_1": {
            "course_id": c1["course_id"],
            "course_name": c1["course_name"],
            "category": c1["category"],
            "difficulty": c1["difficulty"],
            "duration": c1["duration"],
            "modules": c1["total_modules"],
            "labs": c1["total_labs"],
            "prerequisites": c1["prerequisites"],
            "skills": c1["skills"]
        },
        "course_2": {
            "course_id": c2["course_id"],
            "course_name": c2["course_name"],
            "category": c2["category"],
            "difficulty": c2["difficulty"],
            "duration": c2["duration"],
            "modules": c2["total_modules"],
            "labs": c2["total_labs"],
            "prerequisites": c2["prerequisites"],
            "skills": c2["skills"]
        }
    }
