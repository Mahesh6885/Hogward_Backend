"""Project routes for users/teams."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.project import ProjectSubmitRequest, ProjectDraftRequest
from app.services.project_service import (
    submit_project,
    submit_final_project,
    save_project_draft,
    get_user_project,
    get_project_timeline,
    get_project_problem_statement,
)
from app.services.review_service import get_project_reviews

router = APIRouter(prefix="/api/projects", tags=["Projects"])


def _serialize_project(project) -> dict:
    domain_map = {"AI": "AI", "CYBERSECURITY": "Cybersecurity", "OPEN_INNOVATION": "Open Innovation"}
    u = project.user
    user_data = {
        "id": u.id,
        "name": u.name,
        "username": u.username,
        "team_name": u.team_name or u.name,
        "team_leader": u.team_leader or u.name,
        "member_one": u.member_one,
        "member_two": u.member_two,
        "member_three": u.member_three,
        "college_name": u.college_name or u.organization,
        "organization": u.organization or u.college_name,
        "department": u.department,
        "edit_permission": getattr(u, "edit_permission", False),
        "edit_permission_reason": getattr(u, "edit_permission_reason", None),
        "edit_permission_granted_at": u.edit_permission_granted_at.isoformat() if getattr(u, "edit_permission_granted_at", None) else None,
    }
    # Resolve effective technology_stack
    tech = project.technology_stack or project.technologies

    return {
        "id": project.id,
        "project_code": project.project_code,
        "user_id": project.user_id,
        "user": user_data,
        "edit_permission": getattr(u, "edit_permission", False),
        "edit_permission_reason": getattr(u, "edit_permission_reason", None),
        "edit_permission_granted_at": u.edit_permission_granted_at.isoformat() if getattr(u, "edit_permission_granted_at", None) else None,
        "domain_id": project.domain_id,
        "domain": (
            {
                "id": project.domain.id,
                "name": project.domain.name,
                "display_name": domain_map.get(project.domain.name, project.domain.name),
            }
            if project.domain
            else (
                {
                    "id": u.domain.id,
                    "name": u.domain.name,
                    "display_name": domain_map.get(u.domain.name, u.domain.name),
                }
                if (u and getattr(u, "domain", None))
                else None
            )
        ),
        "realm": project.realm or (project.domain.name if project.domain else (u.domain.name if u and u.domain else "AI")),
        "problem_statement_id": str(project.problem_statement_id) if project.problem_statement_id else None,
        "problem_statement": (
            {
                "id": str(project.problem_statement_rel.id),
                "problem_code": project.problem_statement_rel.problem_code,
                "realm": project.problem_statement_rel.realm,
                "title": project.problem_statement_rel.title,
                "description": project.problem_statement_rel.description,
                "detailed_description": project.problem_statement_rel.description,
                "difficulty": project.problem_statement_rel.difficulty,
            }
            if project.problem_statement_rel
            else (
                {
                    "id": str(project.problem_statement_id) if project.problem_statement_id else None,
                    "problem_code": project.problem_code or "—",
                    "realm": project.realm or (project.domain.name if project.domain else "AI"),
                    "title": project.project_title or "Official Problem Statement",
                    "description": project.problem_statement or "",
                    "detailed_description": project.problem_statement or "",
                    "difficulty": "INTERMEDIATE",
                }
                if (project.problem_statement or project.problem_code)
                else None
            )
        ),
        "problem_code": (
            project.problem_statement_rel.problem_code
            if project.problem_statement_rel
            else (project.problem_code or "—")
        ),
        "problem_statement_title": (
            project.problem_statement_rel.title
            if project.problem_statement_rel
            else (project.project_title or "Official Problem Statement")
        ),
        "project_title": (
            project.project_title
            if project.project_title
            else (project.problem_statement_rel.title if project.problem_statement_rel else "Project")
        ),
        "abstract": project.abstract,
        "problem_description": (
            project.problem_statement_rel.description
            if project.problem_statement_rel
            else (project.problem_statement or "")
        ),
        "problem_statement_description": (
            project.problem_statement_rel.description
            if project.problem_statement_rel
            else (project.problem_statement or "")
        ),
        "objectives": project.objectives,
        "proposed_solution": project.proposed_solution,
        "technologies": tech,
        "technology_stack": tech,
        "expected_outcome": project.expected_outcome,
        "project_description": project.project_description,
        "github_url": project.github_url,
        "demo_url": project.demo_url,
        "is_submitted": project.is_submitted,
        "status": project.status,
        "current_round": project.current_round,
        "draft_saved_at": project.draft_saved_at.isoformat() if project.draft_saved_at else None,
        "submitted_at": project.submitted_at.isoformat() if project.submitted_at else None,
        "updated_at": project.updated_at.isoformat() if project.updated_at else datetime.now(timezone.utc).isoformat(),
    }


def _serialize_review(r) -> dict:
    return {
        "id": r.id,
        "project_id": r.project_id,
        "admin_id": r.admin_id,
        "admin": {"id": r.admin.id, "name": r.admin.name, "username": r.admin.username},
        "round_number": r.round_number,
        "review_text": r.review_text,
        "suggested_improvements": r.suggested_improvements,
        "status": r.status,
        "reviewed_at": r.reviewed_at.isoformat() if r.reviewed_at else r.created_at.isoformat(),
        "created_at": r.created_at.isoformat(),
        "updated_at": r.updated_at.isoformat(),
    }


# ─── Legacy submit (keep for backward compatibility) ──────────────────────────

@router.post("", status_code=201)
def submit_project_endpoint(
    data: ProjectSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Submit a project (legacy endpoint). Delegates to submit_final_project.
    """
    project = submit_final_project(db, current_user, data)
    return {"success": True, "message": "Project submitted successfully", "data": _serialize_project(project)}


# ─── Draft Save ───────────────────────────────────────────────────────────────

@router.patch("/me/draft", status_code=200)
def save_draft_endpoint(
    data: ProjectDraftRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Save draft: create or update editable project blocks without finalising.
    Each block (abstract, objectives, etc.) can be saved independently.
    Returns HTTP 403 if project is already submitted.
    """
    project = save_project_draft(db, current_user, data)
    return {"success": True, "message": "Draft saved successfully", "data": _serialize_project(project)}


# ─── Final Submit ─────────────────────────────────────────────────────────────

@router.post("/me/submit", status_code=201)
def final_submit_endpoint(
    data: ProjectSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Final project submission. Sets is_submitted=True and status=SUBMITTED.
    After this point, the user can no longer edit the project.
    """
    project = submit_final_project(db, current_user, data, require_github_for_oi=True)
    return {"success": True, "message": "Project submitted successfully! Your project is now locked.", "data": _serialize_project(project)}


# ─── My Project ───────────────────────────────────────────────────────────────

@router.get("/me", status_code=200)
def get_my_project(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the current team's complete project details (draft or submitted)."""
    project = get_user_project(db, current_user)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "message": "You have not started a project yet", "error_code": "NOT_FOUND"},
        )
    return {"success": True, "message": "Project retrieved", "data": _serialize_project(project)}


# ─── Problem Statement ────────────────────────────────────────────────────────

@router.get("/me/problem-statement", status_code=200)
def get_problem_statement_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get predefined problem statement for this team's domain.
    For AI/Cyber: returns topic description. For OI: returns user-submitted problem statement.
    """
    result = get_project_problem_statement(db, current_user)
    return {"success": True, "message": "Problem statement retrieved", "data": result}


# ─── Review History ───────────────────────────────────────────────────────────

@router.get("/me/reviews", status_code=200)
def get_my_project_reviews(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all reviews for the current team's project with feedback and suggested improvements."""
    project = get_user_project(db, current_user)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "message": "You have not started a project yet", "error_code": "NOT_FOUND"},
        )
    reviews = get_project_reviews(db, project.id)
    return {
        "success": True,
        "message": "Reviews retrieved",
        "data": [_serialize_review(r) for r in reviews],
    }


# ─── Timeline ─────────────────────────────────────────────────────────────────

@router.get("/me/timeline", status_code=200)
def get_my_project_timeline(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get chronological timeline milestones for the team's project."""
    project = get_user_project(db, current_user)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "message": "You have not started a project yet", "error_code": "NOT_FOUND"},
        )
    if not project.is_submitted and project.status == "DRAFT":
        return {"success": True, "message": "Project timeline retrieved", "data": []}
    timeline = get_project_timeline(db, project)
    return {
        "success": True,
        "message": "Project timeline retrieved",
        "data": timeline,
    }


# ─── Team Evaluations (Phase 3 User Portal View) ─────────────────────────────

@router.get("/me/evaluations", status_code=200)
def get_my_project_evaluations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get evaluated round scores, totals, evaluator remarks, and suggestions for the team."""
    from app.services.evaluation_service import get_team_evaluation_details
    data = get_team_evaluation_details(db, current_user.id)
    return {
        "success": True,
        "message": "Team evaluations retrieved",
        "data": data,
    }


# ─── Sorting Hat Ceremony ─────────────────────────────────────────────────────

@router.post("/me/complete-sorting-ceremony", status_code=200)
def complete_sorting_ceremony(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark the Sorting Hat Ceremony as completed for this team in PostgreSQL."""
    current_user.sorting_ceremony_completed = True
    db.commit()
    db.refresh(current_user)
    return {
        "success": True,
        "message": "Sorting Hat ceremony completed successfully",
        "data": {"sorting_ceremony_completed": True},
    }
