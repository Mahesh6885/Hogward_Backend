"""Domain model."""
import enum
from datetime import datetime, timezone

from sqlalchemy import String, Text, DateTime, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class DomainName(str, enum.Enum):
    AI = "AI"
    CYBERSECURITY = "CYBERSECURITY"
    OPEN_INNOVATION = "OPEN_INNOVATION"

    @property
    def display_name(self) -> str:
        mapping = {
            "AI": "AI",
            "CYBERSECURITY": "Cybersecurity",
            "OPEN_INNOVATION": "Open Innovation",
        }
        return mapping[self.value]


class Domain(Base):
    __tablename__ = "domains"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(
        SAEnum(DomainName, name="domain_name_enum"), unique=True, nullable=False, index=True
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    users: Mapped[list["User"]] = relationship("User", back_populates="domain")
    projects: Mapped[list["Project"]] = relationship("Project", back_populates="domain")

    def __repr__(self) -> str:
        return f"<Domain id={self.id} name={self.name}>"
