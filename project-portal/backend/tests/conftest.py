"""
Pytest configuration and shared fixtures for Hogwarts Legacy 5.0.

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
from app.models.problem_statement import ProblemStatement, RealmEnum, DifficultyEnum
from app.models.project import Project, ProjectStatus
from app.models.review import Review

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
        db.query(Review).delete()
        db.query(Project).delete()
        db.query(ProblemStatement).delete()
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
    db.add_all([ai, cyber])
    db.commit()
    db.refresh(ai)
    db.refresh(cyber)

    # Seed at least one default problem statement per realm
    from app.models.problem_statement import ProblemStatement, RealmEnum, DifficultyEnum
    ps_ai = ProblemStatement(
        problem_code="AI-PS-01",
        realm=RealmEnum.AI,
        title="AI Default Problem",
        description="Default AI Description for testing",
        difficulty=DifficultyEnum.INTERMEDIATE,
        status=True,
    )
    ps_cy = ProblemStatement(
        problem_code="CY-PS-01",
        realm=RealmEnum.CYBERSECURITY,
        title="Cyber Default Problem",
        description="Default Cyber Description for testing",
        difficulty=DifficultyEnum.INTERMEDIATE,
        status=True,
    )
    db.add_all([ps_ai, ps_cy])
    db.commit()

    return {"ai": ai, "cyber": cyber}


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
def ai_problem_statements(db):
    """Seed 10 AI problem statements."""
    statements = []
    for i in range(1, 11):
        code = f"AI-PS-{i:02d}"
        s = db.query(ProblemStatement).filter(ProblemStatement.problem_code == code).first()
        if not s:
            s = ProblemStatement(
                problem_code=code,
                realm=RealmEnum.AI,
                title=f"AI Challenge {i}",
                description=f"Detailed technical description for AI problem statement {i}",
                difficulty=DifficultyEnum.INTERMEDIATE,
                status=True,
            )
            db.add(s)
            db.commit()
            db.refresh(s)
        statements.append(s)
    return statements


@pytest.fixture
def cyber_problem_statements(db):
    """Seed 10 Cybersecurity problem statements."""
    statements = []
    for i in range(1, 11):
        code = f"CY-PS-{i:02d}"
        s = db.query(ProblemStatement).filter(ProblemStatement.problem_code == code).first()
        if not s:
            s = ProblemStatement(
                problem_code=code,
                realm=RealmEnum.CYBERSECURITY,
                title=f"Cyber Challenge {i}",
                description=f"Detailed technical description for Cybersecurity problem statement {i}",
                difficulty=DifficultyEnum.ADVANCED,
                status=True,
            )
            db.add(s)
            db.commit()
            db.refresh(s)
        statements.append(s)
    return statements


@pytest.fixture
def ai_user(db, domains, ai_problem_statements):
    user = User(
        name="AI User",
        team_name="AI Team",
        team_leader="Alice",
        member_one="Bob",
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

    ps = ai_problem_statements[0]
    project = Project(
        project_code="PRJ-AI-0001",
        user_id=user.id,
        domain_id=domains["ai"].id,
        problem_statement_id=ps.id,
        problem_code=ps.problem_code,
        realm=ps.realm,
        project_title=f"{ps.problem_code} Solution Project",
        problem_statement=ps.description,
        status=ProjectStatus.DRAFT,
        is_submitted=False,
    )
    db.add(project)
    db.commit()
    return user


@pytest.fixture
def cyber_user(db, domains, cyber_problem_statements):
    user = User(
        name="Cyber User",
        team_name="Cyber Team",
        team_leader="Carol",
        member_one="Dave",
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

    ps = cyber_problem_statements[0]
    project = Project(
        project_code="PRJ-CY-0001",
        user_id=user.id,
        domain_id=domains["cyber"].id,
        problem_statement_id=ps.id,
        problem_code=ps.problem_code,
        realm=ps.realm,
        project_title=f"{ps.problem_code} Solution Project",
        problem_statement=ps.description,
        status=ProjectStatus.DRAFT,
        is_submitted=False,
    )
    db.add(project)
    db.commit()
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


# ─── Auth token helpers ───────────────────────────────────────────────────────

def get_token(client, username: str, password: str) -> str:
    resp = client.post("/api/auth/login", json={"username": username, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]["access_token"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
