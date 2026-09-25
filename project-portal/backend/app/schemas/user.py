"""Pydantic schemas for users and teams."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator
import re

from app.models.user import UserRole, UserStatus
from app.models.domain import DomainName


class DomainBasic(BaseModel):
    id: int
    name: str
    display_name: str

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    name: Optional[str] = None
    team_name: Optional[str] = None
    team_leader: Optional[str] = None
    member_one: Optional[str] = None
    member_two: Optional[str] = None
    member_three: Optional[str] = None
    college_name: Optional[str] = None
    organization: Optional[str] = None
    department: Optional[str] = None
    academic_year: Optional[str] = None

    username: Optional[str] = None
    email: EmailStr
    password: Optional[str] = "hogwarts-legacy"
    phone: Optional[str] = None
    domain: DomainName
    role: UserRole = UserRole.USER
    status: UserStatus = UserStatus.ACTIVE

    @field_validator("username")
    @classmethod
    def username_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip().lower()
        if len(v) < 3 or len(v) > 50:
            raise ValueError("Username must be between 3 and 50 characters")
        if not re.match(r"^[a-z0-9_]+$", v):
            raise ValueError("Username may only contain lowercase letters, digits, and underscores")
        return v

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: Optional[str]) -> str:
        if not v:
            return "hogwarts-legacy"
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

    @field_validator("phone")
    @classmethod
    def phone_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if v and not re.match(r"^\+?[\d\s\-]{7,20}$", v):
            raise ValueError("Invalid phone number format")
        return v


class TeamCreate(UserCreate):
    """Alias for team creation."""
    pass


class TeamEditPermissionRequest(BaseModel):
    edit_permission: bool
    reason: Optional[str] = None


class BulkEditPermissionRequest(BaseModel):
    team_ids: list[int]
    edit_permission: bool
    reason: Optional[str] = None


class BulkPasswordResetRequest(BaseModel):
    team_ids: list[int]


class UserUpdate(BaseModel):
    name: Optional[str] = None
    team_name: Optional[str] = None
    team_leader: Optional[str] = None
    member_one: Optional[str] = None
    member_two: Optional[str] = None
    member_three: Optional[str] = None
    college_name: Optional[str] = None
    department: Optional[str] = None
    academic_year: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    organization: Optional[str] = None
    domain: Optional[DomainName] = None
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None


class TeamUpdate(UserUpdate):
    """Alias for team update."""
    pass


class UserStatusUpdate(BaseModel):
    status: UserStatus


class UserPasswordReset(BaseModel):
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class TeamResponse(BaseModel):
    id: int
    team_name: Optional[str]
    team_leader: Optional[str]
    member_one: Optional[str]
    member_two: Optional[str]
    member_three: Optional[str]
    college_name: Optional[str]
    organization: Optional[str]
    department: Optional[str]
    academic_year: Optional[str]
    username: str
    email: str
    phone: Optional[str]
    domain_id: Optional[int]
    domain: Optional[DomainBasic]
    role: UserRole
    status: UserStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserResponse(BaseModel):
    id: int
    name: str
    team_name: Optional[str] = None
    team_leader: Optional[str] = None
    member_one: Optional[str] = None
    member_two: Optional[str] = None
    member_three: Optional[str] = None
    college_name: Optional[str] = None
    department: Optional[str] = None
    academic_year: Optional[str] = None
    username: str
    email: str
    phone: Optional[str]
    organization: Optional[str]
    domain_id: Optional[int]
    domain: Optional[DomainBasic]
    role: UserRole
    status: UserStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    success: bool
    message: str
    data: list[UserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class UserSingleResponse(BaseModel):
    success: bool
    message: str
    data: UserResponse
