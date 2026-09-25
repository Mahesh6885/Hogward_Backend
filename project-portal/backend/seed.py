"""
Seed script — safe to run multiple times (idempotent).

Production-safe database seeding for Hogwarts Legacy 5.0 on Render + PostgreSQL.
Populates:
1. Domains (AI and CYBERSECURITY)
2. Initial admin account
3. Exactly 20 Official Hogwarts Legacy 5.0 Problem Statements:
   - 10 AI Problem Statements (AI-PS-01 to AI-PS-10)
   - 10 Cybersecurity Problem Statements (CY-PS-01 to CY-PS-10)
   With official codes, titles, full descriptions, difficulties, and active status.
"""
import os
import sys

# Ensure backend directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.core.config import settings
from app.core.security import hash_password
from app.database.database import SessionLocal, engine
from app.database.migration import auto_migrate_schema
from app.models.domain import Domain, DomainName
from app.models.user import User, UserRole, UserStatus
from app.models.problem_statement import ProblemStatement, RealmEnum, DifficultyEnum

DOMAINS = [
    {
        "name": DomainName.AI.value,
        "description": "Artificial Intelligence — covers machine learning, deep learning, NLP, computer vision, and more.",
    },
    {
        "name": DomainName.CYBERSECURITY.value,
        "description": "Cybersecurity — covers network security, ethical hacking, cryptography, forensics, and more.",
    },
]

OFFICIAL_PROBLEM_STATEMENTS = [
    # ── AI Realm (10) ────────────────────────────────────────────────────────
    {
        "problem_code": "AI-PS-01",
        "realm": RealmEnum.AI,
        "title": "Multi-Modal Clinical Diagnostic Assistant for Radiology and Electronic Health Records",
        "description": (
            "Build an end-to-end multi-modal diagnostic reasoning engine that combines chest X-ray/CT radiograph imagery "
            "with structured Electronic Health Record (EHR) data and unstructured doctor clinical notes. "
            "The system must process DICOM/PNG images using vision transformers alongside patient vitals, pathology records, "
            "and historical admissions. It must accurately localize pulmonary lesions and cardiac abnormalities with attention "
            "heatmaps (Grad-CAM) while synthesizing clinically interpretable diagnostic summaries. "
            "The engine must strictly adhere to differential diagnostic protocols, automatically flag adverse drug-allergy interactions, "
            "quantify predictive uncertainty, and provide verifiable citations to established clinical medical ontologies "
            "(e.g., SNOMED CT and ICD-10) without hallucinating phantom conditions or unverified symptoms."
        ),
        "difficulty": DifficultyEnum.ADVANCED,
    },
    {
        "problem_code": "AI-PS-02",
        "realm": RealmEnum.AI,
        "title": "Autonomous Multi-Agent Collaborative Task Orchestration and Verification Framework",
        "description": (
            "Design and deploy a resilient multi-agent orchestration architecture capable of decomposing complex, "
            "ambiguously phrased software engineering and business workflow requests into verifiable sub-goals. "
            "The system must coordinate specialized autonomous agents (planner, coder, verifier, and security auditor) "
            "with strict contract validation, dynamic replanning on tool failures, and cyclic dependency resolution. "
            "It must incorporate long-term vector memory caching with semantic deduplication, deterministic human-in-the-loop "
            "intervention checkpoints, rate-limiting guards against infinite recursive loops, and structured audit telemetry "
            "tracing agent communication graphs and token expenditures."
        ),
        "difficulty": DifficultyEnum.ADVANCED,
    },
    {
        "problem_code": "AI-PS-03",
        "realm": RealmEnum.AI,
        "title": "Real-Time Multilingual Speech-to-Speech Translation with Zero-Shot Voice Cloning",
        "description": (
            "Develop an edge-deployable, low-latency streaming pipeline that captures spoken dialectal audio, "
            "performs streaming speech recognition, translates across non-English low-resource languages, and synthesizes "
            "output speech that preserves the speaker's original emotional intonation, cadence, and vocal timbre using "
            "zero-shot neural voice cloning. The pipeline must operate with an end-to-end glass-to-glass latency under 600ms, "
            "incorporate acoustic echo cancellation and background denoising algorithms, handle code-mixed conversational inputs "
            "(such as Spanglish or Hinglish), and generate synchronized lip-motion landmarks for video streaming integration."
        ),
        "difficulty": DifficultyEnum.INTERMEDIATE,
    },
    {
        "problem_code": "AI-PS-04",
        "realm": RealmEnum.AI,
        "title": "Privacy-Preserving Federated Graph Neural Network for Anti-Money Laundering",
        "description": (
            "Construct a decentralized, privacy-preserving financial forensics system using federated graph neural networks (FedGNN) "
            "across partitioned banking institutions without centralizing sensitive customer transaction logs. "
            "The platform must model multi-hop entity graphs to detect illicit structuring, wash trading, and synthetic identity rings "
            "traversing disparate banking ledgers. The framework must implement differential privacy mechanisms and secure multi-party "
            "computation (SMPC) to prevent gradient inversion attacks, ensure sub-second graph inference on real-time transaction "
            "streams, and generate automated regulatory Suspicious Activity Reports (SAR) with explainable sub-graph visualizations."
        ),
        "difficulty": DifficultyEnum.ADVANCED,
    },
    {
        "problem_code": "AI-PS-05",
        "realm": RealmEnum.AI,
        "title": "High-Precision Edge Computer Vision for Autonomous Precision Agriculture and Crop Disease Prognosis",
        "description": (
            "Architect an offline-capable, lightweight deep learning computer vision pipeline designed for deployment on constrained "
            "edge hardware mounted on autonomous agricultural drones or tractors. The system must execute real-time multi-spectral "
            "leaf disease segmentation, weeds vs. crop classification, and soil moisture estimation under fluctuating natural illumination, "
            "partial occlusions, and severe camera jitter. The solution must feature automated quantization (INT8/FP16), model pruning to "
            "maintain 30+ FPS, and trigger targeted micro-actuation spray commands that minimize herbicide waste while providing localized "
            "yield forecasting heatmaps."
        ),
        "difficulty": DifficultyEnum.INTERMEDIATE,
    },
    {
        "problem_code": "AI-PS-06",
        "realm": RealmEnum.AI,
        "title": "Context-Aware Retrieval-Augmented Generation (RAG) System for Complex Regulatory and Legal Auditing",
        "description": (
            "Build a production-grade enterprise RAG auditing engine capable of parsing thousands of heterogeneous legal contracts, "
            "regulatory filings (SEC 10-K, GDPR, HIPAA), and compliance policies in PDF/DOCX formats. The system must implement "
            "hybrid dense-sparse hierarchical chunking, knowledge graph entity extraction, and multi-vector reranking to answer ambiguous "
            "statutory queries. It must guarantee zero hallucinations by enforcing strict sentence-level citation verification against "
            "ground-truth source documents, calculating semantic contradiction scores, highlighting governing clauses, and generating automated "
            "redline revision summaries for compliance attorneys."
        ),
        "difficulty": DifficultyEnum.INTERMEDIATE,
    },
    {
        "problem_code": "AI-PS-07",
        "realm": RealmEnum.AI,
        "title": "Physics-Informed Neural Network (PINN) for Industrial Digital Twin and Predictive Maintenance",
        "description": (
            "Develop a physics-informed deep learning system that models thermodynamic, vibration, and fluid dynamics degradation curves "
            "for high-value industrial machinery (e.g., wind turbines, gas compressors, CNC spindle bearings). By embedding partial "
            "differential equations (Navier-Stokes and heat diffusion) into the loss function, the neural network must extrapolate remaining "
            "useful life (RUL) with high fidelity even when training sensor data is scarce or noisy. The system must ingest high-frequency "
            "telemetry streams via MQTT/Kafka, trigger predictive maintenance alerts weeks prior to catastrophic component failure, and simulate "
            "optimal load distributions to maximize operational longevity."
        ),
        "difficulty": DifficultyEnum.ADVANCED,
    },
    {
        "problem_code": "AI-PS-08",
        "realm": RealmEnum.AI,
        "title": "Self-Supervised Video Representation Learning for Real-Time Anomaly and Hazard Detection in Smart Cities",
        "description": (
            "Create a self-supervised spatio-temporal video understanding framework that ingests continuous feeds from municipal CCTV networks "
            "to autonomously detect emerging traffic collisions, pedestrian hazards, unauthorized intrusions, and public safety anomalies in real time "
            "without human supervision. The model must learn normative crowd and vehicular dynamics from unannotated video streams, recognize "
            "temporal boundary transitions, and flag deviations with high precision while actively suppressing false positives caused by weather "
            "variations, camera glare, or shadows. It must provide instantaneous spatial bounding alerts and anonymize bystander faces and license "
            "plates at the edge."
        ),
        "difficulty": DifficultyEnum.INTERMEDIATE,
    },
    {
        "problem_code": "AI-PS-09",
        "realm": RealmEnum.AI,
        "title": "Explainable AI Financial Fraud and Credit Default Decision Engine with Algorithmic Fairness Constraints",
        "description": (
            "Engineer a transparent, fair, and high-throughput credit underwriting and real-time payment fraud prevention platform leveraging "
            "ensemble gradient boosted trees and deep surrogate networks. The decision engine must generate counterfactual explanations and local "
            "Shapley additive explanations (SHAP) for every credit determination within 50 milliseconds. Crucially, the system must enforce strict "
            "algorithmic fairness constraints, mitigating disparate impact and demographic bias across protected socio-demographic attributes while "
            "maintaining an AUC-ROC above 0.94 on highly skewed, imbalanced fraud datasets."
        ),
        "difficulty": DifficultyEnum.ADVANCED,
    },
    {
        "problem_code": "AI-PS-10",
        "realm": RealmEnum.AI,
        "title": "Generative AI Synthetic Data Generation Platform with Verifiable Differential Privacy and Fidelity Guarantees",
        "description": (
            "Construct a tabular and temporal synthetic data generation platform powered by conditional diffusion models and generative "
            "adversarial networks (CTGAN/TabDDPM). The platform must enable organizations to generate realistic, structurally identical synthetic "
            "datasets from sensitive healthcare, financial, and telecommunication records for machine learning development and third-party sharing. "
            "The generator must mathematically guarantee (epsilon, delta)-differential privacy against membership inference and attribute disclosure "
            "attacks, preserve statistical correlations and cross-column dependencies, and benchmark fidelity metrics (Wasserstein distance, "
            "empirical mutual information, and machine learning efficacy)."
        ),
        "difficulty": DifficultyEnum.ADVANCED,
    },

    # ── Cybersecurity Realm (10) ─────────────────────────────────────────────
    {
        "problem_code": "CY-PS-01",
        "realm": RealmEnum.CYBERSECURITY,
        "title": "Automated Zero-Day Vulnerability Discovery and Exploit Mitigation Engine for Cloud-Native Binaries",
        "description": (
            "Engineer an automated binary analysis and dynamic fuzzing framework tailored for containerized microservices and compiled ELF/PE executables. "
            "The system must combine coverage-guided symbolic execution, grammar-aware mutation fuzzing, and concolic testing to uncover memory corruption "
            "bugs (buffer overflows, use-after-free, integer underflows) and unvalidated inputs in critical services. Upon detecting an anomaly, the platform "
            "must automatically generate Proof-of-Concept exploit payloads in sandboxed environments to verify exploitability, construct software bill of "
            "materials (SBOM) vulnerability mappings, and synthesize virtual live-patches or eBPF filtering rules to neutralize vulnerabilities without "
            "restarting running containers."
        ),
        "difficulty": DifficultyEnum.ADVANCED,
    },
    {
        "problem_code": "CY-PS-02",
        "realm": RealmEnum.CYBERSECURITY,
        "title": "Enterprise Zero Trust Network Access (ZTNA) with Continuous Micro-Segmentation and Behavioral Risk Scoring",
        "description": (
            "Design and deploy a modern Zero Trust software-defined perimeter architecture that replaces traditional corporate VPNs with continuous, "
            "context-driven identity and device verification. The system must enforce dynamic micro-segmentation policies using mutual TLS (mTLS), "
            "hardware-backed device posture attestation (TPM/Secure Enclave checks), and continuous behavioral anomaly scoring (evaluating login telemetry, "
            "geo-velocity, keystroke dynamics, and network access patterns). If risk metrics breach configurable thresholds, the access controller must "
            "dynamically downgrade permissions, invoke step-up biometric multi-factor authentication, or isolate compromised endpoints in real time."
        ),
        "difficulty": DifficultyEnum.INTERMEDIATE,
    },
    {
        "problem_code": "CY-PS-03",
        "realm": RealmEnum.CYBERSECURITY,
        "title": "AI-Powered Autonomous Extended Detection and Response (XDR) with Automated Threat Hunting and Remediation",
        "description": (
            "Build a centralized XDR analytics and response engine that correlates billions of heterogeneous security events across cloud workloads "
            "(AWS CloudTrail, GCP Audit Logs), host telemetry (Sysmon, OSquery, auditd), and network traffic sensors (Zeek, Suricata). The engine must "
            "implement sequence-to-sequence deep learning models and ATT&CK graph neural networks to reconstruct fragmented advanced persistent threat (APT) "
            "kill chains. It must execute automated SOAR response playbooks (isolating infected subnets, revoking OAuth session tokens, terminating malicious "
            "processes) within seconds of adversary detection, while generating threat hunting hypotheses and incident timelines for SOC analysts."
        ),
        "difficulty": DifficultyEnum.ADVANCED,
    },
    {
        "problem_code": "CY-PS-04",
        "realm": RealmEnum.CYBERSECURITY,
        "title": "Cryptographically Secure Post-Quantum TLS 1.3 Proxy and Key Encapsulation Infrastructure",
        "description": (
            "Develop a high-performance reverse proxy and cryptographic handshake termination gateway implementing NIST-standardized Post-Quantum "
            "Cryptography (PQC) algorithms (ML-KEM / Kyber for key encapsulation and ML-DSA / Dilithium for digital signatures) alongside hybrid classical "
            "elliptic-curve schemes (X25519-Kyber768). The proxy must inspect, decrypt, and forward high-throughput enterprise web traffic while securing "
            "data-in-transit against 'Harvest Now, Decrypt Later' quantum adversary campaigns. The solution must feature automated cryptographic algorithm "
            "agility, session resumption caching, side-channel attack mitigation, and comprehensive benchmarking of handshake latencies and certificate overheads."
        ),
        "difficulty": DifficultyEnum.ADVANCED,
    },
    {
        "problem_code": "CY-PS-05",
        "realm": RealmEnum.CYBERSECURITY,
        "title": "Deception-Based Cyber Defense Architecture with Honeytoken Injection and Active Adversary Entrapment",
        "description": (
            "Architect an intelligent deceptive defense platform that automatically provisions high-fidelity honeypots, decoy services (fake active directory "
            "domain controllers, phantom databases, synthetic Kubernetes clusters), and canary tokens across production infrastructure. The system must "
            "dynamically inject believable honey-credentials, SSH keys, AWS IAM tokens, and fake API secrets into workstation memory, code repositories, "
            "and filesystem caches. Upon adversary interaction with any deceptive asset, the platform must silently initiate forensic session packet capture, "
            "fingerprint adversary toolsets, feed false intelligence to delay adversary progression, and instantly trigger lockdown protocols across the real network."
        ),
        "difficulty": DifficultyEnum.INTERMEDIATE,
    },
    {
        "problem_code": "CY-PS-06",
        "realm": RealmEnum.CYBERSECURITY,
        "title": "Hardware-Rooted Firmware Integrity Attestation and Supply Chain Vulnerability Scanner",
        "description": (
            "Construct a specialized firmware security assessment and attestation framework capable of analyzing UEFI, BIOS, BMC, and embedded IoT firmware "
            "images for malicious implants, backdoors, hardcoded private keys, and outdated components. The platform must perform automated firmware unpacking, "
            "static reverse engineering via Ghidra/radare2 APIs, binary diffing against known vendor golden baselines, and runtime emulation using QEMU to test "
            "peripheral interfaces. Furthermore, it must integrate cryptographic remote attestation leveraging hardware roots of trust (TPM 2.0 / DICE) to verify "
            "that boot sequences have not been tampered with by bootkits or hypervisor-level rootkits."
        ),
        "difficulty": DifficultyEnum.ADVANCED,
    },
    {
        "problem_code": "CY-PS-07",
        "realm": RealmEnum.CYBERSECURITY,
        "title": "Next-Generation Web Application and API Security Gateway (WAAP) with Real-Time AST and Bot Defense",
        "description": (
            "Create a high-throughput, low-latency Web Application and API Protection (WAAP) proxy that inspects REST, GraphQL, and gRPC traffic for OWASP API "
            "Top 10 vulnerabilities, including broken object level authorization (BOLA/IDOR), mass assignment, SQL/NoSQL injection, and credential stuffing. "
            "The gateway must combine Abstract Syntax Tree (AST) query inspection with unsupervised behavioral clustering to distinguish legitimate client traffic "
            "from sophisticated headless browser botnets. The system must enforce dynamic per-endpoint rate limits, validate OpenAPI specifications against live "
            "payload schemas, and decrypt encrypted traffic with zero noticeable latency impact (<5ms)."
        ),
        "difficulty": DifficultyEnum.INTERMEDIATE,
    },
    {
        "problem_code": "CY-PS-08",
        "realm": RealmEnum.CYBERSECURITY,
        "title": "Distributed Ransomware Early Warning and Immutable Storage Recovery Orchestrator",
        "description": (
            "Build an endpoint and file server protection daemon designed to detect, halt, and reverse ransomware encryption activity before data loss occurs. "
            "The daemon must monitor kernel-level filesystem events (eBPF / Windows Filter Drivers) to track abnormal file modification entropy, rapid mass renames, "
            "canary file tampering, and volume shadow copy deletion attempts. Upon confirming ransomware behavior, the agent must instantly freeze culprit process "
            "trees, sever network communication to prevent command-and-control key exchange, and coordinate instant automated file rollback utilizing write-once-read-many "
            "(WORM) immutable snapshot storage mechanisms."
        ),
        "difficulty": DifficultyEnum.INTERMEDIATE,
    },
    {
        "problem_code": "CY-PS-09",
        "realm": RealmEnum.CYBERSECURITY,
        "title": "Advanced Phishing and Social Engineering Attack Surface Analyzer with Defensive LLM Guardrails",
        "description": (
            "Engineer an advanced inbound email and communication security pipeline that combats modern generative-AI powered spear-phishing, business email "
            "compromise (BEC), and QR-code (quishing) attacks. The analyzer must inspect email headers for DKIM/SPF/DMARC anomalies, analyze domain age and visual "
            "similarity (punycode/typosquatting), and utilize fine-tuned language models to detect coercive psychological manipulation, urgency indicators, and "
            "synthetic writing patterns. The platform must dynamically detonate embedded attachments and hyperlinks in headless sandboxes, inspect landing pages for "
            "brand impersonation, and rewrite outbound suspicious links with real-time browser isolation redirects."
        ),
        "difficulty": DifficultyEnum.BEGINNER,
    },
    {
        "problem_code": "CY-PS-10",
        "realm": RealmEnum.CYBERSECURITY,
        "title": "Automated Cloud Security Posture Management (CSPM) and Infrastructure-as-Code (IaC) Compliance Engine",
        "description": (
            "Construct an automated multi-cloud compliance and misconfiguration remediation engine targeting AWS, Azure, and Google Cloud environments. "
            "The platform must ingest Terraform, CloudFormation, and Kubernetes manifests during CI/CD pipelines to prevent security debt before deployment, while "
            "continuously scanning live cloud API control planes for drift, overly permissive IAM roles, publicly exposed S3/storage buckets, unencrypted databases, "
            "and unsegmented VPCs. The engine must map cloud risks directly to SOC 2, ISO 27001, and CIS Benchmarks, calculate blast-radius risk vectors, and offer "
            "automated one-click remediation pull requests and CLI patches."
        ),
        "difficulty": DifficultyEnum.INTERMEDIATE,
    },
]


def seed_domains(db) -> dict:
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
            domain_map[d["name"]] = existing
    return domain_map


def seed_admin(db) -> None:
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
        domain_id=None,
    )
    db.add(admin)
    db.flush()
    print(f"  [OK] Created admin: {settings.ADMIN_USERNAME}")


def seed_problem_statements(db) -> None:
    """Idempotently seed exactly 20 official Hogwarts Legacy 5.0 problem statements from the official PDF."""
    from app.services.pdf_import_service import import_official_statements
    res = import_official_statements(db)
    print(f"  [OK] Seeded official problem statements: Total={res['total']} (AI={res['ai_count']}, CY={res['cybersecurity_count']})")


def main():
    print("\n Starting production-safe PostgreSQL database migration and seed...")
    auto_migrate_schema(engine)

    db = SessionLocal()
    try:
        print("\n[1/3] Seeding domains (AI & CYBERSECURITY)...")
        seed_domains(db)

        print("\n[2/3] Seeding admin account...")
        seed_admin(db)

        print("\n[3/3] Seeding 20 Official Hogwarts Legacy 5.0 Problem Statements...")
        seed_problem_statements(db)

        db.commit()
        print("\n[SUCCESS] Production-safe PostgreSQL seed completed successfully!\n")
    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
