"""Problem Statement model for predefined domain challenges."""
from datetime import datetime, timezone

from sqlalchemy import String, Text, DateTime, ForeignKey, Integer, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class ProblemStatement(Base):
    __tablename__ = "problem_statements"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    problem_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    domain_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("domains.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    detailed_description: Mapped[str] = mapped_column(Text, nullable=False)
    is_assigned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    assigned_team_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    domain: Mapped["Domain"] = relationship("Domain")
    projects: Mapped[list["Project"]] = relationship("Project", back_populates="assigned_problem_statement")

    def __repr__(self) -> str:
        return f"<ProblemStatement id={self.id} code={self.problem_code} domain_id={self.domain_id}>"
