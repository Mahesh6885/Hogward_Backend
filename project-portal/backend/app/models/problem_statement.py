"""Problem Statement model for Hogwarts Legacy 5.0."""
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Text, DateTime, Boolean, Enum as SAEnum, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class GUID(TypeDecorator):
    """Platform-independent GUID/UUID type.
    Uses PostgreSQL's native UUID type, otherwise uses CHAR(36), storing as stringified hex.
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(str(value))


class RealmEnum(str, enum.Enum):
    AI = "AI"
    CYBERSECURITY = "CYBERSECURITY"


class DifficultyEnum(str, enum.Enum):
    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"


class ProblemStatement(Base):
    __tablename__ = "problem_statements"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    problem_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    realm: Mapped[str] = mapped_column(
        SAEnum(RealmEnum, name="realm_enum"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[str] = mapped_column(
        SAEnum(DifficultyEnum, name="difficulty_enum"),
        nullable=False,
        default=DifficultyEnum.INTERMEDIATE,
        index=True,
    )
    status: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    projects: Mapped[list["Project"]] = relationship("Project", back_populates="problem_statement_rel")

    def __repr__(self) -> str:
        return f"<ProblemStatement code={self.problem_code} realm={self.realm} title={self.title[:30]}>"
