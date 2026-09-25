"""User and team management service."""
from datetime import datetime, timezone
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

    # Determine realm or domain: AI, CYBERSECURITY, or OPEN_INNOVATION
    chosen_realm = None
    is_open_innovation = False

    domain_val = None
    if data.domain:
        domain_val = data.domain.value if hasattr(data.domain, "value") else str(data.domain).strip().upper()

    realm_candidate = (data.realm.strip().upper() if data.realm else None) or domain_val

    if realm_candidate in (RealmEnum.AI.value, "AI"):
        chosen_realm = RealmEnum.AI
    elif realm_candidate in (RealmEnum.CYBERSECURITY.value, "CYBERSECURITY"):
        chosen_realm = RealmEnum.CYBERSECURITY
    elif realm_candidate in (DomainName.OPEN_INNOVATION.value, "OPEN_INNOVATION", "OPEN INNOVATION", "OI"):
        is_open_innovation = True

    if not chosen_realm and not is_open_innovation and data.role == UserRole.USER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "message": "A valid domain (AI, CYBERSECURITY, or OPEN_INNOVATION) must be selected.", "error_code": "DOMAIN_REQUIRED"},
        )

    # Problem statement assignment for USER role (only for AI / CYBERSECURITY)
    ps = None
    if data.role == UserRole.USER and not is_open_innovation:
        if data.problem_statement_id and str(data.problem_statement_id).strip():
            try:
                ps_uuid = uuid.UUID(str(data.problem_statement_id).strip())
                ps = db.query(ProblemStatement).filter(ProblemStatement.id == ps_uuid).first()
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"success": False, "message": "Invalid problem statement ID format", "error_code": "INVALID_UUID"},
                )
            if ps and ps.realm != chosen_realm:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"success": False, "message": f"Realm mismatch: Problem statement '{ps.problem_code}' is in realm '{ps.realm}', but '{chosen_realm.value}' was selected.", "error_code": "REALM_MISMATCH"},
                )

        if not ps and chosen_realm:
            # Automatic fair balanced rotation assignment from chosen realm!
            from app.services.problem_statement_service import assign_balanced_problem_statement
            ps = assign_balanced_problem_statement(db, chosen_realm)

    domain = None
    if chosen_realm:
        domain = db.query(Domain).filter(Domain.name == chosen_realm.value).first()
        if not domain:
            domain = Domain(name=chosen_realm.value, description=f"{chosen_realm.value} domain")
            db.add(domain)
            db.flush()
    elif is_open_innovation:
        domain = db.query(Domain).filter(Domain.name == DomainName.OPEN_INNOVATION.value).first()
        if not domain:
            domain = Domain(
                name=DomainName.OPEN_INNOVATION.value,
                description="Open Innovation — open track for creative, cross-disciplinary technical solutions."
            )
            db.add(domain)
            db.flush()
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

        now_utc = datetime.now(timezone.utc)
        project = Project(
            project_code=proj_code,
            user_id=user.id,
            domain_id=domain.id if domain else None,
            problem_statement_id=ps.id,
            problem_code=ps.problem_code,
            realm=ps.realm,
            project_title=ps.title,
            problem_statement=ps.description,
            status=ProjectStatus.DRAFT,
            is_submitted=False,
            current_round=1,
            assigned_at=now_utc,
            created_at=now_utc,
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
    from app.models.project import Project
    from app.models.review import Review

    user = get_user_by_id(db, user_id)
    if user.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "message": "You cannot delete your own account", "error_code": "SELF_DELETE"},
        )

    # 1. Delete reviews associated with any project of this user, then delete the projects
    user_projects = db.query(Project).filter(Project.user_id == user.id).all()
    for prj in user_projects:
        db.query(Review).filter(Review.project_id == prj.id).delete()
        db.delete(prj)
    db.flush()

    # 2. If this user ever authored reviews as admin/reviewer, clean those up
    db.query(Review).filter(Review.admin_id == user.id).delete()

    # 3. If this user was referenced as admin in audit_logs, nullify foreign key
    db.query(AuditLog).filter(AuditLog.admin_id == user.id).update(
        {"admin_id": None}, synchronize_session=False
    )

    # 4. Log the deletion action
    username_deleted = user.username
    team_deleted = user.team_name or user.name
    log = AuditLog(
        admin_id=admin.id,
        action="DELETE_USER",
        target_type="user",
        target_id=user.id,
        description=f"Admin '{admin.username}' deleted team/user '{username_deleted}' ({team_deleted})",
    )
    db.add(log)

    # 5. Delete user and commit transaction
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
