"""User model."""
import enum
from datetime import datetime, timezone

from sqlalchemy import String, Text, DateTime, ForeignKey, Enum as SAEnum, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    USER = "USER"


class UserStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    organization: Mapped[str | None] = mapped_column(String(255), nullable=True)
    college_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    department: Mapped[str | None] = mapped_column(String(255), nullable=True)
    team_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    team_leader: Mapped[str | None] = mapped_column(String(255), nullable=True)
    member_one: Mapped[str | None] = mapped_column(String(255), nullable=True)
    member_two: Mapped[str | None] = mapped_column(String(255), nullable=True)
    member_three: Mapped[str | None] = mapped_column(String(255), nullable=True)
    domain_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("domains.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    role: Mapped[str] = mapped_column(
        SAEnum(UserRole, name="user_role_enum"), nullable=False, default=UserRole.USER
    )
    status: Mapped[str] = mapped_column(
        SAEnum(UserStatus, name="user_status_enum"), nullable=False, default=UserStatus.ACTIVE
    )
    edit_permission: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    edit_permission_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    edit_permission_granted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    session_last_active: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    password_reset_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    domain: Mapped["Domain | None"] = relationship("Domain", back_populates="users")
    projects: Mapped[list["Project"]] = relationship("Project", back_populates="user", foreign_keys="Project.user_id")
    reviews_given: Mapped[list["Review"]] = relationship("Review", back_populates="admin", foreign_keys="Review.admin_id")
    audit_logs: Mapped[list["AuditLog"]] = relationship("AuditLog", back_populates="admin")

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username} role={self.role}>"
