"""Admin routes — user & team management, project review, dashboard."""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.database import get_db
from app.core.dependencies import require_admin
from app.models.domain import Domain, DomainName
from app.models.project import Project, ProjectStatus
from app.models.user import User, UserStatus, UserRole
from app.models.audit_log import AuditLog
from app.schemas.user import UserCreate, UserUpdate, UserStatusUpdate, UserPasswordReset, TeamEditPermissionRequest, BulkEditPermissionRequest, BulkPasswordResetRequest
from app.schemas.review import ReviewCreate, ReviewUpdate
from app.services.user_service import (
    create_user, list_users, get_user_by_id,
    update_user, update_user_status, reset_user_password, delete_user,
    set_team_edit_permission, reset_team_password_default, bulk_set_edit_permission, bulk_reset_password,
)
from app.schemas.project import AdminProjectUpdateRequest, AdminGithubUpdateRequest, AdminDomainUpdateRequest
from app.services.project_service import list_projects_admin, get_project_by_id, admin_update_project
from app.services.review_service import create_review, update_review, get_project_reviews

router = APIRouter(prefix="/api/admin", tags=["Admin"])

DOMAIN_DISPLAY = {"AI": "AI", "CYBERSECURITY": "Cybersecurity", "OPEN_INNOVATION": "Open Innovation"}


# ─── Dashboard ───────────────────────────────────────────────────────────────

@router.get("/dashboard", status_code=200)
def admin_dashboard(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Return aggregated statistics for admin dashboard."""
    total_users = db.query(User).filter(User.role == UserRole.USER).count()
    active_users = db.query(User).filter(User.role == UserRole.USER, User.status == UserStatus.ACTIVE).count()
    inactive_users = db.query(User).filter(User.role == UserRole.USER, User.status == UserStatus.INACTIVE).count()

    domain_counts = {}
    for dn in [DomainName.AI, DomainName.CYBERSECURITY, DomainName.OPEN_INNOVATION]:
        domain_obj = db.query(Domain).filter(Domain.name == dn.value).first()
        if domain_obj:
            count = db.query(User).filter(User.domain_id == domain_obj.id, User.role == UserRole.USER).count()
        else:
            count = 0
        domain_counts[dn.value] = count

    total_projects = db.query(Project).count()
    submitted = db.query(Project).filter(Project.status == ProjectStatus.SUBMITTED).count()
    under_review = db.query(Project).filter(Project.status == ProjectStatus.UNDER_REVIEW).count()
    in_progress = db.query(Project).filter(Project.status == ProjectStatus.IN_PROGRESS).count()
    completed = db.query(Project).filter(Project.status == ProjectStatus.COMPLETED).count()
    rejected = db.query(Project).filter(Project.status == ProjectStatus.REJECTED).count()

    from app.core.config import settings
    rounds = []
    for r in range(1, settings.MAX_REVIEW_ROUNDS + 1):
        count = db.query(Project).filter(Project.current_round == r).count()
        rounds.append({"round": r, "count": count})

    return {
        "success": True,
        "message": "Dashboard data retrieved",
        "data": {
            "users": {
                "total": total_users,
                "ai": domain_counts.get("AI", 0),
                "cybersecurity": domain_counts.get("CYBERSECURITY", 0),
                "open_innovation": domain_counts.get("OPEN_INNOVATION", 0),
                "active": active_users,
                "inactive": inactive_users,
            },
            "projects": {
                "total": total_projects,
                "submitted": submitted,
                "under_review": under_review,
                "in_progress": in_progress,
                "completed": completed,
                "rejected": rejected,
            },
            "rounds": rounds,
        },
    }


# ─── Team / User Management ──────────────────────────────────────────────────

def _handle_list_teams(
    search: Optional[str],
    domain: Optional[str],
    status: Optional[str],
    page: int,
    page_size: int,
    db: Session,
):
    items, total, total_pages = list_users(db, page, page_size, domain, status, search)
    return {
        "success": True,
        "message": "Teams retrieved",
        "data": [_user_dict(u) for u in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


@router.get("/teams", status_code=200)
def admin_list_teams(
    search: Optional[str] = Query(None),
    domain: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return _handle_list_teams(search, domain, status, page, page_size, db)


@router.get("/users", status_code=200)
def admin_list_users(
    search: Optional[str] = Query(None),
    domain: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return _handle_list_teams(search, domain, status, page, page_size, db)


@router.post("/teams", status_code=201)
def admin_create_team(
    data: UserCreate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = create_user(db, data, admin)
    return {"success": True, "message": "Team created successfully", "data": _user_dict(user)}


@router.post("/users", status_code=201)
def admin_create_user(
    data: UserCreate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = create_user(db, data, admin)
    return {"success": True, "message": "Team created successfully", "data": _user_dict(user)}


@router.get("/teams/{user_id}", status_code=200)
def admin_get_team(
    user_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = get_user_by_id(db, user_id)
    return {"success": True, "message": "Team retrieved", "data": _user_dict(user)}


@router.get("/users/{user_id}", status_code=200)
def admin_get_user(
    user_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = get_user_by_id(db, user_id)
    return {"success": True, "message": "Team retrieved", "data": _user_dict(user)}


@router.put("/teams/{user_id}", status_code=200)
def admin_update_team(
    user_id: int,
    data: UserUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = update_user(db, user_id, data, admin)
    return {"success": True, "message": "Team updated", "data": _user_dict(user)}


@router.put("/users/{user_id}", status_code=200)
def admin_update_user(
    user_id: int,
    data: UserUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = update_user(db, user_id, data, admin)
    return {"success": True, "message": "Team updated", "data": _user_dict(user)}


@router.patch("/teams/{user_id}/status", status_code=200)
def admin_update_team_status(
    user_id: int,
    data: UserStatusUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = update_user_status(db, user_id, data, admin)
    return {"success": True, "message": "Team status updated", "data": _user_dict(user)}


@router.patch("/users/{user_id}/status", status_code=200)
def admin_update_user_status(
    user_id: int,
    data: UserStatusUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = update_user_status(db, user_id, data, admin)
    return {"success": True, "message": "Team status updated", "data": _user_dict(user)}


@router.patch("/teams/{user_id}/password", status_code=200)
def admin_reset_team_password(
    user_id: int,
    data: UserPasswordReset,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = reset_user_password(db, user_id, data, admin)
    return {"success": True, "message": "Password reset successfully", "data": {"id": user.id, "username": user.username}}


@router.patch("/users/{user_id}/password", status_code=200)
def admin_reset_user_password(
    user_id: int,
    data: UserPasswordReset,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = reset_user_password(db, user_id, data, admin)
    return {"success": True, "message": "Password reset successfully", "data": {"id": user.id, "username": user.username}}


@router.delete("/teams/{user_id}", status_code=200)
def admin_delete_team(
    user_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    delete_user(db, user_id, admin)
    return {"success": True, "message": "Team deleted", "data": None}


@router.delete("/users/{user_id}", status_code=200)
def admin_delete_user(
    user_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    delete_user(db, user_id, admin)
    return {"success": True, "message": "Team deleted", "data": None}


# ─── Edit Permission & Password Reset ────────────────────────────────────────

@router.patch("/teams/{user_id}/edit-permission", status_code=200)
def admin_set_edit_permission(
    user_id: int,
    data: TeamEditPermissionRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Grant or revoke editing permission for a submitted project."""
    user = set_team_edit_permission(db, user_id, data, admin)
    return {"success": True, "message": "Edit permission updated", "data": _user_dict(user)}


@router.post("/teams/{user_id}/reset-password", status_code=200)
def admin_reset_team_password_default(
    user_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Reset a team password to the default 'hogwarts-legacy'."""
    user = reset_team_password_default(db, user_id, admin)
    return {"success": True, "message": "Password reset to default successfully", "data": {"id": user.id, "username": user.username}}


@router.post("/bulk/edit-permission", status_code=200)
def admin_bulk_edit_permission(
    data: BulkEditPermissionRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Set edit permission for multiple teams at once."""
    results = bulk_set_edit_permission(db, data, admin)
    return {"success": True, "message": f"Edit permission updated for {len(results)} teams", "data": [_user_dict(u) for u in results]}


@router.post("/bulk/reset-password", status_code=200)
def admin_bulk_reset_password(
    data: BulkPasswordResetRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Reset passwords to default for multiple teams at once."""
    results = bulk_reset_password(db, data, admin)
    return {"success": True, "message": f"Passwords reset for {len(results)} teams", "data": [{"id": u.id, "username": u.username} for u in results]}


@router.get("/export/teams", status_code=200)
def admin_export_teams(
    domain: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Export all teams as CSV."""
    import io, csv
    from fastapi.responses import StreamingResponse
    items, _, _ = list_users(db, 1, 1000, domain, status, None)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Team Name", "Leader", "Email", "Domain", "College", "Members", "Status", "Project Status", "Submitted At", "Edit Permission"])
    for u in items:
        domain_name = u.domain.name if u.domain else ""
        project = u.projects[0] if u.projects else None
        members = ", ".join(filter(None, [u.member_one, u.member_two, u.member_three]))
        writer.writerow([
            u.id, u.team_name or u.name, u.team_leader or u.name,
            u.email, domain_name, u.college_name or u.organization,
            members, u.status,
            project.status if project else "",
            project.submitted_at.isoformat() if project and project.submitted_at else "",
            getattr(u, "edit_permission", False),
        ])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=teams_export.csv"}
    )


# ─── Project Management ──────────────────────────────────────────────────────

@router.get("/projects", status_code=200)
def admin_list_projects(
    domain: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_round: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    items, total, total_pages = list_projects_admin(db, domain, status, current_round, user_id, page, page_size)
    return {
        "success": True,
        "message": "Projects retrieved",
        "data": [_project_dict(p) for p in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


@router.get("/projects/{project_id}", status_code=200)
def admin_get_project(
    project_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    project = get_project_by_id(db, project_id)
    reviews = get_project_reviews(db, project_id)
    data = _project_dict(project)
    data["reviews"] = [_review_dict(r) for r in reviews]
    return {"success": True, "message": "Project retrieved", "data": data}


@router.get("/projects/{project_id}/reviews", status_code=200)
def admin_get_project_reviews_endpoint(
    project_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    get_project_by_id(db, project_id)  # 404 if not found
    reviews = get_project_reviews(db, project_id)
    return {
        "success": True,
        "message": "Reviews retrieved",
        "data": [_review_dict(r) for r in reviews],
    }


@router.post("/projects/{project_id}/reviews", status_code=201)
def admin_create_review(
    project_id: int,
    data: ReviewCreate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    review = create_review(db, project_id, data, admin)
    return {"success": True, "message": "Review submitted", "data": _review_dict(review)}


@router.put("/projects/{project_id}/reviews/{review_id}", status_code=200)
def admin_update_review_endpoint(
    project_id: int,
    review_id: int,
    data: ReviewUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    review = update_review(db, project_id, review_id, data, admin)
    return {"success": True, "message": "Review updated", "data": _review_dict(review)}


@router.put("/projects/{project_id}", status_code=200)
def admin_update_project_endpoint(
    project_id: int,
    data: AdminProjectUpdateRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin updates any project field (including locked fields) regardless of submission status."""
    project = admin_update_project(db, project_id, data, admin)
    reviews = get_project_reviews(db, project_id)
    result = _project_dict(project)
    result["reviews"] = [_review_dict(r) for r in reviews]
    return {"success": True, "message": "Project updated", "data": result}


@router.put("/projects/{project_id}/github", status_code=200)
def admin_update_project_github(
    project_id: int,
    data: AdminGithubUpdateRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin updates the locked GitHub URL for a project."""
    from app.services.project_service import _check_github_unique
    project = get_project_by_id(db, project_id)
    _check_github_unique(db, data.github_url, exclude_project_id=project.id)
    project.github_url = data.github_url
    db.commit()
    db.refresh(project)
    return {"success": True, "message": "GitHub URL updated", "data": _project_dict(project)}


@router.put("/projects/{project_id}/domain", status_code=200)
def admin_update_project_domain(
    project_id: int,
    data: AdminDomainUpdateRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin updates the domain for a project."""
    from app.models.domain import Domain
    project = get_project_by_id(db, project_id)
    domain = db.query(Domain).filter(Domain.name == data.domain).first()
    if not domain:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail={"success": False, "message": f"Domain '{data.domain}' not found"})
    project.domain_id = domain.id
    db.commit()
    db.refresh(project)
    return {"success": True, "message": "Project domain updated", "data": _project_dict(project)}


# ─── Problem Statements Management ──────────────────────────────────────────

@router.get("/problem-statements", status_code=200)
def admin_list_problem_statements(
    domain: Optional[str] = Query(None),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List all predefined problem statements with assignment status and assigned teams."""
    from app.models.problem_statement import ProblemStatement
    query = db.query(ProblemStatement)
    if domain:
        query = query.join(Domain).filter(Domain.name == domain)
    statements = query.order_by(ProblemStatement.id).all()

    data = []
    for ps in statements:
        assigned_projects = db.query(Project).filter(Project.assigned_problem_statement_id == ps.id).all()
        teams = [{"id": prj.user.id, "team_name": prj.user.team_name, "username": prj.user.username} for prj in assigned_projects]
        data.append({
            "id": ps.id,
            "problem_code": ps.problem_code,
            "domain_id": ps.domain_id,
            "domain": ps.domain.name if ps.domain else None,
            "detailed_description": ps.detailed_description,
            "is_assigned": len(teams) > 0,
            "assigned_team_id": teams[0]["id"] if teams else None,
            "teams": teams,
            "teams_count": len(teams),
            "created_at": ps.created_at.isoformat(),
        })

    return {"success": True, "message": "Problem statements retrieved", "data": data}


@router.patch("/problem-statements/{id}/release", status_code=200)
def admin_release_problem_statement(
    id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Release/unassign a problem statement if a team was deleted."""
    from app.models.problem_statement import ProblemStatement
    from fastapi import HTTPException
    ps = db.query(ProblemStatement).filter(ProblemStatement.id == id).first()
    if not ps:
        raise HTTPException(status_code=404, detail={"success": False, "message": "Problem statement not found"})

    ps.is_assigned = False
    ps.assigned_team_id = None
    db.commit()
    db.refresh(ps)
    return {"success": True, "message": f"Problem statement {ps.problem_code} released", "data": {"id": ps.id, "problem_code": ps.problem_code, "is_assigned": False}}


# ─── Serialization helpers ───────────────────────────────────────────────────

def _user_dict(user: User) -> dict:
    domain_basic = None
    if user.domain:
        domain_basic = {
            "id": user.domain.id,
            "name": user.domain.name,
            "display_name": DOMAIN_DISPLAY.get(user.domain.name, user.domain.name),
        }

    project_summary = None
    if user.projects:
        p = user.projects[0]
        p_code = p.assigned_problem_statement.problem_code if p.assigned_problem_statement else None
        project_summary = {
            "id": p.id,
            "project_code": p.project_code,
            "problem_code": p_code,
            "assigned_problem_statement_id": p.assigned_problem_statement_id,
            "project_title": p.project_title or (
                f"{p_code} Solution Project" if p_code else (p.topic.title if p.topic else p.custom_topic)
            ),
            "status": p.status,
            "current_round": p.current_round,
            "submitted_at": p.submitted_at.isoformat() if p.submitted_at else None,
            "is_submitted": p.is_submitted,
        }

    return {
        "id": user.id,
        "name": user.name,
        "team_name": user.team_name or user.name,
        "team_leader": user.team_leader or user.name,
        "member_one": user.member_one,
        "member_two": user.member_two,
        "member_three": user.member_three,
        "college_name": user.college_name or user.organization,
        "organization": user.organization or user.college_name,
        "department": user.department,
        "academic_year": user.academic_year,
        "username": user.username,
        "email": user.email,
        "phone": user.phone,
        "domain_id": user.domain_id,
        "domain": domain_basic,
        "role": user.role,
        "status": user.status,
        "project": project_summary,
        "edit_permission": getattr(user, "edit_permission", False),
        "edit_permission_reason": getattr(user, "edit_permission_reason", None),
        "edit_permission_granted_at": user.edit_permission_granted_at.isoformat() if getattr(user, "edit_permission_granted_at", None) else None,
        "password_reset_required": getattr(user, "password_reset_required", False),
        "created_at": user.created_at.isoformat(),
        "updated_at": user.updated_at.isoformat(),
    }


def _project_dict(project: Project) -> dict:
    domain_map = {"AI": "AI", "CYBERSECURITY": "Cybersecurity", "OPEN_INNOVATION": "Open Innovation"}
    u = project.user
    user_info = {
        "id": u.id,
        "name": u.name,
        "username": u.username,
        "email": u.email,
        "phone": u.phone,
        "team_name": u.team_name or u.name,
        "team_leader": u.team_leader or u.name,
        "member_one": u.member_one,
        "member_two": u.member_two,
        "member_three": u.member_three,
        "college_name": u.college_name or u.organization,
        "organization": u.organization or u.college_name,
        "department": u.department,
        "academic_year": u.academic_year,
    }
    p_code = project.assigned_problem_statement.problem_code if project.assigned_problem_statement else None
    return {
        "id": project.id,
        "project_code": project.project_code,
        "user_id": project.user_id,
        "user": user_info,
        "domain_id": project.domain_id,
        "domain": {
            "id": project.domain.id,
            "name": project.domain.name,
            "display_name": domain_map.get(project.domain.name, project.domain.name),
        },
        "topic_id": project.topic_id,
        "topic": (
            {"id": project.topic.id, "title": project.topic.title, "description": project.topic.description}
            if project.topic
            else None
        ),
        "assigned_problem_statement_id": project.assigned_problem_statement_id,
        "assigned_problem_statement": (
            {
                "id": project.assigned_problem_statement.id,
                "problem_code": project.assigned_problem_statement.problem_code,
                "detailed_description": project.assigned_problem_statement.detailed_description,
            }
            if project.assigned_problem_statement
            else None
        ),
        "problem_code": p_code,
        "custom_topic": project.custom_topic,
        "project_title": project.project_title or (
            f"{p_code} Solution Project" if p_code else (project.topic.title if project.topic else project.custom_topic)
        ),
        "abstract": project.abstract,
        "problem_statement": (
            project.assigned_problem_statement.detailed_description
            if project.assigned_problem_statement
            else project.problem_statement
        ),
        "objectives": project.objectives,
        "proposed_solution": project.proposed_solution,
        "technologies": project.technology_stack or project.technologies,
        "technology_stack": project.technology_stack or project.technologies,
        "expected_outcome": project.expected_outcome,
        "project_description": project.project_description,
        "github_url": project.github_url,
        "demo_url": project.demo_url,
        "is_submitted": project.is_submitted,
        "status": project.status,
        "current_round": project.current_round,
        "draft_saved_at": project.draft_saved_at.isoformat() if project.draft_saved_at else None,
        "submitted_at": project.submitted_at.isoformat() if project.submitted_at else None,
        "updated_at": project.updated_at.isoformat(),
        "edit_permission": getattr(u, "edit_permission", False),
        "edit_permission_reason": getattr(u, "edit_permission_reason", None),
        "edit_permission_granted_at": u.edit_permission_granted_at.isoformat() if getattr(u, "edit_permission_granted_at", None) else None,
    }


def _review_dict(review) -> dict:
    return {
        "id": review.id,
        "project_id": review.project_id,
        "admin_id": review.admin_id,
        "admin": {"id": review.admin.id, "name": review.admin.name, "username": review.admin.username},
        "round_number": review.round_number,
        "review_text": review.review_text,
        "suggested_improvements": review.suggested_improvements,
        "status": review.status,
        "reviewed_at": review.reviewed_at.isoformat() if review.reviewed_at else review.created_at.isoformat(),
        "created_at": review.created_at.isoformat(),
        "updated_at": review.updated_at.isoformat(),
    }
