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
    import re
    import uuid
    from app.models.problem_statement import ProblemStatement, RealmEnum
    from app.models.project import Project, ProjectStatus

    # Determine realm: must be AI or CYBERSECURITY
    chosen_realm = None
    if data.realm:
        realm_str = data.realm.strip().upper()
        if realm_str in (RealmEnum.AI.value, RealmEnum.CYBERSECURITY.value):
            chosen_realm = RealmEnum(realm_str)
    elif data.domain:
        if data.domain.value in (RealmEnum.AI.value, RealmEnum.CYBERSECURITY.value):
            chosen_realm = RealmEnum(data.domain.value)

    if not chosen_realm and data.role == UserRole.USER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "message": "A valid realm (AI or CYBERSECURITY) must be selected.", "error_code": "REALM_REQUIRED"},
        )

    # Validate problem statement for USER role
    ps = None
    if data.role == UserRole.USER:
        if data.problem_statement_id:
            try:
                ps_uuid = uuid.UUID(str(data.problem_statement_id))
                ps = db.query(ProblemStatement).filter(ProblemStatement.id == ps_uuid).first()
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"success": False, "message": "Invalid problem statement ID format", "error_code": "INVALID_UUID"},
                )
        else:
            # Fallback to an active statement in the chosen realm
            ps = db.query(ProblemStatement).filter(ProblemStatement.realm == chosen_realm, ProblemStatement.status == True).first()

        if not ps:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"success": False, "message": "Team cannot register without selecting one problem statement.", "error_code": "PROBLEM_STATEMENT_REQUIRED"},
            )
        if ps.realm != chosen_realm:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"success": False, "message": f"Realm mismatch: Problem statement '{ps.problem_code}' is in realm '{ps.realm}', but '{chosen_realm.value}' was selected.", "error_code": "REALM_MISMATCH"},
            )

    domain = None
    if chosen_realm:
        domain = db.query(Domain).filter(Domain.name == chosen_realm.value).first()
    elif data.domain:
        domain = get_domain_by_name(db, data.domain)
    else:
        domain = db.query(Domain).filter(Domain.name == DomainName.AI.value).first()

    team_name = (data.team_name or data.name or "Hogwarts Team").strip()
    team_leader = (data.team_leader or data.name or team_name).strip()
    college = (data.college_name or data.organization or "").strip() or None

    # Auto-generate username if not provided
    username = data.username.strip().lower() if data.username else None
    if not username:
        clean_name = re.sub(r"[^a-z0-9_]+", "", team_name.lower().replace(" ", "_"))
        if not clean_name:
            clean_name = "team"
        candidate = f"team_{clean_name}"[:35]
        cnt = 1
        username = candidate
        while db.query(User).filter(User.username == username).first():
            username = f"{candidate}_{cnt}"
            cnt += 1

    existing_username = db.query(User).filter(User.username == username).first()
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

    # Validate team member count for USER role:
    # Team Leader (required) + Member 1 (required) + Member 2 (optional) + Member 3 (optional)
    # Total team size = 2 to 4 members maximum, including Team Leader
    if data.role == UserRole.USER and any(m is not None for m in [data.member_one, data.member_two, data.member_three]):
        if not data.member_one or not data.member_one.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"success": False, "message": "Member 1 is required. Minimum team size is 2 (Leader + Member 1).", "error_code": "MEMBER_ONE_REQUIRED"},
            )
        members = [m.strip() for m in [data.member_one, data.member_two, data.member_three] if m and m.strip()]
        if len(members) < 1 or len(members) > 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"success": False, "message": f"Total team size must be between 2 and 4 members including the leader. Current count: {len(members) + 1}", "error_code": "INVALID_MEMBER_COUNT"},
            )

    raw_pass = (data.password or "hogwarts-legacy").strip() or "hogwarts-legacy"

    user = User(
        name=team_name,
        team_name=team_name,
        team_leader=team_leader,
        member_one=data.member_one.strip() if data.member_one else None,
        member_two=data.member_two.strip() if data.member_two else None,
        member_three=data.member_three.strip() if data.member_three else None,
        college_name=college,
        organization=college,
        department=data.department.strip() if data.department else None,
        username=username,
        email=str(data.email),
        password_hash=hash_password(raw_pass),
        phone=data.phone.strip() if data.phone else None,
        domain_id=domain.id,
        role=data.role,
        status=data.status,
        edit_permission=False,
        password_reset_required=False,
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

    # For USER role, automatically create the Project linked to the chosen problem statement
    if data.role == UserRole.USER and ps:
        from app.utils.helpers import generate_project_code
        from sqlalchemy import func
        max_id = db.query(func.max(Project.id)).scalar() or 0
        proj_code = generate_project_code(max_id + 1)

        project = Project(
            project_code=proj_code,
            user_id=user.id,
            domain_id=domain.id if domain else None,
            problem_statement_id=ps.id,
            problem_code=ps.problem_code,
            realm=ps.realm,
            project_title=f"{ps.problem_code} Solution Project",
            problem_statement=ps.description,
            status=ProjectStatus.DRAFT,
            is_submitted=False,
            current_round=1,
        )
        db.add(project)
        db.flush()

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
    round_filter: Optional[int] = None,
):
    from app.models.project import Project
    query = db.query(User).filter(User.role == UserRole.USER)
    if domain_name:
        query = query.join(Domain, User.domain_id == Domain.id).filter(Domain.name == domain_name)
    if status_filter:
        query = query.filter(User.status == status_filter)
    if round_filter is not None:
        query = query.join(Project, User.id == Project.user_id).filter(Project.current_round == round_filter)
    if search:
        search_pattern = f"%{search.strip()}%"
        # Join projects to allow searching by project_code
        if round_filter is None:
            query = query.outerjoin(Project, User.id == Project.user_id)
        query = query.filter(
            or_(
                User.team_name.ilike(search_pattern),
                User.team_leader.ilike(search_pattern),
                User.username.ilike(search_pattern),
                User.name.ilike(search_pattern),
                Project.project_code.ilike(search_pattern),
            )
        )
    query = query.distinct().order_by(User.created_at.desc())
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

    if data.college_name is not None:
        user.college_name = data.college_name.strip() if data.college_name else None
        user.organization = user.college_name
    elif data.organization is not None:
        user.organization = data.organization.strip() if data.organization else None
        user.college_name = user.organization

    if data.department is not None:
        user.department = data.department.strip() if data.department else None

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


def set_team_edit_permission(db: Session, user_id: int, data, admin: User) -> User:
    from datetime import datetime, timezone
    # Accept both schema object and raw args
    edit_permission = data.edit_permission if hasattr(data, 'edit_permission') else data
    reason = data.reason if hasattr(data, 'reason') else None
    user = get_user_by_id(db, user_id)
    user.edit_permission = edit_permission
    user.edit_permission_reason = reason.strip() if reason else None
    user.edit_permission_granted_at = datetime.now(timezone.utc) if edit_permission else None

    action = "editing_permission_granted" if edit_permission else "editing_permission_revoked"
    desc = f"Admin {admin.name} ({admin.username}) {'granted' if edit_permission else 'revoked'} editing permission for team '{user.team_name}'."
    if reason:
        desc += f" Reason: {reason.strip()}"
    log = AuditLog(
        admin_id=admin.id,
        action=action,
        target_type="team",
        target_id=user.id,
        description=desc,
    )
    db.add(log)
    db.commit()
    db.refresh(user)
    return user


def reset_team_password_default(db: Session, user_id: int, admin: User) -> User:
    user = get_user_by_id(db, user_id)
    default_pass = "hogwarts-legacy"
    user.password_hash = hash_password(default_pass)
    user.password_reset_required = False

    log = AuditLog(
        admin_id=admin.id,
        action="password_reset",
        target_type="team",
        target_id=user.id,
        description=f"Admin {admin.name} ({admin.username}) reset password for team '{user.team_name}' to default.",
    )
    db.add(log)
    db.commit()
    db.refresh(user)
    return user


def bulk_set_edit_permission(db: Session, data, admin: User) -> list:
    from datetime import datetime, timezone
    team_ids = data.team_ids if hasattr(data, 'team_ids') else data
    edit_permission = data.edit_permission if hasattr(data, 'edit_permission') else True
    reason = data.reason if hasattr(data, 'reason') else None
    users = db.query(User).filter(User.id.in_(team_ids)).all()
    now = datetime.now(timezone.utc) if edit_permission else None
    r_clean = reason.strip() if reason else None
    action = "editing_permission_granted" if edit_permission else "editing_permission_revoked"

    for u in users:
        u.edit_permission = edit_permission
        u.edit_permission_reason = r_clean
        u.edit_permission_granted_at = now
        log = AuditLog(
            admin_id=admin.id,
            action=action,
            target_type="team",
            target_id=u.id,
            description=f"Bulk action: Admin {admin.username} {'granted' if edit_permission else 'revoked'} editing permission.",
        )
        db.add(log)
    db.commit()
    for u in users:
        db.refresh(u)
    return users


def bulk_reset_password(db: Session, data, admin: User) -> list:
    team_ids = data.team_ids if hasattr(data, 'team_ids') else data
    default_pass = "hogwarts-legacy"
    h = hash_password(default_pass)
    users = db.query(User).filter(User.id.in_(team_ids)).all()
    for u in users:
        u.password_hash = h
        u.password_reset_required = False
        log = AuditLog(
            admin_id=admin.id,
            action="password_reset",
            target_type="team",
            target_id=u.id,
            description=f"Bulk password reset for team '{u.team_name}' by admin {admin.username}.",
        )
        db.add(log)
    db.commit()
    for u in users:
        db.refresh(u)
    return users
