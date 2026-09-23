"""Team topic locking model."""
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class TeamTopicLock(Base):
    __tablename__ = "team_topic_locks"
    __table_args__ = (
        UniqueConstraint("user_id", "topic_id", name="uq_team_topic_lock"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    topic_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("topics.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", backref="topic_locks")
    topic: Mapped["Topic"] = relationship("Topic")

    def __repr__(self) -> str:
        return f"<TeamTopicLock user_id={self.user_id} topic_id={self.topic_id}>"
