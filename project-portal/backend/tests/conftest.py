"""
Pytest configuration and shared fixtures.

Uses a separate SQLite test database so tests never touch production PostgreSQL.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
from app.database.database import get_db
from app.main import app
from app.core.security import hash_password
from app.models.domain import Domain, DomainName
from app.models.user import User, UserRole, UserStatus
from app.models.topic import Topic
from app.models.project import Project, ProjectStatus
from app.models.review import Review

# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite:///./test_portal.db"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    """Create all tables once per test session."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()
    import os
    if os.path.exists("test_portal.db"):
        try:
            os.remove("test_portal.db")
        except OSError:
            pass


@pytest.fixture(autouse=True)
def clean_db():
    """Truncate all data between tests."""
    yield
    db = TestingSessionLocal()
    try:
        from app.models.topic_lock import TeamTopicLock
        db.query(TeamTopicLock).delete()
        db.query(Review).delete()
        db.query(Project).delete()
        db.query(Topic).delete()
        db.query(User).delete()
        db.query(Domain).delete()
        db.commit()
    finally:
        db.close()


@pytest.fixture
def db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    return TestClient(app)


# ─── Domain fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def domains(db):
    ai = Domain(name=DomainName.AI.value, description="AI domain")
    cyber = Domain(name=DomainName.CYBERSECURITY.value, description="Cybersecurity domain")
    oi = Domain(name=DomainName.OPEN_INNOVATION.value, description="Open Innovation domain")
    db.add_all([ai, cyber, oi])
    db.commit()
    db.refresh(ai)
    db.refresh(cyber)
    db.refresh(oi)
    return {"ai": ai, "cyber": cyber, "oi": oi}


# ─── User fixtures ────────────────────────────────────────────────────────────

@pytest.fixture
def admin_user(db, domains):
    admin = User(
        name="Admin User",
        username="admin",
        email="admin@test.com",
        password_hash=hash_password("adminpass123"),
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
        domain_id=None,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


@pytest.fixture
def ai_user(db, domains):
    user = User(
        name="AI User",
        username="aiuser",
        email="ai@test.com",
        password_hash=hash_password("userpass123"),
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
        domain_id=domains["ai"].id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def cyber_user(db, domains):
    user = User(
        name="Cyber User",
        username="cyberuser",
        email="cyber@test.com",
        password_hash=hash_password("userpass123"),
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
        domain_id=domains["cyber"].id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def oi_user(db, domains):
    user = User(
        name="OI User",
        username="oiuser",
        email="oi@test.com",
        password_hash=hash_password("userpass123"),
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
        domain_id=domains["oi"].id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def inactive_user(db, domains):
    user = User(
        name="Inactive User",
        username="inactive",
        email="inactive@test.com",
        password_hash=hash_password("userpass123"),
        role=UserRole.USER,
        status=UserStatus.INACTIVE,
        domain_id=domains["ai"].id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ─── Topic fixtures ───────────────────────────────────────────────────────────

@pytest.fixture
def ai_topics(db, domains):
    """Create 15 active AI topics."""
    titles = [
        "Machine Learning", "Deep Learning", "Generative AI", "Computer Vision",
        "Natural Language Processing", "AI Agents", "Reinforcement Learning",
        "Explainable AI", "Edge AI", "AI in Healthcare", "Speech Recognition",
        "Recommendation Systems", "Multimodal AI", "Robotics and AI", "Large Language Models",
    ]
    topics = [
        Topic(title=t, description=f"Description for {t}", domain_id=domains["ai"].id, is_active=True)
        for t in titles
    ]
    db.add_all(topics)
    db.commit()
    for t in topics:
        db.refresh(t)
    return topics


@pytest.fixture
def cyber_topics(db, domains):
    """Create 15 active Cybersecurity topics."""
    titles = [
        "Network Security", "Cloud Security", "IoT Security", "Application Security",
        "Digital Forensics", "Threat Intelligence", "Malware Analysis", "Cryptography",
        "Ethical Hacking", "Zero Trust", "Intrusion Detection", "Security Operations",
        "Identity and Access Management", "Mobile Security", "Web Security",
    ]
    topics = [
        Topic(title=t, description=f"Description for {t}", domain_id=domains["cyber"].id, is_active=True)
        for t in titles
    ]
    db.add_all(topics)
    db.commit()
    for t in topics:
        db.refresh(t)
    return topics


# ─── Auth token helpers ───────────────────────────────────────────────────────

def get_token(client, username: str, password: str) -> str:
    resp = client.post("/api/auth/login", json={"username": username, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]["access_token"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
