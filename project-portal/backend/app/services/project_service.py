"""Project creation, management, and timeline service."""
from datetime import datetime, timezone
from typing import Optional, Union

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from app.core.config import settings
from app.models.domain import Domain, DomainName
from app.models.project import Project, ProjectStatus
from app.models.problem_statement import ProblemStatement, RealmEnum
from app.models.user import User
from app.models.audit_log import AuditLog
from app.schemas.project import ProjectSubmitRequest, ProjectDraftRequest, AdminProjectUpdateRequest
from app.utils.helpers import paginate, generate_project_code


def _next_project_code(db: Session) -> str:
    """Generate the next sequential project code."""
    max_id = db.query(func.max(Project.id)).scalar() or 0
    return generate_project_code(max_id + 1)


def _normalize_list_or_str(val: Optional[Union[str, list]]) -> Optional[str]:
    """Normalize list or str into stored string."""
    if val is None:
        return None
    if isinstance(val, list):
        return "\n".join(str(v) for v in val)
    return str(val).strip() if val else None


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
    Raises HTTP 403 if project is already fully submitted and not granted edit permission.
    """
    existing = get_user_project(db, user)

    if existing and existing.is_submitted and not getattr(user, "edit_permission", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"success": False, "message": "Submitted projects cannot be edited unless editing permission is granted by the Administrator.", "error_code": "ALREADY_SUBMITTED"},
        )

    tech_stack = _normalize_list_or_str(data.technology_stack or data.technologies)
    objectives_str = _normalize_list_or_str(data.objectives)

    github_url = None
    if data.github_url is not None:
        raw_github = data.github_url.strip()
        if raw_github:
            if not raw_github.startswith("https://github.com/"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"success": False, "message": "GitHub URL must start with https://github.com/", "error_code": "INVALID_GITHUB_URL"},
                )
            _check_github_unique(db, raw_github, exclude_project_id=existing.id if existing else None)
            github_url = raw_github

    if existing is None:
        is_oi = bool(user.domain and user.domain.name == DomainName.OPEN_INNOVATION.value)
        if is_oi:
            realm = None
            ps = None
            prefix = "OI"
            p_title = (data.project_title or "Open Innovation Project").strip()
            p_desc = (data.problem_statement or "").strip()
        else:
            realm = RealmEnum.AI if (user.domain and user.domain.name == DomainName.AI.value) else RealmEnum.CYBERSECURITY
            ps = db.query(ProblemStatement).filter(ProblemStatement.realm == realm, ProblemStatement.status == True).first()
            prefix = "AI" if realm == RealmEnum.AI else "CY"
            p_title = data.project_title or (f"{ps.problem_code} Solution Project" if ps else "Project")
            p_desc = ps.description if ps else (data.problem_statement or None)

        project = Project(
            project_code=f"PRJ-{prefix}-{user.id:04d}",
            user_id=user.id,
            domain_id=user.domain_id,
            problem_statement_id=ps.id if ps else None,
            problem_code=ps.problem_code if ps else None,
            realm=ps.realm if ps else realm,
            project_title=p_title,
            abstract=data.abstract.strip() if data.abstract else None,
            problem_statement=p_desc,
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
        is_oi = bool(user.domain and user.domain.name == DomainName.OPEN_INNOVATION.value)
        if data.project_title is not None:
            existing.project_title = data.project_title.strip()
        if data.problem_statement is not None and (is_oi or not existing.problem_statement_id):
            existing.problem_statement = data.problem_statement.strip()
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
        if not existing.is_submitted:
            existing.status = ProjectStatus.DRAFT
        project = existing

    db.commit()
    db.refresh(project)
    return project


def submit_final_project(
    db: Session,
    user: User,
    data: ProjectSubmitRequest,
    require_github_for_oi: bool = False,
) -> Project:
    """
    Final submission: validates all fields, marks is_submitted=True, status=SUBMITTED.
    """
    existing = get_user_project(db, user)

    if existing and existing.is_submitted and not getattr(user, "edit_permission", False):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"success": False, "message": "You already have a project for this user. Multiple projects are not allowed. Editing requires admin permission.", "error_code": "PROJECT_EXISTS"},
        )

    tech_stack = _normalize_list_or_str(data.technology_stack or data.technologies)
    objectives_str = _normalize_list_or_str(data.objectives)

    raw_github = data.github_url or (existing.github_url if existing else None)
    github_url = None
    if raw_github:
        github_url = raw_github.strip()
        if not github_url.startswith("https://github.com/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"success": False, "message": "GitHub URL must start with https://github.com/", "error_code": "INVALID_GITHUB_URL"},
            )
        _check_github_unique(db, github_url, exclude_project_id=existing.id if existing else None)

    is_oi = bool(user.domain and user.domain.name == DomainName.OPEN_INNOVATION.value)
    if require_github_for_oi and is_oi and not github_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "message": "GitHub repository URL is mandatory for Open Innovation projects", "error_code": "GITHUB_URL_REQUIRED"},
        )

    now = datetime.now(timezone.utc)

    if existing is None:
        is_oi = bool(user.domain and user.domain.name == DomainName.OPEN_INNOVATION.value)
        if is_oi:
            realm = None
            ps = None
            prefix = "OI"
            p_title = (data.project_title or "Open Innovation Project").strip()
            p_desc = (data.problem_statement or "").strip()
        else:
            realm = RealmEnum.AI if (user.domain and user.domain.name == DomainName.AI.value) else RealmEnum.CYBERSECURITY
            ps = db.query(ProblemStatement).filter(ProblemStatement.realm == realm, ProblemStatement.status == True).first()
            prefix = "AI" if realm == RealmEnum.AI else "CY"
            p_title = data.project_title or (f"{ps.problem_code} Solution Project" if ps else "Project")
            p_desc = ps.description if ps else (data.problem_statement or None)

        project = Project(
            project_code=f"PRJ-{prefix}-{user.id:04d}",
            user_id=user.id,
            domain_id=user.domain_id,
            problem_statement_id=ps.id if ps else None,
            problem_code=ps.problem_code if ps else None,
            realm=ps.realm if ps else realm,
            project_title=p_title,
            abstract=data.abstract.strip() if data.abstract else None,
            problem_statement=p_desc,
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
        is_oi = bool(user.domain and user.domain.name == DomainName.OPEN_INNOVATION.value)
        if data.project_title:
            existing.project_title = data.project_title.strip()
        if data.problem_statement and (is_oi or not existing.problem_statement_id):
            existing.problem_statement = data.problem_statement.strip()
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

        if not existing.domain_id and user.domain_id:
            existing.domain_id = user.domain_id
        existing.status = ProjectStatus.SUBMITTED
        existing.is_submitted = True
        existing.submitted_at = now
        project = existing

    # Revoke editing permission automatically and record audit log
    if getattr(user, "edit_permission", False):
        user.edit_permission = False
        user.edit_permission_reason = None
        db.add(AuditLog(
            action="PROJECT_RESUBMITTED",
            admin_id=None,
            target_type="project",
            target_id=project.id,
            description=f"Team '{user.team_name}' resubmitted project {project.project_code}. Edit permission revoked automatically."
        ))

    db.commit()
    db.refresh(project)
    return project


def submit_project(
    db: Session,
    user: User,
    data: ProjectSubmitRequest,
    require_github_for_oi: bool = False,
) -> Project:
    """Submit project handler."""
    return submit_final_project(db, user, data, require_github_for_oi=require_github_for_oi)


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
    page: int = 1,
    page_size: int = 20,
    domain: Optional[str] = None,
    realm: Optional[str] = None,
    status_filter: Optional[str] = None,
    round_filter: Optional[int] = None,
    search: Optional[str] = None,
    user_id: Optional[int] = None,
):
    query = db.query(Project)
    if user_id:
        query = query.filter(Project.user_id == user_id)
    if realm:
        query = query.filter(Project.realm == realm)
    elif domain:
        query = query.filter(or_(Project.realm == domain, Project.domain.has(name=domain)))
    if status_filter:
        query = query.filter(Project.status == status_filter)
    if round_filter is not None:
        query = query.filter(Project.current_round == round_filter)
    if search:
        pattern = f"%{search.strip()}%"
        query = query.join(User, Project.user_id == User.id).filter(
            or_(
                Project.project_code.ilike(pattern),
                Project.problem_code.ilike(pattern),
                Project.project_title.ilike(pattern),
                User.team_name.ilike(pattern),
                User.team_leader.ilike(pattern),
                User.username.ilike(pattern),
            )
        )
    query = query.order_by(Project.updated_at.desc())
    return paginate(query, page, page_size)


def admin_update_project(
    db: Session,
    project_id: int,
    data: Optional[Union[AdminProjectUpdateRequest, dict, str]] = None,
    admin: Optional[User] = None,
    project_title: Optional[str] = None,
    current_round: Optional[int] = None,
    status_val: Optional[str] = None,
) -> Project:
    """Admin updates any project field (including locked fields) regardless of submission status."""
    project = get_project_by_id(db, project_id)

    # If data is passed as a string, it might be legacy project_title positional argument
    if isinstance(data, str):
        project_title = data
        data = None

    updates = {}
    if data is not None:
        if hasattr(data, "model_dump"):
            updates = data.model_dump(exclude_unset=True)
        elif isinstance(data, dict):
            updates = dict(data)

    if project_title is not None:
        updates["project_title"] = project_title
    if current_round is not None:
        updates["current_round"] = current_round
    if status_val is not None:
        updates["status"] = status_val

    # Apply project_title
    if "project_title" in updates and updates["project_title"] is not None:
        project.project_title = str(updates["project_title"]).strip()

    # Apply github_url with uniqueness validation
    if "github_url" in updates:
        gh = updates["github_url"]
        if gh:
            gh_clean = str(gh).strip()
            _check_github_unique(db, gh_clean, exclude_project_id=project.id)
            project.github_url = gh_clean
        else:
            project.github_url = None

    # Apply domain
    if "domain" in updates and updates["domain"] is not None:
        dom_name = str(updates["domain"]).strip()
        dom = db.query(Domain).filter(Domain.name == dom_name).first()
        if dom:
            project.domain_id = dom.id

    # Apply status
    if "status" in updates and updates["status"] is not None:
        st = updates["status"]
        if hasattr(st, "value"):
            project.status = st.value
        else:
            project.status = str(st)

    # Apply current_round
    if "current_round" in updates and updates["current_round"] is not None:
        project.current_round = int(updates["current_round"])

    # Optional text fields
    for field in [
        "problem_statement",
        "abstract",
        "objectives",
        "proposed_solution",
        "technologies",
        "technology_stack",
        "expected_outcome",
        "project_description",
        "demo_url",
    ]:
        if field in updates and updates[field] is not None:
            setattr(project, field, str(updates[field]).strip())

    if "realm" in updates and updates["realm"] is not None:
        project.realm = updates["realm"]

    if "problem_statement_id" in updates and updates["problem_statement_id"] is not None:
        project.problem_statement_id = updates["problem_statement_id"]

    if admin:
        log = AuditLog(
            admin_id=admin.id,
            action="ADMIN_UPDATE_PROJECT",
            target_type="project",
            target_id=project.id,
            description=f"Admin '{admin.username}' updated fields for project '{project.project_code}'",
        )
        db.add(log)

    db.commit()
    db.refresh(project)
    return project


def get_project_problem_statement(db: Session, user: User) -> dict:
    """Retrieve the problem statement for the current user's project."""
    project = get_user_project(db, user)
    ps = None
    if project:
        ps = project.problem_statement_rel
        if not ps and project.problem_statement_id:
            ps = db.query(ProblemStatement).filter(ProblemStatement.id == project.problem_statement_id).first()
        if not ps and project.problem_code:
            ps = db.query(ProblemStatement).filter(ProblemStatement.problem_code == project.problem_code).first()

    # If project doesn't have an assigned statement yet, auto-assign from the user's realm
    if not ps and project and not project.problem_statement_id:
        realm_str = project.realm or (user.domain.name if user.domain else "AI")
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
        return {
            "id": str(ps.id),
            "problem_code": ps.problem_code,
            "realm": ps.realm,
            "title": ps.title,
            "description": ps.description,
            "detailed_description": ps.description,
            "problem_statement": ps.description,
            "difficulty": ps.difficulty,
            "status": ps.status,
            "source": "official",
        }

    return {
        "id": str(project.problem_statement_id) if (project and project.problem_statement_id) else None,
        "problem_code": project.problem_code if project else "—",
        "realm": project.realm if project else (user.domain.name if user.domain else "AI"),
        "title": project.project_title if project else "Hogwarts Legacy 5.0 Challenge",
        "description": project.problem_statement if (project and project.problem_statement) else "Official problem statement scope.",
        "detailed_description": project.problem_statement if (project and project.problem_statement) else "Official problem statement scope.",
        "problem_statement": project.problem_statement if (project and project.problem_statement) else "Official problem statement scope.",
        "difficulty": "INTERMEDIATE",
        "status": True,
        "source": "assigned",
    }


def get_project_timeline(db: Session, project: Project) -> list[dict]:
    """Construct vertical timeline showing project progress."""
    from app.services.review_service import get_project_reviews

    timeline = []
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
