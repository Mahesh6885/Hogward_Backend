"""Project model."""
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Text, DateTime, ForeignKey, Integer, UniqueConstraint, Boolean, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.problem_statement import GUID, RealmEnum


class ProjectStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"


class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_projects_user_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    domain_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("domains.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Refactored Problem Statement relationship
    problem_statement_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("problem_statements.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    problem_code: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    realm: Mapped[str | None] = mapped_column(
        SAEnum(RealmEnum, name="realm_enum"), nullable=True, index=True
    )

    assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    project_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    abstract: Mapped[str | None] = mapped_column(Text, nullable=True)
    problem_statement: Mapped[str | None] = mapped_column(Text, nullable=True)
    objectives: Mapped[str | None] = mapped_column(Text, nullable=True)
    proposed_solution: Mapped[str | None] = mapped_column(Text, nullable=True)
    technologies: Mapped[str | None] = mapped_column(Text, nullable=True)
    technology_stack: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_outcome: Mapped[str | None] = mapped_column(Text, nullable=True)
    project_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    github_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    demo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_submitted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(
        SAEnum(ProjectStatus, name="project_status_enum"),
        nullable=False,
        default=ProjectStatus.SUBMITTED,
    )
    current_round: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    draft_saved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="projects", foreign_keys=[user_id])
    domain: Mapped["Domain | None"] = relationship("Domain", back_populates="projects")
    problem_statement_rel: Mapped["ProblemStatement | None"] = relationship(
        "ProblemStatement", back_populates="projects"
    )
    reviews: Mapped[list["Review"]] = relationship(
        "Review", back_populates="project", cascade="all, delete-orphan", order_by="Review.round_number"
    )
    reviews_round_1: Mapped[list["ReviewRound1"]] = relationship(
        "ReviewRound1", back_populates="project", cascade="all, delete-orphan", order_by="ReviewRound1.id.desc()"
    )
    reviews_round_2: Mapped[list["ReviewRound2"]] = relationship(
        "ReviewRound2", back_populates="project", cascade="all, delete-orphan", order_by="ReviewRound2.id.desc()"
    )
    reviews_round_3: Mapped[list["ReviewRound3"]] = relationship(
        "ReviewRound3", back_populates="project", cascade="all, delete-orphan", order_by="ReviewRound3.id.desc()"
    )

    def __repr__(self) -> str:
        return f"<Project id={self.id} code={self.project_code} status={self.status}>"
