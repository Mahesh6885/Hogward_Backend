"""Authentication routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User, UserStatus
from app.schemas.auth import LoginRequest, LoginResponse, LoginResponseData, LoginResponseUser, MeResponse
from app.services.auth_service import authenticate_user, create_token_for_user, build_user_domain_display

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse, status_code=200)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate with username + password. Returns JWT access token."""
    user = authenticate_user(db, data.username.strip(), data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"success": False, "message": "Invalid username or password", "error_code": "INVALID_CREDENTIALS"},
        )

    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"success": False, "message": "Account is inactive. Contact administrator.", "error_code": "ACCOUNT_INACTIVE"},
        )

    token = create_token_for_user(user)
    domain_display = build_user_domain_display(user)

    return LoginResponse(
        success=True,
        message="Login successful",
        data=LoginResponseData(
            access_token=token,
            token_type="bearer",
            user=LoginResponseUser(
                id=user.id,
                name=user.name,
                username=user.username,
                role=user.role,
                domain=domain_display,
                edit_permission=getattr(user, "edit_permission", False),
                edit_permission_reason=getattr(user, "edit_permission_reason", None),
            ),
        ),
    )


@router.get("/me", response_model=MeResponse, status_code=200)
def get_me(current_user: User = Depends(get_current_user)):
    """Return current authenticated user information."""
    from app.services.auth_service import build_user_domain_display
    domain_display = build_user_domain_display(current_user)
    return MeResponse(
        success=True,
        message="User retrieved successfully",
        data=LoginResponseUser(
            id=current_user.id,
            name=current_user.name,
            username=current_user.username,
            role=current_user.role,
            domain=domain_display,
            edit_permission=getattr(current_user, "edit_permission", False),
            edit_permission_reason=getattr(current_user, "edit_permission_reason", None),
        ),
    )
