import os
import tempfile
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, Path, UploadFile, File, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.core.dependencies import require_admin, get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.problem_statement import ProblemStatement, RealmEnum, DifficultyEnum
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
    toggle_problem_statement_status,
)

router = APIRouter(tags=["Problem Statements"])


class ProblemStatementStatusBody(BaseModel):
    status: bool


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


# ─── Public & User APIs ──────────────────────────────────────────────────────

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


@router.get("/api/problem-statements/assigned", status_code=200)
def get_assigned_problem_statement(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve the official problem statement assigned to the current user's team.
    """
    project = db.query(Project).filter(Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "message": "No project registered for this team", "error_code": "NO_PROJECT"},
        )

    ps = project.problem_statement_rel
    if not ps and project.problem_statement_id:
        ps = db.query(ProblemStatement).filter(ProblemStatement.id == project.problem_statement_id).first()
    if not ps and project.problem_code:
        ps = db.query(ProblemStatement).filter(ProblemStatement.problem_code == project.problem_code).first()

    # If team domain is AI or CYBERSECURITY and project has no problem statement linked, auto-assign one
    if not ps and not project.problem_statement_id:
        realm_str = project.realm or (current_user.domain.name if current_user.domain else "AI")
        if realm_str in ("AI", "CYBERSECURITY"):
            from app.services.problem_statement_service import assign_balanced_problem_statement
            try:
                assigned_ps = assign_balanced_problem_statement(db, RealmEnum(realm_str))
                if assigned_ps:
                    project.problem_statement_id = assigned_ps.id
                    project.problem_code = assigned_ps.problem_code
                    project.realm = assigned_ps.realm
                    if not project.project_title or project.project_title == "Project":
                        project.project_title = assigned_ps.title
                    if not project.problem_statement:
                        project.problem_statement = assigned_ps.description
                    db.commit()
                    ps = assigned_ps
            except Exception:
                pass

    if ps:
        data = _ps_dict(ps)
        data["detailed_description"] = ps.description
        data["problem_statement"] = ps.description
        data["assigned_at"] = project.assigned_at.isoformat() if getattr(project, "assigned_at", None) else None
        return {
            "success": True,
            "message": "Assigned problem statement retrieved successfully",
            "data": data,
        }

    return {
        "success": True,
        "message": "Assigned problem statement details retrieved",
        "data": {
            "id": str(project.problem_statement_id) if project.problem_statement_id else None,
            "problem_code": project.problem_code or "—",
            "realm": project.realm or (current_user.domain.name if current_user.domain else "AI"),
            "title": project.project_title or "Official Problem Statement",
            "description": project.problem_statement or "—",
            "detailed_description": project.problem_statement or "—",
            "problem_statement": project.problem_statement or "—",
            "difficulty": "INTERMEDIATE",
            "status": True,
            "assigned_at": project.assigned_at.isoformat() if getattr(project, "assigned_at", None) else None,
        },
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


@router.patch("/api/problem-statements/{id}/status", status_code=200)
@router.patch("/api/admin/problem-statements/{id}/status", status_code=200)
def admin_patch_problem_statement_status(
    id: uuid.UUID,
    payload: Optional[ProblemStatementStatusBody] = None,
    status_param: Optional[bool] = Query(None, alias="status"),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin API: Activate or deactivate a problem statement."""
    new_status = payload.status if payload is not None else status_param
    if new_status is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "message": "Field 'status' (boolean) is required in body or query", "error_code": "STATUS_REQUIRED"},
        )
    ps = toggle_problem_statement_status(db, id, new_status, admin)
    return {
        "success": True,
        "message": f"Problem statement '{ps.problem_code}' status updated to {new_status}",
        "data": _ps_dict(ps),
    }


@router.post("/api/problem-statements/import-pdf", status_code=200)
@router.post("/api/admin/problem-statements/import-pdf", status_code=200)
def admin_import_problem_statements_from_pdf(
    file: Optional[UploadFile] = File(None),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin API: Parse official problem statements from PDF and update database idempotently."""
    from app.services.pdf_import_service import import_official_statements, DEFAULT_PDF_PATH
    temp_path = None
    try:
        if file and file.filename:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(file.file.read())
                temp_path = tmp.name
            path_to_use = temp_path
        else:
            path_to_use = DEFAULT_PDF_PATH

        res = import_official_statements(db, pdf_path=path_to_use)
        return {
            "success": True,
            "message": f"Successfully processed official statements: {res['inserted']} inserted, {res['updated']} updated, {res['total']} total.",
            "data": res,
        }
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass


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
