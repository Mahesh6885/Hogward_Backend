"""Project creation, management, and timeline service."""
from datetime import datetime, timezone
from typing import Optional, Union

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

import random
from app.core.config import settings
from app.models.domain import DomainName
from app.models.project import Project, ProjectStatus
from app.models.topic import Topic
from app.models.user import User
from app.models.audit_log import AuditLog
from app.models.topic_lock import TeamTopicLock
from app.models.problem_statement import ProblemStatement
from app.schemas.project import ProjectSubmitRequest, ProjectDraftRequest
from app.utils.helpers import paginate, generate_project_code


def _next_project_code(db: Session) -> str:
    """Generate the next sequential project code (server-side, not from frontend)."""
    from sqlalchemy import func
    max_id = db.query(func.max(Project.id)).scalar() or 0
    return generate_project_code(max_id + 1)


def _normalize_list_or_str(val: Optional[Union[str, list]]) -> Optional[str]:
    """Normalize list or str into stored string."""
    if val is None:
        return None
    if isinstance(val, list):
        return "\n".join(str(v) for v in val)
    return str(val).strip() if val else None


def _validate_topic_for_domain(db: Session, user: User, topic_id: int) -> Topic:
    """Validate that a topic belongs to the user's domain."""
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "message": "Topic not found", "error_code": "TOPIC_NOT_FOUND"},
        )
    if topic.domain_id != user.domain_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"success": False, "message": "Selected topic does not belong to your domain", "error_code": "DOMAIN_MISMATCH"},
        )
    if not topic.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "message": "Selected topic is no longer available", "error_code": "TOPIC_INACTIVE"},
        )
    return topic


def _check_github_unique(db: Session, github_url: str, exclude_project_id: Optional[int] = None):
    """Validate github URL is unique across all projects."""
    if not github_url:
        return
    query = db.query(Project).filter(Project.github_url == github_url)
    if exclude_project_id:
        query = query.filter(Project.id != exclude_project_id)
    if query.first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"success": False, "message": "GitHub URL already used by another project", "error_code": "GITHUB_URL_EXISTS"},
        )


def get_user_project(db: Session, user: User) -> Optional[Project]:
    """Get the current user's project (or None)."""
    return db.query(Project).filter(Project.user_id == user.id).first()


def save_project_draft(db: Session, user: User, data: ProjectDraftRequest) -> Project:
    """
    Save draft for editable project blocks. Creates draft if not exists.
    Raises HTTP 403 if project is already fully submitted.
    """
    if user.domain is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "message": "User has no domain assigned", "error_code": "NO_DOMAIN"},
        )

    domain_name = user.domain.name
    existing = get_user_project(db, user)

    if existing and existing.is_submitted:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"success": False, "message": "Project already submitted. Only admin can modify it.", "error_code": "ALREADY_SUBMITTED"},
        )

    tech_stack = _normalize_list_or_str(data.technology_stack or data.technologies)
    objectives_str = _normalize_list_or_str(data.objectives)

    # Validate github_url uniqueness if provided
    github_url = data.github_url.strip() if data.github_url else None
    if github_url:
        _check_github_unique(db, github_url, exclude_project_id=existing.id if existing else None)

    if existing is None:
        # Create new draft project
        assigned_ps_id = None
        assigned_ps_desc = None
        assigned_ps_code = None

        if domain_name in (DomainName.AI.value, DomainName.CYBERSECURITY.value):
            statements = db.query(ProblemStatement).filter(ProblemStatement.domain_id == user.domain_id).all()
            if statements:
                chosen = random.choice(statements)
                assigned_ps_id = chosen.id
                assigned_ps_code = chosen.problem_code
                assigned_ps_desc = chosen.detailed_description
                chosen.is_assigned = True
                chosen.assigned_team_id = user.id
            project_title = f"{assigned_ps_code} Solution Project" if assigned_ps_code else (data.project_title or "Project")
            custom_topic = None
            problem_statement = assigned_ps_desc
        else:
            custom_topic = _normalize_list_or_str(data.custom_topic or data.project_title)
            project_title = data.project_title.strip() if data.project_title else custom_topic
            problem_statement = data.problem_statement.strip() if data.problem_statement else None

        prefix = "AI" if domain_name == DomainName.AI.value else ("CY" if domain_name == DomainName.CYBERSECURITY.value else "OI")
        project = Project(
            project_code=f"PRJ-{prefix}-{user.id:04d}",
            user_id=user.id,
            domain_id=user.domain_id,
            assigned_problem_statement_id=assigned_ps_id,
            custom_topic=custom_topic,
            project_title=project_title,
            abstract=data.abstract.strip() if data.abstract else None,
            problem_statement=problem_statement,
            objectives=objectives_str,
            proposed_solution=data.proposed_solution.strip() if data.proposed_solution else None,
            technologies=tech_stack,
            technology_stack=tech_stack,
            expected_outcome=data.expected_outcome.strip() if data.expected_outcome else None,
            project_description=data.project_description.strip() if data.project_description else None,
            github_url=github_url,
            demo_url=data.demo_url.strip() if data.demo_url else None,
            status=ProjectStatus.DRAFT,
            is_submitted=False,
            current_round=1,
            draft_saved_at=datetime.now(timezone.utc),
            submitted_at=None,
        )
        db.add(project)
    else:
        # Update existing draft
        if domain_name in (DomainName.AI.value, DomainName.CYBERSECURITY.value):
            if not existing.assigned_problem_statement_id:
                statements = db.query(ProblemStatement).filter(ProblemStatement.domain_id == user.domain_id).all()
                if statements:
                    chosen = random.choice(statements)
                    existing.assigned_problem_statement_id = chosen.id
                    existing.problem_statement = chosen.detailed_description
                    existing.project_title = f"{chosen.problem_code} Solution Project"
                    chosen.is_assigned = True
                    chosen.assigned_team_id = user.id
        else:
            if data.project_title is not None:
                existing.project_title = data.project_title.strip()
            if data.custom_topic is not None:
                existing.custom_topic = data.custom_topic.strip()
            if data.problem_statement is not None:
                existing.problem_statement = data.problem_statement.strip()

        # Update solution blocks
        if data.abstract is not None:
            existing.abstract = data.abstract.strip()
        if objectives_str is not None:
            existing.objectives = objectives_str
        if data.proposed_solution is not None:
            existing.proposed_solution = data.proposed_solution.strip()
        if tech_stack is not None:
            existing.technologies = tech_stack
            existing.technology_stack = tech_stack
        if data.expected_outcome is not None:
            existing.expected_outcome = data.expected_outcome.strip()
        if data.project_description is not None:
            existing.project_description = data.project_description.strip()
        if github_url is not None:
            existing.github_url = github_url
        if data.demo_url is not None:
            existing.demo_url = data.demo_url.strip()

        existing.draft_saved_at = datetime.now(timezone.utc)
        existing.status = ProjectStatus.DRAFT
        project = existing

    db.commit()
    db.refresh(project)
    return project


def submit_final_project(db: Session, user: User, data: ProjectSubmitRequest, require_github_for_oi: bool = False) -> Project:
    """
    Final submission: validates all fields, marks is_submitted=True, status=SUBMITTED.
    The domain is always taken from the authenticated user.
    """
    if user.domain is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "message": "User has no domain assigned", "error_code": "NO_DOMAIN"},
        )

    domain_name = user.domain.name
    existing = get_user_project(db, user)

    if existing and existing.is_submitted:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"success": False, "message": "You already have a project", "error_code": "PROJECT_EXISTS"},
        )

    tech_stack = _normalize_list_or_str(data.technology_stack or data.technologies)
    objectives_str = _normalize_list_or_str(data.objectives)

    if domain_name == DomainName.OPEN_INNOVATION.value:
        topic_title = data.custom_topic or data.project_title or (existing.custom_topic if existing else None) or (existing.project_title if existing else None)
        if not topic_title:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"success": False, "message": "Open Innovation teams must provide a project topic/title", "error_code": "CUSTOM_TOPIC_REQUIRED"},
            )
        # GitHub URL is mandatory for Open Innovation only when require_github_for_oi is True
        raw_github = data.github_url or (existing.github_url if existing else None)
        if require_github_for_oi and not raw_github:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"success": False, "message": "Open Innovation teams must provide a GitHub Repository URL", "error_code": "GITHUB_REQUIRED"},
            )
        if raw_github:
            github_url = raw_github.strip()
            if not github_url.startswith("https://github.com/"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"success": False, "message": "GitHub URL must start with https://github.com/", "error_code": "INVALID_GITHUB_URL"},
                )
        else:
            github_url = None
        project_title = data.project_title.strip() if data.project_title else topic_title.strip()
        custom_topic = topic_title.strip()
        assigned_ps_id = None
        problem_statement = data.problem_statement.strip() if data.problem_statement else (existing.problem_statement if existing else None)
    else:
        # AI or Cybersecurity: retrieve assigned problem statement
        assigned_ps_id = existing.assigned_problem_statement_id if existing else None
        if not assigned_ps_id:
            statements = db.query(ProblemStatement).filter(ProblemStatement.domain_id == user.domain_id).all()
            if statements:
                chosen = random.choice(statements)
                assigned_ps_id = chosen.id
                chosen.is_assigned = True
                chosen.assigned_team_id = user.id
                problem_statement = chosen.detailed_description
                project_title = f"{chosen.problem_code} Solution Project"
            else:
                problem_statement = data.problem_statement
                project_title = data.project_title or "Project"
        else:
            ps = db.query(ProblemStatement).filter(ProblemStatement.id == assigned_ps_id).first()
            problem_statement = ps.detailed_description if ps else (existing.problem_statement if existing else None)
            project_title = f"{ps.problem_code} Solution Project" if ps else (existing.project_title if existing else "Project")

        custom_topic = None
        raw_github = data.github_url or (existing.github_url if existing else None)
        github_url = raw_github.strip() if raw_github else None

    # Validate github uniqueness
    if github_url:
        _check_github_unique(db, github_url, exclude_project_id=existing.id if existing else None)

    now = datetime.now(timezone.utc)

    if existing is None:
        prefix = "AI" if domain_name == DomainName.AI.value else ("CY" if domain_name == DomainName.CYBERSECURITY.value else "OI")
        project = Project(
            project_code=f"PRJ-{prefix}-{user.id:04d}",
            user_id=user.id,
            domain_id=user.domain_id,
            assigned_problem_statement_id=assigned_ps_id,
            custom_topic=custom_topic,
            project_title=project_title,
            abstract=data.abstract.strip() if data.abstract else None,
            problem_statement=problem_statement,
            objectives=objectives_str,
            proposed_solution=data.proposed_solution.strip() if data.proposed_solution else None,
            technologies=tech_stack,
            technology_stack=tech_stack,
            expected_outcome=data.expected_outcome.strip() if data.expected_outcome else None,
            project_description=data.project_description.strip() if data.project_description else None,
            github_url=github_url,
            demo_url=data.demo_url.strip() if data.demo_url else None,
            status=ProjectStatus.SUBMITTED,
            is_submitted=True,
            current_round=1,
            submitted_at=now,
        )
        db.add(project)
    else:
        # Update draft project with final submission data
        if assigned_ps_id is not None:
            existing.assigned_problem_statement_id = assigned_ps_id
        if custom_topic is not None:
            existing.custom_topic = custom_topic
        existing.project_title = project_title
        if problem_statement is not None:
            existing.problem_statement = problem_statement
        if data.abstract is not None:
            existing.abstract = data.abstract.strip()
        if objectives_str is not None:
            existing.objectives = objectives_str
        if data.proposed_solution is not None:
            existing.proposed_solution = data.proposed_solution.strip()
        if tech_stack is not None:
            existing.technologies = tech_stack
            existing.technology_stack = tech_stack
        if data.expected_outcome is not None:
            existing.expected_outcome = data.expected_outcome.strip()
        if data.project_description is not None:
            existing.project_description = data.project_description.strip()
        if github_url is not None:
            existing.github_url = github_url
        if data.demo_url is not None:
            existing.demo_url = data.demo_url.strip()
        existing.status = ProjectStatus.SUBMITTED
        existing.is_submitted = True
        existing.submitted_at = now
        project = existing

    db.flush()

    # Clear temporary topic locks once submitted
    db.query(TeamTopicLock).filter(TeamTopicLock.user_id == user.id).delete()

    db.commit()
    db.refresh(project)
    return project


def submit_project(db: Session, user: User, data: ProjectSubmitRequest) -> Project:
    """Legacy submit_project — now delegates to submit_final_project."""
    return submit_final_project(db, user, data)


def get_project_by_id(db: Session, project_id: int) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "message": "Project not found", "error_code": "NOT_FOUND"},
        )
    return project


def list_projects_admin(
    db: Session,
    domain_name: Optional[str] = None,
    project_status: Optional[str] = None,
    current_round: Optional[int] = None,
    user_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 20,
):
    from app.models.domain import Domain

    query = db.query(Project)
    if domain_name:
        query = query.join(Domain, Project.domain_id == Domain.id).filter(Domain.name == domain_name)
    if project_status:
        query = query.filter(Project.status == project_status)
    if current_round is not None:
        query = query.filter(Project.current_round == current_round)
    if user_id is not None:
        query = query.filter(Project.user_id == user_id)
    query = query.order_by(Project.updated_at.desc())
    return paginate(query, page, page_size)


def admin_update_project(db: Session, project_id: int, data, admin: User) -> Project:
    """Admin can edit any project field regardless of submission status."""
    project = get_project_by_id(db, project_id)

    if hasattr(data, "assigned_problem_statement_id") and data.assigned_problem_statement_id is not None:
        ps = db.query(ProblemStatement).filter(ProblemStatement.id == data.assigned_problem_statement_id).first()
        if ps:
            project.assigned_problem_statement_id = ps.id
            project.problem_statement = ps.detailed_description
            project.project_title = f"{ps.problem_code} Solution Project"
            ps.is_assigned = True

    if data.project_title is not None:
        project.project_title = data.project_title.strip()
    if data.problem_statement is not None:
        project.problem_statement = data.problem_statement.strip()
    if data.abstract is not None:
        project.abstract = data.abstract.strip()
    if data.objectives is not None:
        project.objectives = data.objectives.strip()
    if data.proposed_solution is not None:
        project.proposed_solution = data.proposed_solution.strip()
    if data.technologies is not None:
        project.technologies = data.technologies.strip()
        project.technology_stack = data.technologies.strip()
    if data.technology_stack is not None:
        project.technology_stack = data.technology_stack.strip()
        project.technologies = data.technology_stack.strip()
    if data.expected_outcome is not None:
        project.expected_outcome = data.expected_outcome.strip()
    if data.project_description is not None:
        project.project_description = data.project_description.strip()
    if data.github_url is not None:
        github_url = data.github_url.strip()
        _check_github_unique(db, github_url, exclude_project_id=project.id)
        project.github_url = github_url
    if data.demo_url is not None:
        project.demo_url = data.demo_url.strip()
    if data.status is not None:
        project.status = data.status
        if data.status == ProjectStatus.SUBMITTED or data.status != ProjectStatus.DRAFT:
            project.is_submitted = True
    if data.current_round is not None:
        project.current_round = data.current_round
    if data.domain_id is not None:
        project.domain_id = data.domain_id

    log = AuditLog(
        admin_id=admin.id,
        action="ADMIN_EDIT_PROJECT",
        target_type="project",
        target_id=project.id,
        description=f"Admin '{admin.username}' edited project '{project.project_code}'",
    )
    db.add(log)
    db.commit()
    db.refresh(project)
    return project


def get_project_problem_statement(db: Session, user: User) -> dict:
    """Return assigned detailed problem statement for AI/Cyber or custom OI statement."""
    project = get_user_project(db, user)
    domain_name = user.domain.name if user.domain else "UNKNOWN"

    if not project:
        if user.domain_id and domain_name in (DomainName.AI.value, DomainName.CYBERSECURITY.value):
            statements = db.query(ProblemStatement).filter(ProblemStatement.domain_id == user.domain_id).all()
            if statements:
                chosen = random.choice(statements)
                prefix = "AI" if domain_name == DomainName.AI.value else "CY"
                project = Project(
                    project_code=f"PRJ-{prefix}-{user.id:04d}",
                    user_id=user.id,
                    domain_id=user.domain_id,
                    assigned_problem_statement_id=chosen.id,
                    project_title=f"{chosen.problem_code} Solution Project",
                    problem_statement=chosen.detailed_description,
                    status=ProjectStatus.DRAFT,
                    is_submitted=False,
                )
                db.add(project)
                chosen.is_assigned = True
                chosen.assigned_team_id = user.id
                db.commit()
                db.refresh(project)
                return {
                    "problem_code": chosen.problem_code,
                    "detailed_description": chosen.detailed_description,
                    "domain": domain_name,
                    "title": chosen.problem_code,
                    "problem_statement": chosen.detailed_description,
                    "source": "assigned",
                }
        return {
            "problem_code": None,
            "detailed_description": None,
            "domain": domain_name,
            "title": None,
            "problem_statement": None,
            "source": "custom",
        }

    # Project exists
    ps = project.assigned_problem_statement
    if not ps and project.assigned_problem_statement_id:
        ps = db.query(ProblemStatement).filter(ProblemStatement.id == project.assigned_problem_statement_id).first()

    if ps:
        return {
            "problem_code": ps.problem_code,
            "detailed_description": ps.detailed_description,
            "domain": domain_name,
            "title": ps.problem_code,
            "problem_statement": ps.detailed_description,
            "source": "assigned",
        }

    # If AI/Cyber lacks assignment, assign one dynamically
    if domain_name in (DomainName.AI.value, DomainName.CYBERSECURITY.value):
        statements = db.query(ProblemStatement).filter(ProblemStatement.domain_id == user.domain_id).all()
        if statements:
            chosen = random.choice(statements)
            project.assigned_problem_statement_id = chosen.id
            project.problem_statement = chosen.detailed_description
            project.project_title = f"{chosen.problem_code} Solution Project"
            chosen.is_assigned = True
            chosen.assigned_team_id = user.id
            db.commit()
            db.refresh(project)
            return {
                "problem_code": chosen.problem_code,
                "detailed_description": chosen.detailed_description,
                "domain": domain_name,
                "title": chosen.problem_code,
                "problem_statement": chosen.detailed_description,
                "source": "assigned",
            }

    # Open Innovation
    return {
        "problem_code": None,
        "detailed_description": project.problem_statement or "",
        "domain": domain_name,
        "title": project.project_title or project.custom_topic or "",
        "problem_statement": project.problem_statement or "",
        "source": "custom",
    }


def get_project_timeline(db: Session, project: Project) -> list[dict]:
    """
    Construct vertical timeline showing project progress.
    """
    from app.services.review_service import get_project_reviews

    timeline = []

    # Milestone 1: Project Submitted
    submitted_date = project.submitted_at or project.updated_at
    timeline.append({
        "round_number": 1,
        "event_type": "SUBMISSION",
        "title": "Project Submitted",
        "status": "SUBMITTED",
        "comments": "Project submitted successfully and entered Round 1 review.",
        "suggested_improvements": None,
        "date": submitted_date.isoformat(),
    })

    # Milestone 2+: Reviews
    reviews = get_project_reviews(db, project.id)
    for r in reviews:
        status_label = r.status.value if hasattr(r.status, "value") else str(r.status)
        timeline.append({
            "round_number": r.round_number,
            "event_type": "REVIEW",
            "title": f"Round {r.round_number} Review Completed",
            "status": status_label,
            "comments": r.review_text,
            "suggested_improvements": r.suggested_improvements,
            "date": (r.reviewed_at or r.created_at).isoformat(),
        })

    # Milestone Final: Decision
    status_val = project.status.value if hasattr(project.status, "value") else str(project.status)
    if status_val == "COMPLETED":
        last_date = reviews[-1].reviewed_at.isoformat() if reviews else project.updated_at.isoformat()
        timeline.append({
            "round_number": project.current_round,
            "event_type": "DECISION",
            "title": "Final Decision — Completed",
            "status": "COMPLETED",
            "comments": "Project has successfully passed all review rounds and is marked as Completed.",
            "suggested_improvements": None,
            "date": last_date,
        })
    elif status_val == "REJECTED":
        last_date = reviews[-1].reviewed_at.isoformat() if reviews else project.updated_at.isoformat()
        timeline.append({
            "round_number": project.current_round,
            "event_type": "DECISION",
            "title": "Final Decision — Rejected",
            "status": "REJECTED",
            "comments": "Project was rejected during the review cycle.",
            "suggested_improvements": None,
            "date": last_date,
        })

    return timeline
