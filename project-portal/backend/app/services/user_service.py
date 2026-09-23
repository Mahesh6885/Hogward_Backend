"""User and team management service."""
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from app.core.security import hash_password
from app.models.user import User, UserRole, UserStatus
from app.models.domain import Domain, DomainName
from app.models.audit_log import AuditLog
from app.schemas.user import UserCreate, UserUpdate, UserStatusUpdate, UserPasswordReset
from app.utils.helpers import paginate


def get_domain_by_name(db: Session, domain_name: DomainName) -> Domain:
    domain = db.query(Domain).filter(Domain.name == domain_name.value).first()
    if not domain:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "message": f"Domain '{domain_name.value}' not found", "error_code": "DOMAIN_NOT_FOUND"},
        )
    return domain


def create_user(db: Session, data: UserCreate, created_by: User) -> User:
    """Admin creates a new team/user account."""
    domain = get_domain_by_name(db, data.domain)

    existing_username = db.query(User).filter(User.username == data.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"success": False, "message": "Username already exists", "error_code": "USERNAME_EXISTS"},
        )

    existing_email = db.query(User).filter(User.email == data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"success": False, "message": "Email already exists", "error_code": "EMAIL_EXISTS"},
        )

    team_name = (data.team_name or data.name or f"Team {data.username}").strip()
    team_leader = (data.team_leader or data.name or data.username).strip()
    college = (data.college_name or data.organization or "").strip() or None

    user = User(
        name=team_name,
        team_name=team_name,
        team_leader=team_leader,
        member_one=data.member_one.strip() if data.member_one else None,
        member_two=data.member_two.strip() if data.member_two else None,
        member_three=data.member_three.strip() if data.member_three else None,
        member_four=data.member_four.strip() if data.member_four else None,
        college_name=college,
        organization=college,
        department=data.department.strip() if data.department else None,
        academic_year=data.academic_year.strip() if data.academic_year else None,
        username=data.username,
        email=str(data.email),
        password_hash=hash_password(data.password),
        phone=data.phone.strip() if data.phone else None,
        domain_id=domain.id,
        role=data.role,
        status=data.status,
    )
    db.add(user)

    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"success": False, "message": "Username or email already exists", "error_code": "DUPLICATE"},
        )

    # Automatic Random Problem Statement Assignment on Team Creation
    import random
    from app.models.problem_statement import ProblemStatement
    from app.models.project import Project, ProjectStatus

    if data.role == UserRole.USER:
        if domain.name in (DomainName.AI.value, DomainName.CYBERSECURITY.value):
            statements = db.query(ProblemStatement).filter(ProblemStatement.domain_id == domain.id).all()
            if statements:
                chosen = random.choice(statements)
                chosen.is_assigned = True
                chosen.assigned_team_id = user.id
                prefix = "AI" if domain.name == DomainName.AI.value else "CY"
                project_code = f"PRJ-{prefix}-{user.id:04d}"
                project = Project(
                    project_code=project_code,
                    user_id=user.id,
                    domain_id=domain.id,
                    assigned_problem_statement_id=chosen.id,
                    project_title=f"{chosen.problem_code} Solution Project",
                    problem_statement=chosen.detailed_description,
                    status=ProjectStatus.DRAFT,
                    is_submitted=False,
                )
                db.add(project)
        elif domain.name == DomainName.OPEN_INNOVATION.value:
            project_code = f"PRJ-OI-{user.id:04d}"
            project = Project(
                project_code=project_code,
                user_id=user.id,
                domain_id=domain.id,
                assigned_problem_statement_id=None,
                project_title=None,
                problem_statement=None,
                status=ProjectStatus.DRAFT,
                is_submitted=False,
            )
            db.add(project)

    # Audit log
    log = AuditLog(
        admin_id=created_by.id,
        action="CREATE_USER",
        target_type="user",
        target_id=user.id,
        description=f"Admin '{created_by.username}' created team '{user.team_name}' ({user.username})",
    )
    db.add(log)
    db.commit()
    db.refresh(user)
    return user


def list_users(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    domain_name: Optional[str] = None,
    status_filter: Optional[str] = None,
    search: Optional[str] = None,
):
    query = db.query(User).filter(User.role == UserRole.USER)
    if domain_name:
        query = query.join(Domain).filter(Domain.name == domain_name)
    if status_filter:
        query = query.filter(User.status == status_filter)
    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                User.team_name.ilike(search_pattern),
                User.team_leader.ilike(search_pattern),
                User.username.ilike(search_pattern),
                User.name.ilike(search_pattern),
            )
        )
    query = query.order_by(User.created_at.desc())
    return paginate(query, page, page_size)


def get_user_by_id(db: Session, user_id: int) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "message": "User / Team not found", "error_code": "NOT_FOUND"},
        )
    return user


def update_user(db: Session, user_id: int, data: UserUpdate, admin: User) -> User:
    user = get_user_by_id(db, user_id)

    if data.team_name is not None:
        user.team_name = data.team_name.strip()
        user.name = data.team_name.strip()
    elif data.name is not None:
        user.name = data.name.strip()
        if not user.team_name:
            user.team_name = data.name.strip()

    if data.team_leader is not None:
        user.team_leader = data.team_leader.strip()
    if data.member_one is not None:
        user.member_one = data.member_one.strip() if data.member_one else None
    if data.member_two is not None:
        user.member_two = data.member_two.strip() if data.member_two else None
    if data.member_three is not None:
        user.member_three = data.member_three.strip() if data.member_three else None
    if data.member_four is not None:
        user.member_four = data.member_four.strip() if data.member_four else None

    if data.college_name is not None:
        user.college_name = data.college_name.strip() if data.college_name else None
        user.organization = user.college_name
    elif data.organization is not None:
        user.organization = data.organization.strip() if data.organization else None
        user.college_name = user.organization

    if data.department is not None:
        user.department = data.department.strip() if data.department else None
    if data.academic_year is not None:
        user.academic_year = data.academic_year.strip() if data.academic_year else None

    if data.email is not None:
        existing = db.query(User).filter(User.email == str(data.email), User.id != user_id).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"success": False, "message": "Email already in use", "error_code": "EMAIL_EXISTS"},
            )
        user.email = str(data.email)

    if data.phone is not None:
        user.phone = data.phone.strip() if data.phone else None

    if data.domain is not None:
        domain = get_domain_by_name(db, data.domain)
        user.domain_id = domain.id
        log = AuditLog(
            admin_id=admin.id,
            action="CHANGE_USER_DOMAIN",
            target_type="user",
            target_id=user.id,
            description=f"Admin '{admin.username}' changed domain of team '{user.team_name}' to '{data.domain.value}'",
        )
        db.add(log)

    if data.role is not None:
        user.role = data.role

    if data.status is not None:
        user.status = data.status

    db.commit()
    db.refresh(user)
    return user


def update_user_status(db: Session, user_id: int, data: UserStatusUpdate, admin: User) -> User:
    user = get_user_by_id(db, user_id)
    user.status = data.status

    log = AuditLog(
        admin_id=admin.id,
        action="CHANGE_USER_STATUS",
        target_type="user",
        target_id=user.id,
        description=f"Admin '{admin.username}' set status of team '{user.team_name}' ({user.username}) to '{data.status.value}'",
    )
    db.add(log)
    db.commit()
    db.refresh(user)
    return user


def reset_user_password(db: Session, user_id: int, data: UserPasswordReset, admin: User) -> User:
    user = get_user_by_id(db, user_id)
    user.password_hash = hash_password(data.new_password)

    log = AuditLog(
        admin_id=admin.id,
        action="RESET_USER_PASSWORD",
        target_type="user",
        target_id=user.id,
        description=f"Admin '{admin.username}' reset password for '{user.username}'",
    )
    db.add(log)
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: int, admin: User) -> None:
    from app.models.problem_statement import ProblemStatement
    from app.models.project import Project
    from app.models.review import Review

    user = get_user_by_id(db, user_id)
    if user.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "message": "You cannot delete your own account", "error_code": "SELF_DELETE"},
        )

    # Delete projects and reviews associated with this user
    for prj in list(user.projects):
        db.query(Review).filter(Review.project_id == prj.id).delete()
        if prj.assigned_problem_statement_id:
            other_using = db.query(Project).filter(
                Project.assigned_problem_statement_id == prj.assigned_problem_statement_id,
                Project.id != prj.id,
            ).first()
            if not other_using:
                ps = db.query(ProblemStatement).filter(ProblemStatement.id == prj.assigned_problem_statement_id).first()
                if ps:
                    ps.is_assigned = False
                    ps.assigned_team_id = None
        db.delete(prj)

    # Release any problem statements directly pointing to this team
    db.query(ProblemStatement).filter(ProblemStatement.assigned_team_id == user_id).update({
        "is_assigned": False,
        "assigned_team_id": None,
    })

    log = AuditLog(
        admin_id=admin.id,
        action="DELETE_USER",
        target_type="user",
        target_id=user.id,
        description=f"Admin '{admin.username}' deleted user '{user.username}'",
    )
    db.add(log)
    db.delete(user)
    db.commit()
