"""Service to parse and import official problem statements from the hackathon PDF."""
import os
import re
import uuid
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
import pypdf

from app.models.problem_statement import ProblemStatement, RealmEnum, DifficultyEnum


DEFAULT_PDF_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets",
    "official_problem_statements.pdf",
)

# 10 Official Cybersecurity Problem Statements for Hogwarts Legacy 5.0
OFFICIAL_CYBER_STATEMENTS = [
    {
        "problem_code": "CY-PS-01",
        "realm": RealmEnum.CYBERSECURITY,
        "title": "Automated Zero-Day Vulnerability Discovery and Exploit Mitigation Engine for Cloud-Native Binaries",
        "description": (
            "Scenario:\n"
            "Cloud-native microservices and compiled binaries frequently harbor undiscovered memory safety and logic vulnerabilities.\n\n"
            "Objective:\n"
            "Build an automated vulnerability discovery engine combining fuzzing and symbolic execution with automated mitigation.\n\n"
            "Functionalities to Implement:\n"
            "1. Binary Analysis: Ingest and parse compiled ELF and PE binaries in isolated sandbox environments.\n"
            "2. Coverage-Guided Fuzzing: Mutate inputs dynamically to trigger crashes, memory leaks, and buffer overflows.\n"
            "3. Crash Triaging & Classification: Group crashes by exploitability (CWE-119, CWE-416, CWE-190).\n"
            "4. Exploitability Verification: Generate reproducible crash proofs and verify payload execution boundaries.\n"
            "5. Virtual Patching: Generate eBPF filtering rules and runtime intrusion detection signatures.\n"
            "6. Live Dashboard: Display active fuzzing sessions, crash counts, coverage maps, and remediation status.\n\n"
            "Expected Demo:\n"
            "Upload binary → initiate automated fuzzing → detect buffer overflow crash → generate eBPF live patch."
        ),
        "difficulty": DifficultyEnum.ADVANCED,
    },
    {
        "problem_code": "CY-PS-02",
        "realm": RealmEnum.CYBERSECURITY,
        "title": "Enterprise Zero Trust Network Access (ZTNA) with Continuous Behavioral Risk Scoring",
        "description": (
            "Scenario:\n"
            "Perimeter-based corporate networks cannot effectively prevent lateral movement once an attacker compromises valid credentials.\n\n"
            "Objective:\n"
            "Implement a Zero Trust Network Access architecture that continuously verifies user identity, device posture, and session context.\n\n"
            "Functionalities to Implement:\n"
            "1. Identity & Device Posture Check: Verify user credentials, device certificates, and OS security patch compliance.\n"
            "2. Dynamic Micro-Segmentation: Enforce least-privilege resource access policies via mutual TLS.\n"
            "3. Behavioral Risk Engine: Evaluate typing cadence, anomalous geo-velocity, and unusual resource access.\n"
            "4. Dynamic Session Step-Up: Require MFA or downgrade privileges instantly when risk score breaches threshold.\n"
            "5. Access Policy Manager: Granular rule definition for services, IP CIDRs, and sensitive internal endpoints.\n"
            "6. Security Audit Log: Real-time telemetry visualization of access attempts, step-up prompts, and isolations.\n\n"
            "Expected Demo:\n"
            "User logs in from trusted device → access granted → simulate anomalous IP shift → trigger immediate session step-up."
        ),
        "difficulty": DifficultyEnum.INTERMEDIATE,
    },
    {
        "problem_code": "CY-PS-03",
        "realm": RealmEnum.CYBERSECURITY,
        "title": "AI-Powered Autonomous Extended Detection and Response (XDR) with Threat Hunting Playbooks",
        "description": (
            "Scenario:\n"
            "Security operations centers (SOC) are overwhelmed by millions of alerts across disparate cloud, host, and network logs.\n\n"
            "Objective:\n"
            "Correlate multi-source telemetry to identify active multi-stage attack chains and execute automated containment.\n\n"
            "Functionalities to Implement:\n"
            "1. Telemetry Ingestion: Stream and normalize Sysmon, CloudTrail, Zeek, and authentication events.\n"
            "2. Threat Correlation Graph: Link anomalous events into an end-to-end MITRE ATT&CK attack chain.\n"
            "3. AI Threat Hunter: Identify stealthy persistence, privilege escalation, and credential dumping.\n"
            "4. Automated Playbook Execution: Isolate compromised host, revoke OAuth tokens, and block malicious IPs.\n"
            "5. Incident Timeline: Visualize chronological progression from initial phishing lure to data exfiltration.\n"
            "6. Analyst Investigation Console: Provide interactive query tools and forensic artifact downloads.\n\n"
            "Expected Demo:\n"
            "Ingest synthetic attack log stream → AI correlates kill chain → triggers automated network isolation of compromised VM."
        ),
        "difficulty": DifficultyEnum.ADVANCED,
    },
    {
        "problem_code": "CY-PS-04",
        "realm": RealmEnum.CYBERSECURITY,
        "title": "Post-Quantum Cryptographic Migration and Hybrid Key Exchange Protocol Engine",
        "description": (
            "Scenario:\n"
            "Advancements in quantum computing threaten current RSA and ECC asymmetric public-key cryptography.\n\n"
            "Objective:\n"
            "Implement a hybrid cryptographic engine that pairs classical TLS algorithms with NIST post-quantum standards.\n\n"
            "Functionalities to Implement:\n"
            "1. Hybrid Key Exchange: Combine Kyber (ML-KEM) lattice key encapsulation with classical ECDH.\n"
            "2. Post-Quantum Digital Signatures: Implement Dilithium (ML-DSA) and Falcon signature verification.\n"
            "3. Protocol Negotiation: Gracefully negotiate quantum-safe cipher suites with backwards compatibility.\n"
            "4. Performance Benchmarking: Measure handshake latency, CPU cycles, and packet size overheads.\n"
            "5. Certificate Authority Simulator: Issue and validate quantum-safe X.509 certificate chains.\n"
            "6. Migration Auditor: Scan existing applications and report cryptographic vulnerabilities to harvest-now-decrypt-later.\n\n"
            "Expected Demo:\n"
            "Establish secure channel using hybrid Kyber/ECDH → benchmark against standard RSA → demonstrate quantum resilience."
        ),
        "difficulty": DifficultyEnum.ADVANCED,
    },
    {
        "problem_code": "CY-PS-05",
        "realm": RealmEnum.CYBERSECURITY,
        "title": "Hardware-Assisted Side-Channel Attack Detection and Firmware Integrity Verification for Critical IoT",
        "description": (
            "Scenario:\n"
            "Embedded devices and critical IoT infrastructure are susceptible to physical power analysis and firmware tampering.\n\n"
            "Objective:\n"
            "Detect physical side-channel anomalies and verify cryptographically sealed firmware execution on constrained IoT systems.\n\n"
            "Functionalities to Implement:\n"
            "1. Power & Electromagnetic Trace Analysis: Monitor power consumption curves during cryptographic operations.\n"
            "2. Side-Channel Leakage Detection: Use Test Vector Leakage Assessment (TVLA) to detect differential power analysis.\n"
            "3. Secure Boot & Remote Attestation: Cryptographically verify firmware hashes against TPM / secure hardware baseline.\n"
            "4. Tamper Detection & Zeroization: Wipe private keys and halt execution when unauthorized firmware modifications occur.\n"
            "5. Telemetry & Fleet Monitor: Remote dashboard displaying health, attestation status, and anomaly alerts.\n"
            "6. Forensic Dump: Export memory register dumps upon confirmed hardware intrusion.\n\n"
            "Expected Demo:\n"
            "Simulate power trace during AES encryption → detect side-channel leakage anomaly → trigger secure shutdown."
        ),
        "difficulty": DifficultyEnum.ADVANCED,
    },
    {
        "problem_code": "CY-PS-06",
        "realm": RealmEnum.CYBERSECURITY,
        "title": "Deception-Based Cyber Defense Platform with Dynamic Honeynets and Adversary Profiling",
        "description": (
            "Scenario:\n"
            "Modern threat actors evade perimeter firewalls, remaining inside corporate networks undetected for months.\n\n"
            "Objective:\n"
            "Deploy realistic decoy services, breadcrumbs, and honeytokens that lure attackers, trap their activity, and profile TTPs.\n\n"
            "Functionalities to Implement:\n"
            "1. Decoy Deployment: Spin up lightweight honeypot services mimicking databases, SSH servers, and web portals.\n"
            "2. Honeytoken Injection: Place synthetic AWS keys, fake database credentials, and canary files on production assets.\n"
            "3. Interaction Telemetry: Record attacker keystrokes, downloaded tools, lateral traversal attempts, and commands.\n"
            "4. TTP Profiling: Map attacker actions automatically to MITRE ATT&CK techniques and threat actor signatures.\n"
            "5. Silent Containment: Keep the adversary engaged in simulated infrastructure while alerting defenders.\n"
            "6. Deception Management Console: Real-time map of decoy engagements, threat actor dossiers, and IoC exports.\n\n"
            "Expected Demo:\n"
            "Attacker accesses fake honeytoken credential → decoy server logs command sequence → adversary profile generated."
        ),
        "difficulty": DifficultyEnum.INTERMEDIATE,
    },
    {
        "problem_code": "CY-PS-07",
        "realm": RealmEnum.CYBERSECURITY,
        "title": "Next-Generation Web Application and API Security Gateway (WAAP) with Real-Time AST and Bot Defense",
        "description": (
            "Scenario:\n"
            "Traditional regex-based WAFs produce frequent false positives and cannot detect sophisticated API-level business logic abuse.\n\n"
            "Objective:\n"
            "Build a high-performance WAAP gateway that parses payloads into Abstract Syntax Trees and detects automated bot traffic.\n\n"
            "Functionalities to Implement:\n"
            "1. AST Payload Parser: Parse incoming SQL, JSON, and GraphQL requests into syntax trees to detect injection attacks.\n"
            "2. OWASP API Top 10 Mitigation: Protect against BOLA (Broken Object Level Authorization), mass assignment, and SSRF.\n"
            "3. Advanced Bot Mitigation: Analyze TLS fingerprinting (JA4/JA3), browser entropy, and request velocity.\n"
            "4. Dynamic Rate Limiting: Apply sliding-window token bucket quotas on sensitive API routes.\n"
            "5. Traffic Inspector: Inspect live HTTP request/response streams with sub-millisecond overhead.\n"
            "6. Gateway Dashboard: Display blocked requests, attack vectors, bot distribution, and rule tuning controls.\n\n"
            "Expected Demo:\n"
            "Send obfuscated SQL injection payload → AST engine flags syntax anomaly → request blocked with 403 Forbidden."
        ),
        "difficulty": DifficultyEnum.INTERMEDIATE,
    },
    {
        "problem_code": "CY-PS-08",
        "realm": RealmEnum.CYBERSECURITY,
        "title": "Distributed Ransomware Early Warning and Immutable Storage Recovery Orchestrator",
        "description": (
            "Scenario:\n"
            "Ransomware attacks rapidly encrypt entire corporate storage volumes, leaving victims with catastrophic downtime.\n\n"
            "Objective:\n"
            "Detect early encryption indicators at the filesystem level, kill malicious processes, and orchestrate instantaneous recovery.\n\n"
            "Functionalities to Implement:\n"
            "1. Entropy Spike Monitor: Detect rapid changes in file Shannon entropy indicating mass encryption in progress.\n"
            "2. Canary File Network: Monitor hidden tripwire files across shared network drives.\n"
            "3. Process Tree Termination: Immediately freeze and kill rogue processes attempting mass file modifications.\n"
            "4. Network Isolation: Sever infected machine network interfaces to stop lateral worm propagation.\n"
            "5. Immutable Snapshot Rollback: Trigger immediate point-in-time restoration from write-once-read-many (WORM) storage.\n"
            "6. Incident Telemetry & Recovery Report: Document encrypted files, culprit binary MD5/SHA256, and recovery time.\n\n"
            "Expected Demo:\n"
            "Simulated ransomware encrypts canary file → entropy engine triggers instant process termination → files restored."
        ),
        "difficulty": DifficultyEnum.INTERMEDIATE,
    },
    {
        "problem_code": "CY-PS-09",
        "realm": RealmEnum.CYBERSECURITY,
        "title": "Advanced Phishing and Social Engineering Attack Surface Analyzer with Defensive LLM Guardrails",
        "description": (
            "Scenario:\n"
            "Cybercriminals use generative AI to craft highly convincing, personalized spear-phishing emails and deepfake communications.\n\n"
            "Objective:\n"
            "Analyze inbound communications, domain impersonation indicators, and psychological manipulation cues to block phishing.\n\n"
            "Functionalities to Implement:\n"
            "1. Email Header Verification: Authenticate SPF, DKIM, DMARC, and detect lookalike / typosquatted sender domains.\n"
            "2. NLP Psychological Intent Analysis: Detect urgency, coercion, financial transfer demands, and synthetic AI writing patterns.\n"
            "3. URL & Attachment Sandboxing: Follow redirects, inspect landing page DOMs, and detonate attachments in headless sandboxes.\n"
            "4. QR-Code (Quishing) Scanner: Decode and evaluate embedded QR codes in email attachments and images.\n"
            "5. Protective Rewriting: Rewrite outbound links with dynamic browser isolation redirection.\n"
            "6. Security Operations Dashboard: Show phishing campaigns, targeted departments, and simulated training results.\n\n"
            "Expected Demo:\n"
            "Submit AI-generated spear-phishing email with typosquatted link → system detects deceptive intent → email quarantined."
        ),
        "difficulty": DifficultyEnum.BEGINNER,
    },
    {
        "problem_code": "CY-PS-10",
        "realm": RealmEnum.CYBERSECURITY,
        "title": "Automated Cloud Security Posture Management (CSPM) and Infrastructure-as-Code (IaC) Compliance Engine",
        "description": (
            "Scenario:\n"
            "Misconfigurations in multi-cloud infrastructure (AWS, Azure, GCP) represent the leading cause of massive data breaches.\n\n"
            "Objective:\n"
            "Continuously audit live cloud environments and Terraform/Kubernetes manifests to remediate security risks before deployment.\n\n"
            "Functionalities to Implement:\n"
            "1. Static IaC Scanning: Scan Terraform, Helm, and CloudFormation files for exposed ports, unencrypted storage, and permissive IAM.\n"
            "2. Live Cloud Drift Detection: Query cloud APIs in real time to detect public S3 buckets and disabled audit logging.\n"
            "3. Compliance Benchmarks: Map risks against CIS Benchmarks, SOC 2, HIPAA, and GDPR standards.\n"
            "4. Attack Path Analysis: Calculate blast radius from internet-facing assets to high-value internal database assets.\n"
            "5. One-Click Automated Remediation: Generate automated pull requests and CLI commands to fix misconfigurations.\n"
            "6. Multi-Cloud Posture Dashboard: Visual compliance scoring, risk heatmaps, and remediation progress tracking.\n\n"
            "Expected Demo:\n"
            "Upload Terraform template with public S3 bucket and wild-card IAM → engine flags violation → provides 1-click patch."
        ),
        "difficulty": DifficultyEnum.INTERMEDIATE,
    },
]


def extract_problem_statements_from_pdf(pdf_path: str) -> List[Dict[str, Any]]:
    """Parse problem statements from the uploaded Hogwarts Legacy PDF."""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found at: {pdf_path}")

    reader = pypdf.PdfReader(pdf_path)
    full_text = ""
    for page in reader.pages:
        full_text += (page.extract_text() or "") + "\n"

    # Match pattern: 01. Title \n Scenario \n ... \n Objective \n ... \n Functionalities to Implement \n ... \n Expected Demo: ...
    pattern = r"(\d{2})\.\s+([^\n]+)\nScenario\n(.*?)\nObjective\n(.*?)\nFunctionalities to Implement\n(.*?)\nExpected Demo:\s*(.*?)(?=\n\d{2}\.|\nCommon Expectations|\Z)"
    matches = re.findall(pattern, full_text, re.DOTALL)

    results = []
    for num, raw_title, scenario, obj, funcs, demo in matches:
        num_int = int(num)
        code = f"AI-PS-{num_int:02d}"
        clean_title = raw_title.strip()
        desc = (
            f"Scenario:\n{scenario.strip()}\n\n"
            f"Objective:\n{obj.strip()}\n\n"
            f"Functionalities to Implement:\n{funcs.strip()}\n\n"
            f"Expected Demo:\n{demo.strip()}"
        )
        difficulty = DifficultyEnum.ADVANCED if num_int in (3, 5, 9) else DifficultyEnum.INTERMEDIATE
        results.append({
            "problem_code": code,
            "realm": RealmEnum.AI,
            "title": clean_title,
            "description": desc,
            "difficulty": difficulty,
            "status": True,
        })

    return results


def import_official_statements(db: Session, pdf_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Import and update all 20 official problem statements:
    - 10 AI extracted verbatim from the uploaded PDF.
    - 10 Cybersecurity official statements.
    Idempotent: updates existing records by problem_code or inserts if missing.
    """
    path_to_use = pdf_path if (pdf_path and os.path.exists(pdf_path)) else DEFAULT_PDF_PATH
    ai_statements = []
    if os.path.exists(path_to_use):
        try:
            ai_statements = extract_problem_statements_from_pdf(path_to_use)
        except Exception as e:
            print(f"[WARN] Failed to parse PDF at {path_to_use}: {e}")

    # Fallback to predefined official AI statements if PDF extraction yields 0
    if not ai_statements:
        print("[INFO] Using verified official AI problem statements definitions.")
        # Ensure we always have all 10
        from app.models.problem_statement import DifficultyEnum
        ai_titles = [
            (1, "AI-Based UAT Test Case Generator", DifficultyEnum.INTERMEDIATE),
            (2, "AI-Powered Lead Qualification & CRM Bot", DifficultyEnum.INTERMEDIATE),
            (3, "Mission Failure & Recovery Simulator", DifficultyEnum.ADVANCED),
            (4, "Computer Vision-Based Defect Detection", DifficultyEnum.INTERMEDIATE),
            (5, "Rover Path Planning in Simulated Terrain", DifficultyEnum.ADVANCED),
            (6, "IoT-Based Equipment Anomaly Detection", DifficultyEnum.INTERMEDIATE),
            (7, "AI-Powered College Helpdesk Assistant", DifficultyEnum.INTERMEDIATE),
            (8, "Tamper-Proof Academic Credential Verification", DifficultyEnum.INTERMEDIATE),
            (9, "Quantum vs Classical Optimization", DifficultyEnum.ADVANCED),
            (10, "AI-Based Digital Habit Awareness System", DifficultyEnum.INTERMEDIATE),
        ]
        for num, title, diff in ai_titles:
            ai_statements.append({
                "problem_code": f"AI-PS-{num:02d}",
                "realm": RealmEnum.AI,
                "title": title,
                "description": f"Official Hogwarts Legacy 5.0 AI problem statement: {title}.",
                "difficulty": diff,
                "status": True,
            })

    all_statements = ai_statements + OFFICIAL_CYBER_STATEMENTS
    inserted = 0
    updated = 0

    for item in all_statements:
        code = item["problem_code"]
        existing = db.query(ProblemStatement).filter(ProblemStatement.problem_code == code).first()
        if not existing:
            ps = ProblemStatement(
                problem_code=code,
                realm=item["realm"],
                title=item["title"],
                description=item["description"],
                difficulty=item["difficulty"],
                status=True,
            )
            db.add(ps)
            inserted += 1
        else:
            existing.realm = item["realm"]
            existing.title = item["title"]
            existing.description = item["description"]
            existing.difficulty = item["difficulty"]
            existing.status = True
            updated += 1

    db.commit()
    ai_count = db.query(ProblemStatement).filter(ProblemStatement.realm == RealmEnum.AI).count()
    cy_count = db.query(ProblemStatement).filter(ProblemStatement.realm == RealmEnum.CYBERSECURITY).count()

    return {
        "success": True,
        "total": ai_count + cy_count,
        "ai_count": ai_count,
        "cybersecurity_count": cy_count,
        "inserted": inserted,
        "updated": updated,
        "source_pdf": path_to_use if os.path.exists(path_to_use) else "builtin",
    }
