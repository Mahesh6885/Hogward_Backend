"""Review model."""
import enum
from datetime import datetime, timezone

from sqlalchemy import String, Text, DateTime, ForeignKey, Integer, UniqueConstraint, Boolean, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class ReviewStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_REVIEW = "IN_REVIEW"
    PASSED = "PASSED"
    NEEDS_IMPROVEMENT = "NEEDS_IMPROVEMENT"
    REJECTED = "REJECTED"


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    admin_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    round_number: Mapped[int] = mapped_column(Integer, nullable=False)
    review_text: Mapped[str] = mapped_column(Text, nullable=False)
    suggested_improvements: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        SAEnum(ReviewStatus, name="review_status_enum"),
        nullable=False,
        default=ReviewStatus.PENDING,
    )
    reviewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
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
    project: Mapped["Project"] = relationship("Project", back_populates="reviews")
    admin: Mapped["User"] = relationship("User", back_populates="reviews_given", foreign_keys=[admin_id])

    def __repr__(self) -> str:
        return f"<Review id={self.id} project_id={self.project_id} round={self.round_number} status={self.status}>"


class ReviewRound1(Base):
    """Review Round 1 (Problem & Plan) evaluation table — Max 60 Marks."""
    __tablename__ = "review_round_1"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    team_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    evaluator_name: Mapped[str] = mapped_column(String(100), default="Chief Arbiter", nullable=False)

    # Criteria 1–6 (1–10 each)
    score_problem_clarity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    score_solution_quality: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    score_tech_stack: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    score_idea_presentation: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    score_feasibility: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    score_confidence_qa: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    total_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)

    comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    suggestions: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="COMPLETED", nullable=False)  # DRAFT or COMPLETED
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
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
    team: Mapped["User"] = relationship("User", foreign_keys=[team_id])
    project: Mapped["Project"] = relationship("Project", foreign_keys=[project_id])


class ReviewRound2(Base):
    """Review Round 2 (Working Progress) evaluation table — Max 70 Marks."""
    __tablename__ = "review_round_2"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    team_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    review_round_1_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("review_round_1.id", ondelete="SET NULL"), nullable=True
    )
    evaluator_name: Mapped[str] = mapped_column(String(100), default="Chief Arbiter", nullable=False)

    # Criteria 1–7 (1–10 each)
    score_planning_workflow: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    score_frontend_progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    score_backend_progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    score_prototype_progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    score_technical_quality: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    score_team_collaboration: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    score_milestone_completion: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    total_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)

    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    improvement_suggestions: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="COMPLETED", nullable=False)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
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
    team: Mapped["User"] = relationship("User", foreign_keys=[team_id])
    project: Mapped["Project"] = relationship("Project", foreign_keys=[project_id])
    round_1_ref: Mapped["ReviewRound1 | None"] = relationship("ReviewRound1", foreign_keys=[review_round_1_id])


class ReviewRound3(Base):
    """Review Round 3 (Final Readiness) evaluation table — Max 70 Marks."""
    __tablename__ = "review_round_3"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    team_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    review_round_2_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("review_round_2.id", ondelete="SET NULL"), nullable=True
    )
    evaluator_name: Mapped[str] = mapped_column(String(100), default="Chief Arbiter", nullable=False)

    # Criteria 1–7 (1–10 each)
    score_tech_understanding: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    score_problem_solution_fit: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    score_innovation_creativity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    score_prototype_functionality: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    score_solution_completeness: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    score_teamwork_execution: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    score_qa_handling: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    total_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)

    final_remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    strengths: Mapped[str | None] = mapped_column(Text, nullable=True)
    weaknesses: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="COMPLETED", nullable=False)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
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
    team: Mapped["User"] = relationship("User", foreign_keys=[team_id])
    project: Mapped["Project"] = relationship("Project", foreign_keys=[project_id])
    round_2_ref: Mapped["ReviewRound2 | None"] = relationship("ReviewRound2", foreign_keys=[review_round_2_id])
