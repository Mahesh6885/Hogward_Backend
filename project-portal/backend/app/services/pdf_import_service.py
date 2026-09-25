"""Service to parse and import official problem statements from the hackathon PDF."""
import os
import re
import uuid
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

try:
    import pypdf
except ImportError:
    pypdf = None

from app.models.problem_statement import ProblemStatement, RealmEnum, DifficultyEnum


DEFAULT_PDF_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets",
    "official_problem_statements.pdf",
)

# 10 Official Artificial Intelligence Problem Statements (Verbatim from Official PDF)
OFFICIAL_AI_STATEMENTS = [
    {
        "problem_code": "AI-PS-01",
        "realm": RealmEnum.AI,
        "title": "AI-Based UAT Test Case Generator",
        "description": (
            "Scenario:\n"
            "Software teams often spend significant time manually converting business workflows and requirements into detailed User Acceptance Testing (UAT) test cases.\n\n"
            "Objective:\n"
            "Convert business requirements and workflows into structured User Acceptance Testing test cases.\n\n"
            "Functionalities to Implement:\n"
            "1. Requirement Input: Accept text, user stories, workflow descriptions, or uploaded documents.\n"
            "2. Requirement Understanding: Extract business rules, roles, actions, outcomes, conditions, and dependencies.\n"
            "3. Scenario Generation: Create positive, negative, and boundary test scenarios.\n"
            "4. Test Case Generation: Include test ID, scenario, preconditions, steps, test data, and expected result.\n"
            "5. Role-Based Cases: Generate cases for different roles and permission levels.\n"
            "6. Validation: Flag duplicates, incomplete cases, and requirements lacking detail.\n"
            "7. Review & Editing: Allow users to review, edit, and regenerate cases.\n"
            "8. Export & Dashboard: Display cases by scenario, priority, and role; export to Excel or CSV.\n\n"
            "Expected Demo:\n"
            "Upload a workflow → generate scenarios and test cases → review/edit → export the test suite."
        ),
        "difficulty": DifficultyEnum.INTERMEDIATE,
    },
    {
        "problem_code": "AI-PS-02",
        "realm": RealmEnum.AI,
        "title": "AI-Powered Lead Qualification & CRM Bot",
        "description": (
            "Scenario:\n"
            "Businesses receive enquiries from multiple customers, but manually collecting information and identifying high-potential leads can be time-consuming.\n\n"
            "Objective:\n"
            "Collect customer enquiries, evaluate lead quality, and manage leads through a CRM workflow.\n\n"
            "Functionalities to Implement:\n"
            "1. Customer Chatbot: Provide a chat interface and understand natural-language enquiries.\n"
            "2. Information Collection: Collect name, contact details, requirements, budget, and timeline; ask follow-up questions when needed.\n"
            "3. Information Extraction: Convert conversation details into structured fields.\n"
            "4. Qualification Engine: Evaluate leads using configurable budget, need, timeline, and business-fit criteria.\n"
            "5. Lead Scoring: Assign scores and categorize leads as High, Medium, or Low priority.\n"
            "6. Lead Categorization: Classify leads by product/service interest and enquiry type.\n"
            "7. CRM Management: Create, edit, and store leads in a database.\n"
            "8. Assignment & Pipeline: Assign leads to representatives and track New, Qualified, Contacted, and Converted stages.\n"
            "9. Dashboard & Summary: Show leads, scores, statuses, conversion statistics, and concise conversation summaries.\n\n"
            "Expected Demo:\n"
            "Customer chats → bot collects details → qualifies and scores lead → saves it to the CRM dashboard."
        ),
        "difficulty": DifficultyEnum.INTERMEDIATE,
    },
    {
        "problem_code": "AI-PS-03",
        "realm": RealmEnum.AI,
        "title": "Mission Failure & Recovery Simulator",
        "description": (
            "Scenario:\n"
            "Autonomous drones may encounter unexpected situations such as GPS loss, low battery, communication failure, or obstacles during a mission.\n\n"
            "Objective:\n"
            "Simulate drone mission failures and demonstrate how an autonomous system detects and responds.\n\n"
            "Functionalities to Implement:\n"
            "1. Mission Simulator: Create a visual environment with drone, start point, and destination.\n"
            "2. Mission Configuration: Set mission parameters and destination.\n"
            "3. Failure Scenarios: Simulate GPS loss, low battery, communication failure, and obstacles.\n"
            "4. Failure Detection: Monitor simulated status and detect predefined failure conditions.\n"
            "5. Failure Classification: Identify failure type, severity, and potential mission impact.\n"
            "6. Recovery Decision Engine: Select actions such as return-to-home, hover, or alternate route based on failure.\n"
            "7. Recovery Simulation: Execute the action in simulation and show whether recovery succeeds.\n"
            "8. Dashboard & Timeline: Display battery, GPS, communication, mission state, failures, recovery decisions, and final outcome.\n\n"
            "Expected Demo:\n"
            "Start a simulated mission → trigger a failure → detect it → select recovery → display the mission outcome."
        ),
        "difficulty": DifficultyEnum.ADVANCED,
    },
    {
        "problem_code": "AI-PS-04",
        "realm": RealmEnum.AI,
        "title": "Computer Vision-Based Defect Detection",
        "description": (
            "Scenario:\n"
            "Manufacturing industries need to identify defective products quickly and consistently during quality inspection.\n\n"
            "Objective:\n"
            "Identify and classify predefined defects in manufactured product images or camera input.\n\n"
            "Functionalities to Implement:\n"
            "1. Image Input: Upload product images or use live camera input where available.\n"
            "2. Preprocessing: Resize and normalize images for model input.\n"
            "3. Defect Detection: Use a trained computer-vision model to identify predefined defects.\n"
            "4. Defect Classification: Classify scratches, cracks, dents, or other selected defect categories.\n"
            "5. Defect Localization: Highlight defects with bounding boxes or segmentation masks, depending on the model.\n"
            "6. Confidence Scoring: Display model confidence for each detection.\n"
            "7. Acceptance Decision: Mark products Accepted or Rejected using predefined rules.\n"
            "8. Inspection History & Dashboard: Store results and show defect categories and acceptance/rejection statistics.\n"
            "9. Inspection Report: Include image, detected defects, and final decision.\n\n"
            "Expected Demo:\n"
            "Upload a product image → detect and highlight defects → classify them → show acceptance/rejection."
        ),
        "difficulty": DifficultyEnum.INTERMEDIATE,
    },
    {
        "problem_code": "AI-PS-05",
        "realm": RealmEnum.AI,
        "title": "Rover Path Planning in Simulated Terrain",
        "description": (
            "Scenario:\n"
            "Autonomous rovers operating in unknown or challenging environments need to reach specific destinations while avoiding obstacles.\n\n"
            "Objective:\n"
            "Plan a safe and efficient route for a rover through an obstacle-filled simulated environment.\n\n"
            "Functionalities to Implement:\n"
            "1. Terrain Simulator: Create a grid/map with free paths, obstacles, and restricted areas.\n"
            "2. Start/Destination: Let users select starting point and destination.\n"
            "3. Obstacle Configuration: Add/remove obstacles and choose preset terrain layouts.\n"
            "4. Pathfinding: Implement A*, Dijkstra, or another suitable algorithm to find a safe route.\n"
            "5. Path Optimization: Minimize distance or movement cost using defined criteria.\n"
            "6. Movement Simulation: Animate rover movement and display current position.\n"
            "7. Dynamic Obstacles: Introduce obstacles during movement and recalculate the route.\n"
            "8. Visualization & Metrics: Show planned/actual path, distance, steps, and planning time.\n"
            "9. Mission Summary: Report whether the rover reached its destination and the route taken.\n\n"
            "Expected Demo:\n"
            "Create terrain → set start and destination → plan and animate route → add an obstacle → show replanning."
        ),
        "difficulty": DifficultyEnum.ADVANCED,
    },
    {
        "problem_code": "AI-PS-06",
        "realm": RealmEnum.AI,
        "title": "IoT-Based Equipment Anomaly Detection",
        "description": (
            "Scenario:\n"
            "Industrial equipment can develop faults when parameters such as temperature, vibration, or power consumption move outside normal operating patterns.\n\n"
            "Objective:\n"
            "Monitor equipment sensor data and identify abnormal conditions early.\n\n"
            "Functionalities to Implement:\n"
            "1. Equipment Registration: Register equipment with unique IDs and types.\n"
            "2. Sensor Data: Collect or simulate temperature, vibration, and power readings.\n"
            "3. Live Monitoring: Display incoming readings and update equipment status.\n"
            "4. Normal Baseline: Define normal ranges or expected patterns for each sensor.\n"
            "5. Anomaly Detection: Detect abnormal values or patterns using thresholds or a model.\n"
            "6. Anomaly Classification: Categorize overheating, excessive vibration, or unusual power consumption.\n"
            "7. Health Scoring: Calculate equipment health/risk from sensor readings.\n"
            "8. Alerts & Dashboard: Trigger alerts and show readings, health, anomaly history, and affected equipment.\n"
            "9. Monitoring Report: Summarize anomalies and recommended inspection actions.\n\n"
            "Expected Demo:\n"
            "Simulate sensor data → introduce abnormal readings → detect anomaly → alert and display equipment health."
        ),
        "difficulty": DifficultyEnum.INTERMEDIATE,
    },
    {
        "problem_code": "AI-PS-07",
        "realm": RealmEnum.AI,
        "title": "AI-Powered College Helpdesk Assistant",
        "description": (
            "Scenario:\n"
            "Students frequently need information about examinations, academic processes, departments, events, and various college services.\n\n"
            "Objective:\n"
            "Answer student questions using an approved college knowledge base.\n\n"
            "Functionalities to Implement:\n"
            "1. Chat Interface: Allow students to ask natural-language questions.\n"
            "2. Knowledge Base: Upload academic calendars, exam schedules, regulations, and department information; organize by category.\n"
            "3. Document Processing: Extract text and split documents into searchable sections.\n"
            "4. Knowledge Retrieval: Retrieve relevant information through semantic or keyword search.\n"
            "5. AI Response: Generate answers grounded in retrieved information.\n"
            "6. Source Citations: Show the supporting document or section for each answer.\n"
            "7. Query Categories: Handle examinations, admissions, departments, events, and academic processes.\n"
            "8. Fallback Handling: State when information is unavailable and record unanswered queries.\n"
            "9. Admin & Dashboard: Let authorized staff update documents; show query history, FAQs, and unanswered questions.\n\n"
            "Expected Demo:\n"
            "Upload college documents → ask a student question → retrieve information → answer with a source."
        ),
        "difficulty": DifficultyEnum.INTERMEDIATE,
    },
    {
        "problem_code": "AI-PS-08",
        "realm": RealmEnum.AI,
        "title": "Tamper-Proof Academic Credential Verification",
        "description": (
            "Scenario:\n"
            "Academic certificates can be difficult to verify manually, creating challenges for institutions, employers, and students.\n\n"
            "Objective:\n"
            "Enable institutions to issue digital credentials and allow authorized users to verify authenticity.\n\n"
            "Functionalities to Implement:\n"
            "1. Institution Registration: Register credential-issuing institutions and maintain their status.\n"
            "2. Credential Issuance: Create certificates with student, qualification, institution, and issue-date details.\n"
            "3. Unique Credential ID: Generate a unique identifier for each credential.\n"
            "4. QR Code: Generate a QR code linking to the verification page.\n"
            "5. Integrity Protection: Hash credential data and store the integrity reference securely.\n"
            "6. Credential Verification: Verify using credential ID or QR code.\n"
            "7. Tampering Detection: Detect modified, invalid, revoked, or unrecognized credentials.\n"
            "8. Revocation: Allow authorized institutions to revoke credentials and show current status.\n"
            "9. Dashboard & History: Display verification results and record issuance, revocation, and verification events.\n\n"
            "Expected Demo:\n"
            "Issue a certificate → generate QR → verify it → alter a test record → demonstrate tampering detection."
        ),
        "difficulty": DifficultyEnum.INTERMEDIATE,
    },
    {
        "problem_code": "AI-PS-09",
        "realm": RealmEnum.AI,
        "title": "Quantum vs Classical Optimization",
        "description": (
            "Scenario:\n"
            "Real-world problems such as scheduling, routing, and resource allocation often involve finding the most efficient solution among many possible combinations.\n\n"
            "Objective:\n"
            "Solve a selected optimization problem with classical and quantum or quantum-inspired approaches and compare results.\n\n"
            "Functionalities to Implement:\n"
            "1. Problem Selection: Choose scheduling, routing, or resource allocation; define objective and constraints.\n"
            "2. Input Interface: Configure parameters and provide sample datasets.\n"
            "3. Classical Engine: Implement a suitable classical algorithm and produce a solution.\n"
            "4. Quantum-Based Engine: Implement a quantum or quantum-inspired method using a simulator/framework if needed.\n"
            "5. Constraint Validation: Check feasibility and identify violated constraints.\n"
            "6. Objective Calculation: Calculate the objective value for each solution.\n"
            "7. Performance Comparison: Compare solution quality, execution time, and feasibility.\n"
            "8. Visualization & Experiments: Show results in tables/charts and allow parameter changes and repeated runs.\n"
            "9. Comparison Report: Summarize settings, solutions, and metrics.\n\n"
            "Expected Demo:\n"
            "Configure a problem → run both approaches → compare solutions, feasibility, and performance."
        ),
        "difficulty": DifficultyEnum.ADVANCED,
    },
    {
        "problem_code": "AI-PS-10",
        "realm": RealmEnum.AI,
        "title": "AI-Based Digital Habit Awareness System",
        "description": (
            "Scenario:\n"
            "People spend significant time using digital devices and applications, but may not always understand their own usage patterns and habits.\n\n"
            "Objective:\n"
            "Analyze digital usage patterns and provide personalized awareness insights.\n\n"
            "Functionalities to Implement:\n"
            "1. Usage Data Input: Import or manually enter screen-time and application usage data.\n"
            "2. Application Tracking: Track time by app and categorize usage.\n"
            "3. Pattern Analysis: Identify daily/weekly trends, peak periods, and frequently used apps.\n"
            "4. Notification Analysis: Measure notification frequency and high-notification periods.\n"
            "5. Habit Detection: Identify long sessions, repeated patterns, and changes over time.\n"
            "6. AI Insights: Generate personalized, explainable insights from usage data.\n"
            "7. Recommendations: Suggest screen-time goals or reducing unnecessary notifications; let users configure goals.\n"
            "8. Goal Tracking: Set daily targets and monitor progress.\n"
            "9. Dashboard & Report: Show screen time, app usage, notifications, trends, goals, and recommendations.\n\n"
            "Expected Demo:\n"
            "Import usage data → analyze habits → generate insights → show recommendations and goal progress."
        ),
        "difficulty": DifficultyEnum.INTERMEDIATE,
    },
]

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
            "5. Immutable Snapshot Rollback: Trigger copy-on-write storage snapshot restoration via AWS EBS or ZFS API.\n"
            "6. Recovery Console: Display encryption progression velocity, affected shares, and one-click rollback controls.\n\n"
            "Expected Demo:\n"
            "Execute simulated ransomware payload → entropy spike detected within 3 files → process killed → snapshot rolled back."
        ),
        "difficulty": DifficultyEnum.ADVANCED,
    },
    {
        "problem_code": "CY-PS-09",
        "realm": RealmEnum.CYBERSECURITY,
        "title": "AI-Powered Phishing and Social Engineering Defense Engine with Computer Vision and Intent Analysis",
        "description": (
            "Scenario:\n"
            "Spear-phishing and business email compromise (BEC) leverage generative AI to bypass traditional SPF/DKIM filters.\n\n"
            "Objective:\n"
            "Detect deceptive inbound communications using multimodal intent analysis, visual brand impersonation, and sender reputation.\n\n"
            "Functionalities to Implement:\n"
            "1. Natural Language Intent Classifier: Detect urgency, credential harvesting requests, and executive impersonation.\n"
            "2. Visual Logo Inspection: Use CNN to detect spoofed Microsoft, Google, or bank logos on login pages.\n"
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
    if pypdf is None:
        raise ImportError("pypdf library is not installed. Please install 'pypdf>=4.0.0'.")

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
    - 10 AI extracted verbatim from the uploaded PDF (or verified verbatim constant).
    - 10 Cybersecurity official statements.
    Idempotent: updates existing records by problem_code or inserts if missing.
    """
    path_to_use = pdf_path if (pdf_path and os.path.exists(pdf_path)) else DEFAULT_PDF_PATH
    ai_statements = []

    # If pypdf is installed and PDF exists, try parsing from PDF
    if pypdf is not None and os.path.exists(path_to_use):
        try:
            ai_statements = extract_problem_statements_from_pdf(path_to_use)
        except Exception as e:
            print(f"[WARN] Failed to parse PDF at {path_to_use}: {e}")

    # Fallback to verified verbatim official AI statements
    if not ai_statements:
        print("[INFO] Using verified verbatim official AI problem statements.")
        ai_statements = OFFICIAL_AI_STATEMENTS

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
        "source_pdf": path_to_use if (pypdf is not None and os.path.exists(path_to_use)) else "official_verbatim_bundle",
    }
