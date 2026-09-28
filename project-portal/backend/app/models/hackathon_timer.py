"""Hackathon Timer model for 24-hour countdown management."""
import enum
from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base


class TimerStatus(str, enum.Enum):
    NOT_STARTED = "NOT_STARTED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"


class HackathonTimer(Base):
    __tablename__ = "hackathon_timer"

    id: Mapped[int] = mapped_column(primary_key=True)
    timer_status: Mapped[str] = mapped_column(String(20), default=TimerStatus.NOT_STARTED.value, nullable=False)
    hackathon_start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    hackathon_end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    remaining_seconds: Mapped[int] = mapped_column(Integer, default=86400, nullable=False)
    total_duration_seconds: Mapped[int] = mapped_column(Integer, default=86400, nullable=False)
    last_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
