import random
import uuid
from typing import Optional, List, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from app.models.problem_statement import ProblemStatement, RealmEnum, DifficultyEnum
from app.models.project import Project
from app.models.user import User
from app.models.audit_log import AuditLog
from app.schemas.problem_statement import ProblemStatementCreate, ProblemStatementUpdate


def get_problem_statements(
    db: Session,
    realm: Optional[RealmEnum] = None,
    difficulty: Optional[DifficultyEnum] = None,
    status_filter: Optional[bool] = None,
    search: Optional[str] = None,
) -> List[ProblemStatement]:
    """Retrieve problem statements with optional filters for realm, difficulty, status, search."""
    query = db.query(ProblemStatement)

    if realm is not None:
        query = query.filter(ProblemStatement.realm == realm)
    if difficulty is not None:
        query = query.filter(ProblemStatement.difficulty == difficulty)
    if status_filter is not None:
        query = query.filter(ProblemStatement.status == status_filter)
    if search:
        pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                ProblemStatement.problem_code.ilike(pattern),
                ProblemStatement.title.ilike(pattern),
                ProblemStatement.description.ilike(pattern),
            )
        )

    # Order by realm, then code
    return query.order_by(ProblemStatement.realm.asc(), ProblemStatement.problem_code.asc()).all()


def get_problem_statement_by_id(db: Session, ps_id: uuid.UUID) -> ProblemStatement:
    """Retrieve a single problem statement by UUID."""
    ps = db.query(ProblemStatement).filter(ProblemStatement.id == ps_id).first()
    if not ps:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "message": "Problem statement not found", "error_code": "NOT_FOUND"},
        )
    return ps


def get_problem_statement_by_code(db: Session, code: str) -> Optional[ProblemStatement]:
    """Retrieve a single problem statement by code."""
    return db.query(ProblemStatement).filter(ProblemStatement.problem_code == code.strip()).first()


def get_problem_statement_stats(db: Session) -> dict:
    """Statistics count for admin console."""
    total_ai = db.query(ProblemStatement).filter(ProblemStatement.realm == RealmEnum.AI).count()
    total_cyber = db.query(ProblemStatement).filter(ProblemStatement.realm == RealmEnum.CYBERSECURITY).count()
    total_active = db.query(ProblemStatement).filter(ProblemStatement.status == True).count()
    total_inactive = db.query(ProblemStatement).filter(ProblemStatement.status == False).count()
    total_all = db.query(ProblemStatement).count()

    return {
        "total_ai": total_ai,
        "total_cybersecurity": total_cyber,
        "total_active": total_active,
        "total_inactive": total_inactive,
        "total_all": total_all,
    }


def create_problem_statement(db: Session, data: ProblemStatementCreate, admin: User) -> ProblemStatement:
    """Create a new problem statement."""
    code = data.problem_code.strip().upper()
    existing = db.query(ProblemStatement).filter(ProblemStatement.problem_code == code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"success": False, "message": f"Problem code '{code}' already exists", "error_code": "CODE_EXISTS"},
        )

    ps = ProblemStatement(
        problem_code=code,
        realm=data.realm,
        title=data.title.strip(),
        description=data.description.strip(),
        difficulty=data.difficulty,
        status=data.status,
    )
    db.add(ps)
    db.flush()

    # Audit log
    log = AuditLog(
        admin_id=admin.id,
        action="CREATE_PROBLEM_STATEMENT",
        target_type="problem_statement",
        target_id=admin.id,  # target_id is integer in audit_logs, record admin
        description=f"Admin '{admin.username}' created problem statement {ps.problem_code}: {ps.title[:50]}",
    )
    db.add(log)
    db.commit()
    db.refresh(ps)
    return ps


def update_problem_statement(
    db: Session, ps_id: uuid.UUID, data: ProblemStatementUpdate, admin: User
) -> ProblemStatement:
    """Update title, description, difficulty, status, or realm."""
    ps = get_problem_statement_by_id(db, ps_id)

    if data.title is not None:
        ps.title = data.title.strip()
    if data.description is not None:
        ps.description = data.description.strip()
    if data.difficulty is not None:
        ps.difficulty = data.difficulty
    if data.status is not None:
        ps.status = data.status
    if data.realm is not None:
        ps.realm = data.realm

    # Audit log
    log = AuditLog(
        admin_id=admin.id,
        action="UPDATE_PROBLEM_STATEMENT",
        target_type="problem_statement",
        target_id=admin.id,
        description=f"Admin '{admin.username}' updated problem statement {ps.problem_code}",
    )
    db.add(log)
    db.commit()
    db.refresh(ps)
    return ps


def delete_problem_statement(db: Session, ps_id: uuid.UUID, admin: User) -> None:
    """Delete only unused problem statements (no associated projects)."""
    ps = get_problem_statement_by_id(db, ps_id)

    # Check if used by any project
    project_count = db.query(Project).filter(Project.problem_statement_id == ps.id).count()
    if project_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "message": f"Cannot delete problem statement '{ps.problem_code}' because it is assigned to {project_count} project(s). Deactivate it instead.",
                "error_code": "STATEMENT_IN_USE",
            },
        )

    code = ps.problem_code
    db.delete(ps)

    # Audit log
    log = AuditLog(
        admin_id=admin.id,
        action="DELETE_PROBLEM_STATEMENT",
        target_type="problem_statement",
        target_id=admin.id,
        description=f"Admin '{admin.username}' deleted problem statement {code}",
    )
    db.add(log)
    db.commit()


def toggle_problem_statement_status(
    db: Session, ps_id: uuid.UUID, status_val: bool, admin: User
) -> ProblemStatement:
    """Toggle or update active status of a problem statement."""
    ps = get_problem_statement_by_id(db, ps_id)
    ps.status = status_val

    log = AuditLog(
        admin_id=admin.id,
        action="TOGGLE_PROBLEM_STATEMENT_STATUS",
        target_type="problem_statement",
        target_id=admin.id,
        description=f"Admin '{admin.username}' set problem statement {ps.problem_code} status to {status_val}",
    )
    db.add(log)
    db.commit()
    db.refresh(ps)
    return ps


def assign_balanced_problem_statement(db: Session, realm: RealmEnum) -> ProblemStatement:
    """
    Assign an active problem statement from the given realm using fair balanced rotation.
    1. Query all ACTIVE problem statements in the realm.
    2. Count existing project assignments for each statement in PostgreSQL.
    3. Find the minimum assignment count across active statements in that realm.
    4. Collect all statements that have this minimum count (current cycle candidates).
    5. Randomly choose one statement from these candidates.

    Guarantees:
      - AI teams receive only AI statements.
      - Cybersecurity teams receive only Cybersecurity statements.
      - Every statement in a realm is assigned exactly once before any is assigned twice.
      - The (N+1)th team begins a new balanced shuffled cycle.
      - Inactive statements are never assigned.
    """
    active_statements = (
        db.query(ProblemStatement)
        .filter(ProblemStatement.realm == realm, ProblemStatement.status == True)
        .all()
    )
    if not active_statements:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "message": f"No active problem statements available in realm {realm.value}",
                "error_code": "NO_ACTIVE_STATEMENTS",
            },
        )

    ps_ids = [ps.id for ps in active_statements]
    counts_query = (
        db.query(Project.problem_statement_id, func.count(Project.id))
        .filter(Project.problem_statement_id.in_(ps_ids))
        .group_by(Project.problem_statement_id)
        .all()
    )
    count_map = {ps.id: 0 for ps in active_statements}
    for ps_id, cnt in counts_query:
        if ps_id in count_map:
            count_map[ps_id] = cnt

    min_count = min(count_map.values())
    candidates = [ps for ps in active_statements if count_map[ps.id] == min_count]
    return random.choice(candidates)

