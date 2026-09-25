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

# 10 Official Cybersecurity Problem Statements (Verbatim from Hogwarts Legacy 2.0 Cybersecurity PDF)
OFFICIAL_CYBER_STATEMENTS = [
    {
        "problem_code": "CY-PS-01",
        "realm": RealmEnum.CYBERSECURITY,
        "title": "Adaptive Phishing Detection & Response",
        "description": (
            "Scenario\n"
            "Employees receive suspicious links through emails, messaging apps, and social media. "
            "Attackers create fake websites that look like real banking, company, or government websites to steal user information.\n\n"
            "Objective\n"
            "Identify phishing websites, assess risk, and warn users before they interact with malicious content.\n\n"
            "Functionalities to Implement\n"
            "1. URL Scanner: Accept URLs; inspect suspicious characters, misleading subdomains, shortened links, and redirects.\n"
            "2. Domain Analysis: Check domain age and registration details where available; compare domain reputation against threat-intelligence sources.\n"
            "3. Website Content Analysis: Inspect webpage content for suspicious login forms, impersonation indicators, and misleading links.\n"
            "4. Phishing Detection Engine: Use rules or a machine-learning model to classify sites as Safe, Suspicious, or Phishing.\n"
            "5. Risk Scoring: Generate a 0–100 risk score and explain the factors contributing to it.\n"
            "6. User Warning System: Warn users about suspicious or malicious sites and explain why they were flagged.\n"
            "7. Threat Dashboard: Show scanned URLs, scores, results, and scan history.\n"
            "8. Security Report: Export URL, findings, score, and recommended actions.\n\n"
            "Expected Demo:\n"
            "Enter a suspicious URL → analyze it → show score and reasons → display a warning and generate a report."
        ),
        "difficulty": DifficultyEnum.INTERMEDIATE,
    },
    {
        "problem_code": "CY-PS-02",
        "realm": RealmEnum.CYBERSECURITY,
        "title": "Intelligent SOC Alert Correlation & Attack-Chain Reconstruction",
        "description": (
            "Scenario\n"
            "A Security Operations Center receives thousands of alerts from firewalls, servers, endpoints, DNS, and authentication systems. "
            "Some alerts look harmless individually but may actually be different steps of the same cyberattack.\n\n"
            "Objective\n"
            "Correlate security alerts from different sources and reconstruct the sequence of a potential cyberattack.\n\n"
            "Functionalities to Implement\n"
            "1. Log Ingestion: Import firewall, server, endpoint, DNS, and authentication logs from CSV or JSON samples.\n"
            "2. Log Normalization: Convert logs to a common structure with timestamps, IPs, usernames, event types, and severity.\n"
            "3. Alert Correlation: Link alerts using shared IPs, accounts, devices, and time windows; group them into incidents.\n"
            "4. Attack Pattern Detection: Identify sequences such as repeated failed logins followed by a successful login.\n"
            "5. Timeline Reconstruction: Arrange related events chronologically from initial activity to potential impact.\n"
            "6. MITRE ATT&CK Mapping: Map detected activity to relevant tactics and techniques.\n"
            "7. Incident Risk Scoring: Prioritize incidents using severity, affected assets, and correlated activity.\n"
            "8. SOC Dashboard & Report: Show incidents, alerts, severity, timeline, affected assets, and recommended actions.\n\n"
            "Expected Demo:\n"
            "Upload logs → correlate related alerts → reconstruct the attack timeline → display severity and an investigation report."
        ),
        "difficulty": DifficultyEnum.ADVANCED,
    },
    {
        "problem_code": "CY-PS-03",
        "realm": RealmEnum.CYBERSECURITY,
        "title": "Ransomware Early-Warning & Automated Containment",
        "description": (
            "Scenario\n"
            "An employee's computer suddenly starts opening and modifying hundreds of files. Antivirus does not recognize the process, "
            "and within minutes many documents become unreadable.\n\n"
            "Objective\n"
            "Detect ransomware-like behavior by monitoring file and process activity and demonstrate a safe response.\n\n"
            "Functionalities to Implement\n"
            "1. File Activity Monitoring: Monitor file creation, modification, renaming, and deletion in a designated test directory.\n"
            "2. Process Monitoring: Observe processes accessing files and flag suspicious activity.\n"
            "3. Behavior Detection: Identify rapid file changes, suspicious extensions, and unusual access patterns.\n"
            "4. Early Warning: Score behavior and trigger alerts when a defined threshold is crossed.\n"
            "5. Safe Containment: Demonstrate suspending a simulated process or restricting the test environment; include manual confirmation.\n"
            "6. Recovery Support: Use backups or snapshots to demonstrate recovery of test files.\n"
            "7. Evidence Collection: Record process details, file activity, and timestamps.\n"
            "8. Dashboard & Report: Show monitored files, alerts, containment status, affected files, and response actions.\n\n"
            "Expected Demo:\n"
            "Run a harmless behavior simulation in a test directory → detect abnormal changes → alert → demonstrate containment and recovery."
        ),
        "difficulty": DifficultyEnum.ADVANCED,
    },
    {
        "problem_code": "CY-PS-04",
        "realm": RealmEnum.CYBERSECURITY,
        "title": "API Abuse Detection & Dynamic Security Gateway",
        "description": (
            "Scenario\n"
            "A financial application provides APIs for login, payments, and account information. Attackers start sending abnormal requests "
            "to guess accounts, abuse APIs, manipulate parameters, and perform automated attacks.\n\n"
            "Objective\n"
            "Monitor API traffic, detect suspicious requests, and apply appropriate security controls.\n\n"
            "Functionalities to Implement\n"
            "1. API Gateway: Route requests to backend APIs and support authentication and validation.\n"
            "2. Request Monitoring: Capture endpoints, methods, timestamps, frequency, and request/response metadata.\n"
            "3. Rate-Limit Detection: Detect excessive requests, repeated login attempts, and request bursts.\n"
            "4. Abuse Detection: Flag suspicious parameter manipulation, abnormal patterns, and common injection indicators in a safe test setup.\n"
            "5. Behavioral Analysis: Establish normal client patterns and identify deviations.\n"
            "6. Risk Scoring: Score requests or sessions and categorize risk.\n"
            "7. Dynamic Controls: Apply rate limits, temporary blocks, and administrator-configurable rules.\n"
            "8. Dashboard & Audit Logs: Show traffic, suspicious clients, blocked requests, detected patterns, and actions taken.\n\n"
            "Expected Demo:\n"
            "Send normal and suspicious API requests → detect abnormal behavior → apply rate limiting or blocking → review security events."
        ),
        "difficulty": DifficultyEnum.INTERMEDIATE,
    },
    {
        "problem_code": "CY-PS-05",
        "realm": RealmEnum.CYBERSECURITY,
        "title": "Cloud Security Posture & Attack-Surface Analyzer",
        "description": (
            "Scenario\n"
            "A company has moved many systems to the cloud. Over time, some storage, servers, databases, permissions, and network services "
            "have accidentally become exposed or overly accessible.\n\n"
            "Objective\n"
            "Identify insecure cloud configurations, exposed resources, and excessive permissions.\n\n"
            "Functionalities to Implement\n"
            "1. Asset Inventory: Import or register storage, virtual machines, databases, and network services.\n"
            "2. Configuration Scanner: Scan configuration files or a sample environment for public exposure and insecure settings.\n"
            "3. Permission Analysis: Flag overly broad roles, access policies, and unnecessary administrative privileges.\n"
            "4. Network Exposure Analysis: Identify exposed ports and unrestricted inbound rules.\n"
            "5. Misconfiguration Detection: Detect public storage, missing encryption, and other insecure configurations.\n"
            "6. Risk Prioritization: Assign severity based on exposure and potential impact.\n"
            "7. Remediation Guidance: Provide concrete corrective actions for each finding.\n"
            "8. Dashboard & Report: Show assets, findings, severity, risk distribution, and recommended fixes.\n\n"
            "Expected Demo:\n"
            "Import a sample cloud configuration → scan it → display prioritized weaknesses → show remediation steps."
        ),
        "difficulty": DifficultyEnum.INTERMEDIATE,
    },
    {
        "problem_code": "CY-PS-06",
        "realm": RealmEnum.CYBERSECURITY,
        "title": "Digital Evidence Integrity & Chain-of-Custody",
        "description": (
            "Scenario\n"
            "During a cybercrime investigation, investigators collect computers, mobile data, disk images, screenshots, and network captures. "
            "The evidence is transferred between different authorized investigators during the investigation.\n\n"
            "Objective\n"
            "Maintain digital evidence integrity and record each custody transfer.\n\n"
            "Functionalities to Implement\n"
            "1. Evidence Registration: Upload files such as documents, screenshots, logs, or forensic images and assign a unique ID.\n"
            "2. Cryptographic Hash: Generate a SHA-256 hash and preserve it as the integrity reference.\n"
            "3. Metadata Management: Record evidence type, collection date, source, and investigator.\n"
            "4. Custody Tracking: Record transfers with timestamps, sender, receiver, and purpose.\n"
            "5. Role-Based Access: Separate investigator and administrator permissions.\n"
            "6. Integrity Verification: Recalculate hashes and compare them with the original to detect changes.\n"
            "7. Audit Trail: Log uploads, access, transfers, and verification actions chronologically.\n"
            "8. Dashboard & Report: Show evidence, custody history, integrity status, hash, and access history.\n\n"
            "Expected Demo:\n"
            "Upload evidence → generate its hash → transfer custody → alter a test copy → verify tampering and review custody history."
        ),
        "difficulty": DifficultyEnum.INTERMEDIATE,
    },
    {
        "problem_code": "CY-PS-07",
        "realm": RealmEnum.CYBERSECURITY,
        "title": "Insider Threat & User Behavior Analytics",
        "description": (
            "Scenario\n"
            "An employee account suddenly accesses sensitive files at unusual times and transfers large amounts of data. "
            "The account is valid and no obvious malware is detected.\n\n"
            "Objective\n"
            "Detect unusual user activity that may indicate an insider threat or compromised account while protecting privacy.\n\n"
            "Functionalities to Implement\n"
            "1. Activity Log Collection: Import login, file access, privilege-change, and data-transfer logs.\n"
            "2. Behavior Baseline: Establish typical login times, resource access, and activity frequency.\n"
            "3. Anomaly Detection: Flag unusual login times/locations, abnormal file access, excessive transfers, and privilege changes.\n"
            "4. User Risk Scoring: Score deviations and categorize severity.\n"
            "5. Alerting & Investigation: Explain suspicious activity and display the sequence of actions for investigation.\n"
            "6. Privacy Controls: Use pseudonymous identifiers where possible and restrict access to sensitive records.\n"
            "7. Dashboard: Show activity, anomalies, scores, and incident history.\n"
            "8. Investigation Report: Summarize suspicious actions, risk indicators, and recommended follow-up.\n\n"
            "Expected Demo:\n"
            "Import activity logs → establish a baseline → detect unusual activity → generate a risk score and investigation report."
        ),
        "difficulty": DifficultyEnum.INTERMEDIATE,
    },
    {
        "problem_code": "CY-PS-08",
        "realm": RealmEnum.CYBERSECURITY,
        "title": "Software Supply-Chain Threat Detection",
        "description": (
            "Scenario\n"
            "A development team installs a third-party software package during a routine update. "
            "The package looks normal but secretly contains suspicious code and communicates with an unknown external server.\n\n"
            "Objective\n"
            "Analyze software dependencies to identify vulnerabilities, suspicious packages, and integrity issues.\n\n"
            "Functionalities to Implement\n"
            "1. Dependency Upload: Accept package.json, requirements.txt, or Maven pom.xml and extract package names and versions.\n"
            "2. Dependency Inventory: List direct and, where supported, transitive dependencies.\n"
            "3. Vulnerability Detection: Check packages against a vulnerability database and identify known issues.\n"
            "4. Integrity Verification: Verify checksums or signatures where available and flag unexpected changes.\n"
            "5. Suspicious Package Detection: Flag known malicious indicators or suspicious package metadata for review.\n"
            "6. Risk Scoring: Score dependencies using vulnerability severity and integrity findings.\n"
            "7. SBOM Generation: Generate a Software Bill of Materials with package names, versions, and dependency information.\n"
            "8. Remediation & Report: Suggest safer versions or fixes and export findings, inventory, and SBOM.\n\n"
            "Expected Demo:\n"
            "Upload a dependency file → scan packages → identify vulnerabilities → generate an SBOM and remediation report."
        ),
        "difficulty": DifficultyEnum.INTERMEDIATE,
    },
    {
        "problem_code": "CY-PS-09",
        "realm": RealmEnum.CYBERSECURITY,
        "title": "IoT Behavioral Anomaly Detection",
        "description": (
            "Scenario\n"
            "A smart facility has hundreds of cameras, sensors, controllers, and other IoT devices. "
            "A normally isolated sensor suddenly starts communicating with an unknown external server and sends unusually high network traffic.\n\n"
            "Objective\n"
            "Learn normal IoT communication patterns and detect suspicious deviations.\n\n"
            "Functionalities to Implement\n"
            "1. Device Registration: Register devices with unique IDs, types, and expected communication behavior.\n"
            "2. Traffic Collection: Import or simulate traffic; record source/destination IP, protocol, volume, and timestamp.\n"
            "3. Behavior Baseline: Record expected destinations, protocols, and traffic levels for each device.\n"
            "4. Anomaly Detection: Flag unknown destinations, traffic spikes, unexpected protocols, or unusual activity times.\n"
            "5. Device Risk Scoring: Score anomalies and identify devices needing investigation.\n"
            "6. Isolation Simulation: Demonstrate simulated network isolation of a suspicious device.\n"
            "7. Alerts & Dashboard: Show device behavior, anomalies, risk, and alerts with reasons.\n"
            "8. Incident Report: Summarize suspicious traffic and recommended containment.\n\n"
            "Expected Demo:\n"
            "Simulate normal device traffic → introduce unusual communication → detect and flag the device → demonstrate simulated isolation."
        ),
        "difficulty": DifficultyEnum.INTERMEDIATE,
    },
    {
        "problem_code": "CY-PS-10",
        "realm": RealmEnum.CYBERSECURITY,
        "title": "Automated Cyber Incident Investigation & Response",
        "description": (
            "Scenario\n"
            "A company notices unusual login attempts, suspicious web requests, an unknown process on an employee computer, "
            "and communication with an unfamiliar external IP. These events are recorded by different security systems.\n\n"
            "Objective\n"
            "Correlate security events, reconstruct attack activity, identify affected systems, and recommend response actions.\n\n"
            "Functionalities to Implement\n"
            "1. Event Collection: Import authentication, endpoint, firewall, and network logs.\n"
            "2. Event Normalization: Convert records into a common event structure.\n"
            "3. Incident Correlation: Group related events using timestamps, IPs, usernames, and device IDs.\n"
            "4. Attack Timeline: Arrange events chronologically and identify a suspected sequence.\n"
            "5. Affected Asset Identification: Identify potentially affected devices, accounts, and services.\n"
            "6. Attack Classification: Map suspicious activity to relevant techniques and classify the incident.\n"
            "7. Risk Scoring: Score severity using event sequence and affected assets.\n"
            "8. Response Recommendations: Suggest actions such as disabling accounts or isolating endpoints; require authorization for real actions.\n"
            "9. Dashboard & Report: Show incidents, timeline, affected assets, risk, and response plan.\n\n"
            "Expected Demo:\n"
            "Import multiple logs → correlate events → reconstruct the attack → identify assets → generate a response plan."
        ),
        "difficulty": DifficultyEnum.ADVANCED,
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
