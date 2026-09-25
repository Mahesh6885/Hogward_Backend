"""Problem Statements routes — public selection for teams, CRUD for admins."""
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.core.dependencies import require_admin
from app.models.user import User
from app.models.problem_statement import RealmEnum, DifficultyEnum
from app.schemas.problem_statement import (
    ProblemStatementCreate,
    ProblemStatementUpdate,
    ProblemStatementResponse,
    ProblemStatementStats,
)
from app.services.problem_statement_service import (
    get_problem_statements,
    get_problem_statement_by_id,
    get_problem_statement_stats,
    create_problem_statement,
    update_problem_statement,
    delete_problem_statement,
)

router = APIRouter(tags=["Problem Statements"])


def _ps_dict(ps, project_count: int = 0) -> dict:
    return {
        "id": str(ps.id),
        "problem_code": ps.problem_code,
        "realm": ps.realm,
        "title": ps.title,
        "description": ps.description,
        "difficulty": ps.difficulty,
        "status": ps.status,
        "created_at": ps.created_at.isoformat() if ps.created_at else None,
        "updated_at": ps.updated_at.isoformat() if ps.updated_at else None,
        "project_count": project_count,
    }


# ─── Public APIs ─────────────────────────────────────────────────────────────

@router.get("/api/problem-statements", status_code=200)
def list_problem_statements(
    realm: Optional[RealmEnum] = Query(None, description="Filter by realm (AI or CYBERSECURITY)"),
    difficulty: Optional[DifficultyEnum] = Query(None, description="Filter by difficulty"),
    status: Optional[bool] = Query(None, description="Filter by active/inactive"),
    search: Optional[str] = Query(None, description="Search by title, code or description"),
    db: Session = Depends(get_db),
):
    """
    Public API: Return official problem statements.
    Optional query parameters:
      - GET /api/problem-statements
      - GET /api/problem-statements?realm=AI
      - GET /api/problem-statements?realm=CYBERSECURITY
    """
    statements = get_problem_statements(db, realm=realm, difficulty=difficulty, status_filter=status, search=search)
    return {
        "success": True,
        "message": "Problem statements retrieved",
        "data": [_ps_dict(ps) for ps in statements],
    }


@router.get("/api/problem-statements/{id}", status_code=200)
def get_single_problem_statement(
    id: uuid.UUID = Path(..., description="Problem statement UUID"),
    db: Session = Depends(get_db),
):
    """Retrieve details of a single problem statement by UUID."""
    ps = get_problem_statement_by_id(db, id)
    return {
        "success": True,
        "message": "Problem statement retrieved",
        "data": _ps_dict(ps),
    }


# ─── Admin APIs ──────────────────────────────────────────────────────────────

@router.get("/api/admin/problem-statements/stats", status_code=200)
def admin_stats_problem_statements(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Retrieve aggregated counts of AI, Cybersecurity, active, and inactive problem statements."""
    stats = get_problem_statement_stats(db)
    return {
        "success": True,
        "message": "Problem statement stats retrieved",
        "data": stats,
    }


@router.post("/api/problem-statements", status_code=201)
@router.post("/api/admin/problem-statements", status_code=201)
def admin_create_problem_statement(
    data: ProblemStatementCreate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin API: Create a new official problem statement."""
    ps = create_problem_statement(db, data, admin)
    return {
        "success": True,
        "message": f"Problem statement '{ps.problem_code}' created successfully",
        "data": _ps_dict(ps),
    }


@router.put("/api/problem-statements/{id}", status_code=200)
@router.put("/api/admin/problem-statements/{id}", status_code=200)
def admin_update_problem_statement(
    id: uuid.UUID,
    data: ProblemStatementUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin API: Update title, description, difficulty, or active status."""
    ps = update_problem_statement(db, id, data, admin)
    return {
        "success": True,
        "message": f"Problem statement '{ps.problem_code}' updated successfully",
        "data": _ps_dict(ps),
    }


@router.delete("/api/problem-statements/{id}", status_code=200)
@router.delete("/api/admin/problem-statements/{id}", status_code=200)
def admin_delete_problem_statement(
    id: uuid.UUID,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin API: Delete only unused problem statements."""
    delete_problem_statement(db, id, admin)
    return {
        "success": True,
        "message": "Problem statement deleted successfully",
    }
