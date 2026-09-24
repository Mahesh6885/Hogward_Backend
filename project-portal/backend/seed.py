"""
Seed script — safe to run multiple times (idempotent).

Creates / ensures:
1. Three domains (AI, CYBERSECURITY, OPEN_INNOVATION)
2. Initial admin account (credentials from .env)
3. Exactly 10 predefined AI problem statements (AI-PS-01 to AI-PS-10)
4. Exactly 10 predefined Cybersecurity problem statements (CY-PS-01 to CY-PS-10)
5. Zero problem statements for Open Innovation
6. Sample teams with assigned problem statements
7. Cleans up legacy topics/topic locks to enforce fixed problem statement architecture.

Usage:
    cd backend
    python seed.py
"""
import os
import sys
import random

# Ensure the backend directory is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.core.config import settings
from app.core.security import hash_password
from app.database.database import SessionLocal
from app.models.domain import Domain, DomainName
from app.models.user import User, UserRole, UserStatus
from app.models.problem_statement import ProblemStatement
from app.models.project import Project, ProjectStatus


DOMAINS = [
    {
        "name": DomainName.AI.value,
        "description": "Artificial Intelligence — covers machine learning, deep learning, NLP, computer vision, and more.",
    },
    {
        "name": DomainName.CYBERSECURITY.value,
        "description": "Cybersecurity — covers network security, ethical hacking, cryptography, forensics, and more.",
    },
    {
        "name": DomainName.OPEN_INNOVATION.value,
        "description": "Open Innovation — users propose their own project topic freely.",
    },
]

AI_PROBLEM_STATEMENTS = [
    (
        "AI-PS-01",
        "Multi-Modal Clinical Diagnostic Assistant for Radiology and Electronic Health Records: "
        "Build an end-to-end multi-modal diagnostic reasoning engine that combines chest X-ray/CT radiograph imagery with structured Electronic Health Record (EHR) data and unstructured doctor clinical notes. "
        "The system must process DICOM/PNG images using vision transformers alongside patient vitals, pathology records, and historical admissions. It must accurately localize pulmonary lesions and cardiac abnormalities with attention heatmaps (Grad-CAM) while synthesizing clinically interpretable diagnostic summaries. "
        "The engine must strictly adhere to differential diagnostic protocols, automatically flag adverse drug-allergy interactions, quantify predictive uncertainty, and provide verifiable citations to established clinical medical ontologies (e.g., SNOMED CT and ICD-10) without hallucinating phantom conditions or unverified symptoms."
    ),
    (
        "AI-PS-02",
        "Autonomous Multi-Agent Collaborative Task Orchestration and Verification Framework: "
        "Design and deploy a resilient multi-agent orchestration architecture capable of decomposing complex, ambiguously phrased software engineering and business workflow requests into verifiable sub-goals. "
        "The system must coordinate specialized autonomous agents (planner, coder, verifier, and security auditor) with strict contract validation, dynamic replanning on tool failures, and cyclic dependency resolution. "
        "It must incorporate long-term vector memory caching with semantic deduplication, deterministic human-in-the-loop intervention checkpoints, rate-limiting guards against infinite recursive loops, and structured audit telemetry tracing agent communication graphs and token expenditures."
    ),
    (
        "AI-PS-03",
        "Real-Time Multilingual Speech-to-Speech Translation with Zero-Shot Voice Cloning: "
        "Develop an edge-deployable, low-latency streaming pipeline that captures spoken dialectal audio, performs streaming speech recognition, translates across non-English low-resource languages, and synthesizes output speech that preserves the speaker's original emotional intonation, cadence, and vocal timbre using zero-shot neural voice cloning. "
        "The pipeline must operate with an end-to-end glass-to-glass latency under 600ms, incorporate acoustic echo cancellation and background denoising algorithms, handle code-mixed conversational inputs (such as Spanglish or Hinglish), and generate synchronized lip-motion landmarks for video streaming integration."
    ),
    (
        "AI-PS-04",
        "Privacy-Preserving Federated Graph Neural Network for Anti-Money Laundering: "
        "Construct a decentralized, privacy-preserving financial forensics system using federated graph neural networks (FedGNN) across partitioned banking institutions without centralizing sensitive customer transaction logs. "
        "The platform must model multi-hop entity graphs to detect illicit structuring, wash trading, and synthetic identity rings traversing disparate banking ledgers. "
        "The framework must implement differential privacy mechanisms and secure multi-party computation (SMPC) to prevent gradient inversion attacks, ensure sub-second graph inference on real-time transaction streams, and generate automated regulatory Suspicious Activity Reports (SAR) with explainable sub-graph visualizations."
    ),
    (
        "AI-PS-05",
        "High-Precision Edge Computer Vision for Autonomous Precision Agriculture and Crop Disease Prognosis: "
        "Architect an offline-capable, lightweight deep learning computer vision pipeline designed for deployment on constrained edge hardware mounted on autonomous agricultural drones or tractors. "
        "The system must execute real-time multi-spectral leaf disease segmentation, weeds vs. crop classification, and soil moisture estimation under fluctuating natural illumination, partial occlusions, and severe camera jitter. "
        "The solution must feature automated quantization (INT8/FP16), model pruning to maintain 30+ FPS, and trigger targeted micro-actuation spray commands that minimize herbicide waste while providing localized yield forecasting heatmaps."
    ),
    (
        "AI-PS-06",
        "Context-Aware Retrieval-Augmented Generation (RAG) System for Complex Regulatory and Legal Auditing: "
        "Build a production-grade enterprise RAG auditing engine capable of parsing thousands of heterogeneous legal contracts, regulatory filings (SEC 10-K, GDPR, HIPAA), and compliance policies in PDF/DOCX formats. "
        "The system must implement hybrid dense-sparse hierarchical chunking, knowledge graph entity extraction, and multi-vector reranking to answer ambiguous statutory queries. "
        "It must guarantee zero hallucinations by enforcing strict sentence-level citation verification against ground-truth source documents, calculating semantic contradiction scores, highlighting governing clauses, and generating automated redline revision summaries for compliance attorneys."
    ),
    (
        "AI-PS-07",
        "Physics-Informed Neural Network (PINN) for Industrial Digital Twin and Predictive Maintenance: "
        "Develop a physics-informed deep learning system that models thermodynamic, vibration, and fluid dynamics degradation curves for high-value industrial machinery (e.g., wind turbines, gas compressors, CNC spindle bearings). "
        "By embedding partial differential equations (Navier-Stokes and heat diffusion) into the loss function, the neural network must extrapolate remaining useful life (RUL) with high fidelity even when training sensor data is scarce or noisy. "
        "The system must ingest high-frequency telemetry streams via MQTT/Kafka, trigger predictive maintenance alerts weeks prior to catastrophic component failure, and simulate optimal load distributions to maximize operational longevity."
    ),
    (
        "AI-PS-08",
        "Self-Supervised Video Representation Learning for Real-Time Anomaly and Hazard Detection in Smart Cities: "
        "Create a self-supervised spatio-temporal video understanding framework that ingests continuous feeds from municipal CCTV networks to autonomously detect emerging traffic collisions, pedestrian hazards, unauthorized intrusions, and public safety anomalies in real time without human supervision. "
        "The model must learn normative crowd and vehicular dynamics from unannotated video streams, recognize temporal boundary transitions, and flag deviations with high precision while actively suppressing false positives caused by weather variations, camera glare, or shadows. "
        "It must provide instantaneous spatial bounding alerts and anonymize bystander faces and license plates at the edge."
    ),
    (
        "AI-PS-09",
        "Explainable AI Financial Fraud and Credit Default Decision Engine with Algorithmic Fairness Constraints: "
        "Engineer a transparent, fair, and high-throughput credit underwriting and real-time payment fraud prevention platform leveraging ensemble gradient boosted trees and deep surrogate networks. "
        "The decision engine must generate counterfactual explanations and local Shapley additive explanations (SHAP) for every credit determination within 50 milliseconds. "
        "Crucially, the system must enforce strict algorithmic fairness constraints, mitigating disparate impact and demographic bias across protected socio-demographic attributes while maintaining an AUC-ROC above 0.94 on highly skewed, imbalanced fraud datasets."
    ),
    (
        "AI-PS-10",
        "Generative AI Synthetic Data Generation Platform with Verifiable Differential Privacy and Fidelity Guarantees: "
        "Construct a tabular and temporal synthetic data generation platform powered by conditional diffusion models and generative adversarial networks (CTGAN/TabDDPM). "
        "The platform must enable organizations to generate realistic, structurally identical synthetic datasets from sensitive healthcare, financial, and telecommunication records for machine learning development and third-party sharing. "
        "The generator must mathematically guarantee (epsilon, delta)-differential privacy against membership inference and attribute disclosure attacks, preserve statistical correlations and cross-column dependencies, and benchmark fidelity metrics (Wasserstein distance, empirical mutual information, and machine learning efficacy)."
    ),
]

CYBERSECURITY_PROBLEM_STATEMENTS = [
    (
        "CY-PS-01",
        "Automated Zero-Day Vulnerability Discovery and Exploit Mitigation Engine for Cloud-Native Binaries: "
        "Engineer an automated binary analysis and dynamic fuzzing framework tailored for containerized microservices and compiled ELF/PE executables. "
        "The system must combine coverage-guided symbolic execution, grammar-aware mutation fuzzing, and concolic testing to uncover memory corruption bugs (buffer overflows, use-after-free, integer underflows) and unvalidated inputs in critical services. "
        "Upon detecting an anomaly, the platform must automatically generate Proof-of-Concept exploit payloads in sandboxed environments to verify exploitability, construct software bill of materials (SBOM) vulnerability mappings, and synthesize virtual live-patches or eBPF filtering rules to neutralize vulnerabilities without restarting running containers."
    ),
    (
        "CY-PS-02",
        "Enterprise Zero Trust Network Access (ZTNA) with Continuous Micro-Segmentation and Behavioral Risk Scoring: "
        "Design and deploy a modern Zero Trust software-defined perimeter architecture that replaces traditional corporate VPNs with continuous, context-driven identity and device verification. "
        "The system must enforce dynamic micro-segmentation policies using mutual TLS (mTLS), hardware-backed device posture attestation (TPM/Secure Enclave checks), and continuous behavioral anomaly scoring (evaluating login telemetry, geo-velocity, keystroke dynamics, and network access patterns). "
        "If risk metrics breach configurable thresholds, the access controller must dynamically downgrade permissions, invoke step-up biometric multi-factor authentication, or isolate compromised endpoints in real time."
    ),
    (
        "CY-PS-03",
        "AI-Powered Autonomous Extended Detection and Response (XDR) with Automated Threat Hunting and Remediation: "
        "Build a centralized XDR analytics and response engine that correlates billions of heterogeneous security events across cloud workloads (AWS CloudTrail, GCP Audit Logs), host telemetry (Sysmon, OSquery, auditd), and network traffic sensors (Zeek, Suricata). "
        "The engine must implement sequence-to-sequence deep learning models and ATT&CK graph neural networks to reconstruct fragmented advanced persistent threat (APT) kill chains. "
        "It must execute automated SOAR response playbooks (isolating infected subnets, revoking OAuth session tokens, terminating malicious processes) within seconds of adversary detection, while generating threat hunting hypotheses and incident timelines for SOC analysts."
    ),
    (
        "CY-PS-04",
        "Cryptographically Secure Post-Quantum TLS 1.3 Proxy and Key Encapsulation Infrastructure: "
        "Develop a high-performance reverse proxy and cryptographic handshake termination gateway implementing NIST-standardized Post-Quantum Cryptography (PQC) algorithms (ML-KEM / Kyber for key encapsulation and ML-DSA / Dilithium for digital signatures) alongside hybrid classical elliptic-curve schemes (X25519-Kyber768). "
        "The proxy must inspect, decrypt, and forward high-throughput enterprise web traffic while securing data-in-transit against 'Harvest Now, Decrypt Later' quantum adversary campaigns. "
        "The solution must feature automated cryptographic algorithm agility, session resumption caching, side-channel attack mitigation, and comprehensive benchmarking of handshake latencies and certificate overheads."
    ),
    (
        "CY-PS-05",
        "Deception-Based Cyber Defense Architecture with Honeytoken Injection and Active Adversary Entrapment: "
        "Architect an intelligent deceptive defense platform that automatically provisions high-fidelity honeypots, decoy services (fake active directory domain controllers, phantom databases, synthetic Kubernetes clusters), and canary tokens across production infrastructure. "
        "The system must dynamically inject believable honey-credentials, SSH keys, AWS IAM tokens, and fake API secrets into workstation memory, code repositories, and filesystem caches. "
        "Upon adversary interaction with any deceptive asset, the platform must silently initiate forensic session packet capture, fingerprint adversary toolsets, feed false intelligence to delay adversary progression, and instantly trigger lockdown protocols across the real network."
    ),
    (
        "CY-PS-06",
        "Hardware-Rooted Firmware Integrity Attestation and Supply Chain Vulnerability Scanner: "
        "Construct a specialized firmware security assessment and attestation framework capable of analyzing UEFI, BIOS, BMC, and embedded IoT firmware images for malicious implants, backdoors, hardcoded private keys, and outdated components. "
        "The platform must perform automated firmware unpacking, static reverse engineering via Ghidra/radare2 APIs, binary diffing against known vendor golden baselines, and runtime emulation using QEMU to test peripheral interfaces. "
        "Furthermore, it must integrate cryptographic remote attestation leveraging hardware roots of trust (TPM 2.0 / DICE) to verify that boot sequences have not been tampered with by bootkits or hypervisor-level rootkits."
    ),
    (
        "CY-PS-07",
        "Next-Generation Web Application and API Security Gateway (WAAP) with Real-Time AST and Bot Defense: "
        "Create a high-throughput, low-latency Web Application and API Protection (WAAP) proxy that inspects REST, GraphQL, and gRPC traffic for OWASP API Top 10 vulnerabilities, including broken object level authorization (BOLA/IDOR), mass assignment, SQL/NoSQL injection, and credential stuffing. "
        "The gateway must combine Abstract Syntax Tree (AST) query inspection with unsupervised behavioral clustering to distinguish legitimate client traffic from sophisticated headless browser botnets. "
        "The system must enforce dynamic per-endpoint rate limits, validate OpenAPI specifications against live payload schemas, and decrypt encrypted traffic with zero noticeable latency impact (<5ms)."
    ),
    (
        "CY-PS-08",
        "Distributed Ransomware Early Warning and Immutable Storage Recovery Orchestrator: "
        "Build an endpoint and file server protection daemon designed to detect, halt, and reverse ransomware encryption activity before data loss occurs. "
        "The daemon must monitor kernel-level filesystem events (eBPF / Windows Filter Drivers) to track abnormal file modification entropy, rapid mass renames, canary file tampering, and volume shadow copy deletion attempts. "
        "Upon confirming ransomware behavior, the agent must instantly freeze culprit process trees, sever network communication to prevent command-and-control key exchange, and coordinate instant automated file rollback utilizing write-once-read-many (WORM) immutable snapshot storage mechanisms."
    ),
    (
        "CY-PS-09",
        "Advanced Phishing and Social Engineering Attack Surface Analyzer with Defensive LLM Guardrails: "
        "Engineer an advanced inbound email and communication security pipeline that combats modern generative-AI powered spear-phishing, business email compromise (BEC), and QR-code (quishing) attacks. "
        "The analyzer must inspect email headers for DKIM/SPF/DMARC anomalies, analyze domain age and visual similarity (punycode/typosquatting), and utilize fine-tuned language models to detect coercive psychological manipulation, urgency indicators, and synthetic writing patterns. "
        "The platform must dynamically detonate embedded attachments and hyperlinks in headless sandboxes, inspect landing pages for brand impersonation, and rewrite outbound suspicious links with real-time browser isolation redirects."
    ),
    (
        "CY-PS-10",
        "Automated Cloud Security Posture Management (CSPM) and Infrastructure-as-Code (IaC) Compliance Engine: "
        "Construct an automated multi-cloud compliance and misconfiguration remediation engine targeting AWS, Azure, and Google Cloud environments. "
        "The platform must ingest Terraform, CloudFormation, and Kubernetes manifests during CI/CD pipelines to prevent security debt before deployment, while continuously scanning live cloud API control planes for drift, overly permissive IAM roles, publicly exposed S3/storage buckets, unencrypted databases, and unsegmented VPCs. "
        "The engine must map cloud risks directly to SOC 2, ISO 27001, and CIS Benchmarks, calculate blast-radius risk vectors, and offer automated one-click remediation pull requests and CLI patches."
    ),
]


def seed_domains(db) -> dict:
    """Create domains if they don't exist. Returns {name: Domain} mapping."""
    domain_map = {}
    for d in DOMAINS:
        existing = db.query(Domain).filter(Domain.name == d["name"]).first()
        if not existing:
            domain = Domain(name=d["name"], description=d["description"])
            db.add(domain)
            db.flush()
            print(f"  [OK] Created domain: {d['name']}")
            domain_map[d["name"]] = domain
        else:
            print(f"  - Domain already exists: {d['name']}")
            domain_map[d["name"]] = existing
    return domain_map


def seed_admin(db, domain_map: dict) -> None:
    """Create the initial admin account if it doesn't exist."""
    existing = db.query(User).filter(User.username == settings.ADMIN_USERNAME).first()
    if existing:
        print(f"  - Admin already exists: {settings.ADMIN_USERNAME}")
        return

    admin = User(
        name=settings.ADMIN_NAME,
        username=settings.ADMIN_USERNAME,
        email=settings.ADMIN_EMAIL,
        password_hash=hash_password(settings.ADMIN_PASSWORD),
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
        domain_id=None,  # Admins have no domain
    )
    db.add(admin)
    print(f"  [OK] Created admin: {settings.ADMIN_USERNAME}")


def clean_legacy_topics(db) -> None:
    """Clean up legacy topics and topic locks to enforce fixed problem statement architecture."""
    try:
        # Clear topic_locks
        db.execute(text("DELETE FROM team_topic_locks;"))
        # Unset topic_id in projects
        db.execute(text("UPDATE projects SET topic_id = NULL WHERE topic_id IS NOT NULL;"))
        # Delete topics
        db.execute(text("DELETE FROM topics;"))
        db.flush()
        print("  [OK] Cleaned legacy topics and locks.")
    except Exception as e:
        print(f"  [WARN] Legacy cleanup notice: {e}")


def seed_problem_statements(db, domain_map: dict) -> None:
    """Seed exactly 10 AI and 10 Cybersecurity problem statements."""
    ai_domain = domain_map.get(DomainName.AI.value)
    cyber_domain = domain_map.get(DomainName.CYBERSECURITY.value)

    # 1. AI Problem Statements
    for code, desc in AI_PROBLEM_STATEMENTS:
        existing = db.query(ProblemStatement).filter(ProblemStatement.problem_code == code).first()
        if not existing:
            ps = ProblemStatement(
                problem_code=code,
                domain_id=ai_domain.id,
                detailed_description=desc,
                is_assigned=False,
            )
            db.add(ps)
        else:
            existing.detailed_description = desc
            existing.domain_id = ai_domain.id

    # 2. Cybersecurity Problem Statements
    for code, desc in CYBERSECURITY_PROBLEM_STATEMENTS:
        existing = db.query(ProblemStatement).filter(ProblemStatement.problem_code == code).first()
        if not existing:
            ps = ProblemStatement(
                problem_code=code,
                domain_id=cyber_domain.id,
                detailed_description=desc,
                is_assigned=False,
            )
            db.add(ps)
        else:
            existing.detailed_description = desc
            existing.domain_id = cyber_domain.id

    db.flush()

    ai_count = db.query(ProblemStatement).filter(ProblemStatement.domain_id == ai_domain.id).count()
    cyber_count = db.query(ProblemStatement).filter(ProblemStatement.domain_id == cyber_domain.id).count()
    oi_count = db.query(ProblemStatement).join(Domain).filter(Domain.name == DomainName.OPEN_INNOVATION.value).count()

    print(f"  [OK] Seeded problem statements: AI={ai_count}, Cybersecurity={cyber_count}, Open Innovation={oi_count}")


def seed_sample_users(db, domain_map: dict) -> None:
    """Create sample student users for each domain and assign initial problem statements."""
    ai_domain = domain_map.get(DomainName.AI.value)
    cyber_domain = domain_map.get(DomainName.CYBERSECURITY.value)
    oi_domain = domain_map.get(DomainName.OPEN_INNOVATION.value)

    sample_users = [
        ("Team Alpha AI", "alice_ai", "alice@example.com", DomainName.AI.value, "+1-555-0101", "MIT Tech", "Alice Chen", "David Zhang", "Emily Watson", "Frank Castle", "Computer Science", "2025-2026"),
        ("Team Cyber Shield", "bob_cyber", "bob@example.com", DomainName.CYBERSECURITY.value, "+1-555-0102", "Stanford Univ", "Bob Miller", "Grace Hopper", "Hannah Abbott", "Ian Malcolm", "Information Security", "2025-2026"),
        ("Team Nexus OI", "carol_oi", "carol@example.com", DomainName.OPEN_INNOVATION.value, "+1-555-0103", "Harvard Labs", "Carol Davis", "James Potter", "Lily Evans", None, "Innovation & Tech", "2025-2026"),
    ]

    for team_name, uname, email, dname, phone, org, leader, m1, m2, m3, dept, yr in sample_users:
        user = db.query(User).filter(User.username == uname).first()
        domain = domain_map.get(dname)
        if not user:
            user = User(
                name=team_name,
                team_name=team_name,
                team_leader=leader,
                member_one=m1,
                member_two=m2,
                member_three=m3,
                college_name=org,
                organization=org,
                department=dept,
                academic_year=yr,
                username=uname,
                email=email,
                password_hash=hash_password("UserPassword123!"),
                role=UserRole.USER,
                status=UserStatus.ACTIVE,
                domain_id=domain.id if domain else None,
                phone=phone,
            )
            db.add(user)
            db.flush()
            print(f"  [OK] Created sample team: {team_name} ({uname})")
        else:
            if not user.team_name:
                user.team_name = team_name
                user.team_leader = leader
                user.member_one = m1
                user.member_two = m2
                user.member_three = m3
                user.college_name = org
                user.department = dept
                user.academic_year = yr

        # Check or create project with assigned problem statement
        project = db.query(Project).filter(Project.user_id == user.id).first()
        if not project:
            assigned_ps_id = None
            assigned_ps_code = None
            assigned_ps_desc = None
            if dname in (DomainName.AI.value, DomainName.CYBERSECURITY.value):
                statements = db.query(ProblemStatement).filter(ProblemStatement.domain_id == domain.id).all()
                if statements:
                    chosen = random.choice(statements)
                    assigned_ps_id = chosen.id
                    assigned_ps_code = chosen.problem_code
                    assigned_ps_desc = chosen.detailed_description
                    chosen.is_assigned = True
                    chosen.assigned_team_id = user.id

            prefix = "AI" if dname == DomainName.AI.value else ("CY" if dname == DomainName.CYBERSECURITY.value else "OI")
            p_code = f"PRJ-{prefix}-{user.id:04d}"

            project = Project(
                project_code=p_code,
                user_id=user.id,
                domain_id=domain.id,
                assigned_problem_statement_id=assigned_ps_id,
                project_title=f"{assigned_ps_code} Solution Project" if assigned_ps_code else f"{team_name} Project",
                problem_statement=assigned_ps_desc if assigned_ps_desc else "Custom project innovation statement.",
                status=ProjectStatus.DRAFT,
                is_submitted=False,
            )
            db.add(project)
            print(f"  [OK] Initialized project for {uname} with {assigned_ps_code or 'custom title'}")
        else:
            # If project exists but lacks assigned_problem_statement_id for AI/Cyber, assign one
            if dname in (DomainName.AI.value, DomainName.CYBERSECURITY.value) and not project.assigned_problem_statement_id:
                statements = db.query(ProblemStatement).filter(ProblemStatement.domain_id == domain.id).all()
                if statements:
                    chosen = random.choice(statements)
                    project.assigned_problem_statement_id = chosen.id
                    project.problem_statement = chosen.detailed_description
                    chosen.is_assigned = True
                    chosen.assigned_team_id = user.id
                    print(f"  [OK] Assigned {chosen.problem_code} to existing project for {uname}")


def seed_bulk_users_inline(db, domain_map: dict) -> None:
    """Seed 40 test users across all domains (idempotent — skips existing)."""
    from app.core.security import hash_password

    TEST_USERS = [
        # AI domain (14)
        ("Team NeuralNexus",    "team_neuralnexus",    "neuralnexus@test.com",    "AI",            "Arjun Sharma",    "Priya Nair",      "Rohit Das",     "Sneha Pillai",  "IIT Bombay",         "Computer Science",    "2025-2026"),
        ("Team DeepMind Delta", "team_deepmind_delta", "deepminddelta@test.com",  "AI",            "Kiran Mehta",     "Anjali Verma",    "Suresh Reddy",  "Divya Rajan",   "IIT Delhi",          "AI and ML",           "2025-2026"),
        ("Team AlphaWave",      "team_alphawave",      "alphawave@test.com",      "AI",            "Vikram Singh",    "Pooja Mishra",    "Ankit Gupta",   "Riya Kapoor",   "NIT Trichy",         "Data Science",        "2025-2026"),
        ("Team VisionCore",     "team_visioncore",     "visioncore@test.com",     "AI",            "Rahul Patel",     "Meena Iyer",      "Sanjay Kumar",  "Tara Bose",     "VIT Vellore",        "Computer Vision",     "2025-2026"),
        ("Team SynthIQ",        "team_synthiq",        "synthiq@test.com",        "AI",            "Aditya Joshi",    "Kavitha Rao",     "Nikhil Menon",  None,            "BITS Pilani",        "Artificial Intel.",   "2025-2026"),
        ("Team LogicForge",     "team_logicforge",     "logicforge@test.com",     "AI",            "Harish Nambiar",  "Shruti Tiwari",   "Pranav Yadav",  "Lakshmi Pillai","SRM University",     "Machine Learning",    "2025-2026"),
        ("Team EdgeBrain",      "team_edgebrain",      "edgebrain@test.com",      "AI",            "Vinay Choudhary", "Deepa Krishnan",  "Manoj Patil",   "Nisha Sharma",  "Manipal University", "Computer Science",    "2025-2026"),
        ("Team OmegaAI",        "team_omegaai",        "omegaai@test.com",        "AI",            "Sandeep Ravi",    "Geeta Nair",      "Tarun Jain",    "Pallavi Mehta", "Anna University",    "AI and Robotics",     "2025-2026"),
        ("Team QuantumLeap",    "team_quantumleap",    "quantumleap@test.com",    "AI",            "Rajesh Kumar",    "Swathi Reddy",    "Aryan Bose",    None,            "Jadavpur University","Deep Learning",       "2025-2026"),
        ("Team NovaMind",       "team_novamind",       "novamind@test.com",       "AI",            "Varun Sharma",    "Asha Pillai",     "Ravi Teja",     "Shalini Gupta", "Amrita University",  "Neural Networks",     "2025-2026"),
        ("Team PulseCog",       "team_pulsecog",       "pulsecog@test.com",       "AI",            "Kiran Raj",       "Bhavna Iyer",     "Gaurav Singh",  "Nandita Das",   "PSG College",        "AI Engineering",      "2025-2026"),
        ("Team ZeroGravAI",     "team_zerogravai",     "zerogravai@test.com",     "AI",            "Mohit Verma",     "Chitra Menon",    "Lokesh Reddy",  "Ananya Rao",    "CEG Chennai",        "Computer Science",    "2025-2026"),
        ("Team FusionNet",      "team_fusionnet",      "fusionnet@test.com",      "AI",            "Suman Ghosh",     "Rekha Krishnan",  "Arun Pandey",   None,            "IIIT Hyderabad",     "ML and Data Science", "2025-2026"),
        ("Team NexusByte",      "team_nexusbyte",      "nexusbyte@test.com",      "AI",            "Dinesh Patel",    "Vandana Sharma",  "Sunil Mishra",  "Farah Khan",    "Thapar University",  "AI Research",         "2025-2026"),
        # Cybersecurity domain (13)
        ("Team CipherX",        "team_cipherx",        "cipherx@test.com",        "CYBERSECURITY", "Akash Dubey",     "Nandini Bose",    "Vasudev Rao",   "Preethi Nair",  "IIT Madras",         "Cybersecurity",       "2025-2026"),
        ("Team GhostNet",       "team_ghostnet",       "ghostnet@test.com",       "CYBERSECURITY", "Naveen Kumar",    "Soumya Das",      "Harshit Joshi", None,            "IIT Roorkee",        "Network Security",    "2025-2026"),
        ("Team PhantomByte",    "team_phantombyte",    "phantombyte@test.com",    "CYBERSECURITY", "Vivek Nair",      "Smitha Pillai",   "Deven Shah",    "Ritu Gupta",    "NIT Surathkal",      "Ethical Hacking",     "2025-2026"),
        ("Team IronShield",     "team_ironshield",     "ironshield@test.com",     "CYBERSECURITY", "Sriram Iyengar",  "Madhavi Iyer",    "Rohit Sinha",   "Kavya Menon",   "IIIT Bangalore",     "Cryptography",        "2025-2026"),
        ("Team DarkVector",     "team_darkvector",     "darkvector@test.com",     "CYBERSECURITY", "Suresh Babu",     "Gayathri Raj",    "Kiran Desai",   None,            "Amity University",   "Forensics",           "2025-2026"),
        ("Team ZeroDay",        "team_zeroday",        "zeroday@test.com",        "CYBERSECURITY", "Amar Srivastava", "Sunita Pandey",   "Yash Kapoor",   "Tanya Singh",   "Symbiosis Institute","Penetration Testing", "2025-2026"),
        ("Team SteelGuard",     "team_steelguard",     "steelguard@test.com",     "CYBERSECURITY", "Mahesh Iyer",     "Deepika Raman",   "Souvik Das",    "Arpita Roy",    "Manipal University", "Network Defence",     "2025-2026"),
        ("Team NullByte",       "team_nullbyte",       "nullbyte@test.com",       "CYBERSECURITY", "Rajan Pillai",    "Anitha Kumar",    "Dev Sharma",    None,            "SRM University",     "Cybersecurity",       "2025-2026"),
        ("Team ByteForce",      "team_byteforce",      "byteforce@test.com",      "CYBERSECURITY", "Praveen Reddy",   "Lalitha Menon",   "Shankar Rao",   "Isha Malhotra", "SASTRA University",  "Security Engineering","2025-2026"),
        ("Team HexHunter",      "team_hexhunter",      "hexhunter@test.com",      "CYBERSECURITY", "Ashwin Kumar",    "Yamini Naidu",    "Siddharth Roy", "Neha Agarwal",  "Karunya University", "Ethical Hacking",     "2025-2026"),
        ("Team FortressX",      "team_fortressx",      "fortressx@test.com",      "CYBERSECURITY", "Balaji Krishnan", "Padma Suresh",    "Nilesh Patil",  None,            "CIT Coimbatore",     "Cloud Security",      "2025-2026"),
        ("Team RedTeam9",       "team_redteam9",       "redteam9@test.com",       "CYBERSECURITY", "Surya Prakash",   "Jaya Lakshmi",    "Aditya Rout",   "Pooja Sharma",  "Chandigarh Univ.",   "Red Teaming",         "2025-2026"),
        ("Team VigilanceOps",   "team_vigilanceops",   "vigilanceops@test.com",   "CYBERSECURITY", "Ramesh Babu",     "Kavitha Srinivas","Girish Nair",   "Anjali Rathi",  "PESIT Bangalore",    "SOC Operations",      "2025-2026"),
        # Open Innovation domain (13)
        ("Team Ignite360",      "team_ignite360",      "ignite360@test.com",      "OPEN_INNOVATION","Aarav Shah",     "Ishaan Mehta",    "Disha Kapoor",  "Kriti Nair",    "DSCE Bangalore",     "Innovation Design",   "2025-2026"),
        ("Team VaultVision",    "team_vaultvision",    "vaultvision@test.com",    "OPEN_INNOVATION","Prakash Iyer",   "Sindhu Rajan",    "Alok Mishra",   None,            "GEC Thrissur",       "Product Design",      "2025-2026"),
        ("Team BlueSparks",     "team_bluesparks",     "bluesparks@test.com",     "OPEN_INNOVATION","Tejesh Kumar",   "Chaitra Reddy",   "Nitin Bhat",    "Ranjana Patel", "NITK Surathkal",     "Embedded Systems",    "2025-2026"),
        ("Team Tectonic",       "team_tectonic",       "tectonic@test.com",       "OPEN_INNOVATION","Gopal Shankar",  "Preethi Menon",   "Suhas Rao",     "Bhoomika Jain", "BIT Mesra",          "Emerging Tech",       "2025-2026"),
        ("Team SolarFlux",      "team_solarflux",      "solarflux@test.com",      "OPEN_INNOVATION","Aryan Verma",    "Roshni Pillai",   "Tushar Sinha",  None,            "DAIICT Gandhinagar", "Green Technology",    "2025-2026"),
        ("Team PixelPulse",     "team_pixelpulse",     "pixelpulse@test.com",     "OPEN_INNOVATION","Mithun Raj",     "Lakshanya Iyer",  "Yash Dubey",    "Swathi Pillai", "SIT Tumkur",         "UX and Design",       "2025-2026"),
        ("Team StormCell",      "team_stormcell",      "stormcell@test.com",      "OPEN_INNOVATION","Deepak Sharma",  "Archana Reddy",   "Jayesh Patel",  "Shreya Gupta",  "RIT Bangalore",      "IoT Systems",         "2025-2026"),
        ("Team EchoLabs",       "team_echolabs",       "echolabs@test.com",       "OPEN_INNOVATION","Santhosh Kumar", "Vidya Nair",      "Prashant Roy",  None,            "JSSATE Bangalore",   "Product Development", "2025-2026"),
        ("Team TitanX",         "team_titanx",         "titanx@test.com",         "OPEN_INNOVATION","Raghavendra Rao","Uma Shankar",     "Kiran Pillai",  "Divya Sharma",  "MVJ College",        "Robotics",            "2025-2026"),
        ("Team AuraFlow",       "team_auraflow",       "auraflow@test.com",       "OPEN_INNOVATION","Shiva Prasad",   "Nalini Krishnan", "Bhuvan Raj",    "Parvathy Iyer", "RNSIT Bangalore",    "AR VR Technology",    "2025-2026"),
        ("Team NovaSpark",      "team_novaspark",      "novaspark@test.com",      "OPEN_INNOVATION","Abhishek Jain",  "Kavya Pillai",    "Santosh Das",   None,            "BMS College",        "Smart Systems",       "2025-2026"),
        ("Team CodeBridge",     "team_codebridge",     "codebridge@test.com",     "OPEN_INNOVATION","Venkatesh Rao",  "Sridevi Menon",   "Mohan Lal",     "Geeta Singh",   "Nitte University",   "Software Innovation", "2025-2026"),
        ("Team WarpDrive",      "team_warpdrive",      "warpdrive@test.com",      "OPEN_INNOVATION","Jayant Kumar",   "Kamala Nair",     "Srihari Bhat",  "Anushka Rao",   "Presidency College", "Future Tech",         "2025-2026"),
    ]

    created = 0
    for (name, username, email, dname, leader, m1, m2, m3, college, dept, yr) in TEST_USERS:
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            continue
        suffix = username.replace("team_", "").capitalize()
        password = f"Pass@{suffix}2025"
        domain = domain_map.get(dname)
        user = User(
            name=name, username=username, email=email,
            password_hash=hash_password(password),
            role=UserRole.USER, status=UserStatus.ACTIVE,
            domain_id=domain.id if domain else None,
            team_name=name, team_leader=leader,
            member_one=m1, member_two=m2, member_three=m3,
            college_name=college, organization=college,
            department=dept, academic_year=yr,
        )
        db.add(user)
        db.flush()
        created += 1
    print(f"  [OK] Bulk users: {created} created (rest already existed).")


def main():
    print("\n Starting database initialization and seed process...")
    from app.database.database import engine
    from app.database.base import Base
    from app.database.migration import auto_migrate_schema
    import app.models  # noqa: F401

    print("\n[0/4] Ensuring database schema and columns are up to date...")
    auto_migrate_schema(engine)
    print("  [OK] Database schema initialized and migrated.")

    db = SessionLocal()
    try:
        print("\n[1/4] Seeding domains...")
        domain_map = seed_domains(db)

        print("\n[2/4] Cleaning legacy topics...")
        clean_legacy_topics(db)

        print("\n[3/4] Seeding predefined problem statements (10 AI, 10 Cyber, 0 OI)...")
        seed_problem_statements(db, domain_map)

        print("\n[4/4] Seeding admin account...")
        seed_admin(db, domain_map)

        print("\n[5/4] Seeding 40 bulk test users...")
        seed_bulk_users_inline(db, domain_map)

        db.commit()
        print("\n[SUCCESS] Seed completed successfully!\n")
        print(f"   Admin username : {settings.ADMIN_USERNAME}")
        print(f"   Admin password : {settings.ADMIN_PASSWORD}")
        print(f"   Test users     : 40 users seeded (see test_credentials.txt)")
        print(f"   API docs       : http://localhost:8000/docs\n")
    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
