"""User self-service routes (read-only own data and team details)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.project_service import get_user_project
from app.services.review_service import get_project_reviews

router = APIRouter(prefix="/api/users", tags=["Users"])


def _build_domain_basic(domain):
    if domain is None:
        return None
    domain_map = {"AI": "AI", "CYBERSECURITY": "Cybersecurity", "OPEN_INNOVATION": "Open Innovation"}
    return {"id": domain.id, "name": domain.name, "display_name": domain_map.get(domain.name, domain.name)}


def _user_dict(user: User) -> dict:
    domain_basic = _build_domain_basic(user.domain)
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
        "username": user.username,
        "email": user.email,
        "phone": user.phone,
        "domain_id": user.domain_id,
        "domain": domain_basic,
        "role": user.role,
        "status": user.status,
        "created_at": user.created_at.isoformat(),
        "updated_at": user.updated_at.isoformat(),
    }


def _serialize_project(project) -> dict:
    domain_map = {"AI": "AI", "CYBERSECURITY": "Cybersecurity", "OPEN_INNOVATION": "Open Innovation"}
    tech = project.technology_stack or project.technologies
    return {
        "id": project.id,
        "project_code": project.project_code,
        "user_id": project.user_id,
        "user": _user_dict(project.user),
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
        "custom_topic": project.custom_topic,
        "project_title": project.project_title or (project.topic.title if project.topic else project.custom_topic),
        "abstract": project.abstract,
        "problem_statement": project.problem_statement or (project.topic.description if project.topic else None),
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
        "updated_at": project.updated_at.isoformat(),
    }


def _serialize_review(review) -> dict:
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


@router.get("/me", status_code=200)
def get_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get current user/team's profile."""
    return {
        "success": True,
        "message": "User retrieved successfully",
        "data": _user_dict(current_user),
    }


@router.get("/me/team", status_code=200)
def get_my_team(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get authenticated user's team details and members."""
    return {
        "success": True,
        "message": "Team details retrieved successfully",
        "data": _user_dict(current_user),
    }


@router.get("/me/project", status_code=200)
def get_my_project(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get the current user's project."""
    project = get_user_project(db, current_user)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "message": "You have not submitted a project yet", "error_code": "NOT_FOUND"},
        )
    return {"success": True, "message": "Project retrieved", "data": _serialize_project(project)}


@router.get("/me/reviews", status_code=200)
def get_my_reviews(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get all reviews for the current user's project."""
    project = get_user_project(db, current_user)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "message": "You have not submitted a project yet", "error_code": "NOT_FOUND"},
        )
    reviews = get_project_reviews(db, project.id)
    return {
        "success": True,
        "message": "Reviews retrieved",
        "data": [_serialize_review(r) for r in reviews],
    }
