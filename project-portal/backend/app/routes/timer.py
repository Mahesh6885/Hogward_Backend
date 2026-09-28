"""Hackathon Countdown Timer API routes."""
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.core.dependencies import require_admin
from app.models.hackathon_timer import HackathonTimer, TimerStatus
from app.models.user import User

router = APIRouter(prefix="/api/timer", tags=["Hackathon Timer"])

TOTAL_SECONDS_24H = 24 * 3600  # 86400 seconds


def get_or_create_timer(db: Session) -> HackathonTimer:
    """Retrieve the singleton hackathon timer row, or initialize it."""
    timer = db.query(HackathonTimer).filter(HackathonTimer.id == 1).first()
    if not timer:
        timer = HackathonTimer(
            id=1,
            timer_status=TimerStatus.NOT_STARTED.value,
            hackathon_start_time=None,
            hackathon_end_time=None,
            remaining_seconds=TOTAL_SECONDS_24H,
            total_duration_seconds=TOTAL_SECONDS_24H,
            last_updated_at=datetime.now(timezone.utc),
        )
        db.add(timer)
        db.commit()
        db.refresh(timer)
    return timer


def sync_timer_state(timer: HackathonTimer, db: Session) -> dict:
    """Calculate the precise real-time state of the countdown."""
    now = datetime.now(timezone.utc)

    if timer.timer_status == TimerStatus.RUNNING.value:
        if timer.hackathon_end_time:
            diff = (timer.hackathon_end_time - now).total_seconds()
            rem = int(diff)
            if rem <= 0:
                timer.timer_status = TimerStatus.COMPLETED.value
                timer.remaining_seconds = 0
                timer.last_updated_at = now
                db.commit()
                db.refresh(timer)
            else:
                timer.remaining_seconds = rem
        else:
            timer.hackathon_end_time = now + timedelta(seconds=timer.remaining_seconds)
            db.commit()
            db.refresh(timer)

    return {
        "timer_status": timer.timer_status,
        "hackathon_start_time": timer.hackathon_start_time.isoformat() if timer.hackathon_start_time else None,
        "hackathon_end_time": timer.hackathon_end_time.isoformat() if timer.hackathon_end_time else None,
        "remaining_seconds": max(0, timer.remaining_seconds),
        "total_duration_seconds": timer.total_duration_seconds,
        "server_time": now.isoformat(),
    }


@router.get("", summary="Get synchronized hackathon countdown state")
def get_timer(db: Session = Depends(get_db)):
    """Return the current synchronized countdown timer status for participants and admins."""
    timer = get_or_create_timer(db)
    data = sync_timer_state(timer, db)
    return {"success": True, "data": data}


@router.post("/start", summary="Start hackathon countdown (Admin only)")
def start_timer(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Start the official 24-hour hackathon countdown."""
    timer = get_or_create_timer(db)
    now = datetime.now(timezone.utc)

    # If already running, return current state
    if timer.timer_status == TimerStatus.RUNNING.value:
        return {"success": True, "message": "Hackathon is already running.", "data": sync_timer_state(timer, db)}

    duration = timer.remaining_seconds if (timer.timer_status == TimerStatus.PAUSED.value and timer.remaining_seconds > 0) else TOTAL_SECONDS_24H

    timer.timer_status = TimerStatus.RUNNING.value
    timer.hackathon_start_time = now if not timer.hackathon_start_time else timer.hackathon_start_time
    timer.hackathon_end_time = now + timedelta(seconds=duration)
    timer.remaining_seconds = duration
    timer.total_duration_seconds = TOTAL_SECONDS_24H
    timer.last_updated_at = now

    db.commit()
    db.refresh(timer)
    return {"success": True, "message": "Hackathon countdown started successfully.", "data": sync_timer_state(timer, db)}


@router.post("/pause", summary="Pause hackathon countdown (Admin only)")
def pause_timer(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Freeze the countdown timer globally."""
    timer = get_or_create_timer(db)
    now = datetime.now(timezone.utc)

    if timer.timer_status == TimerStatus.RUNNING.value:
        if timer.hackathon_end_time:
            rem = max(0, int((timer.hackathon_end_time - now).total_seconds()))
            timer.remaining_seconds = rem
        timer.timer_status = TimerStatus.PAUSED.value
        timer.last_updated_at = now
        db.commit()
        db.refresh(timer)
        return {"success": True, "message": "Time frozen by the Ministry.", "data": sync_timer_state(timer, db)}

    return {"success": True, "message": f"Timer is not running (status: {timer.timer_status}).", "data": sync_timer_state(timer, db)}


@router.post("/resume", summary="Resume paused countdown (Admin only)")
def resume_timer(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Resume countdown from paused time."""
    timer = get_or_create_timer(db)
    now = datetime.now(timezone.utc)

    if timer.timer_status == TimerStatus.PAUSED.value:
        rem = timer.remaining_seconds if timer.remaining_seconds > 0 else TOTAL_SECONDS_24H
        timer.timer_status = TimerStatus.RUNNING.value
        timer.hackathon_end_time = now + timedelta(seconds=rem)
        timer.last_updated_at = now
        db.commit()
        db.refresh(timer)
        return {"success": True, "message": "Hackathon countdown resumed.", "data": sync_timer_state(timer, db)}

    return {"success": True, "message": f"Timer is not paused (status: {timer.timer_status}).", "data": sync_timer_state(timer, db)}


@router.post("/stop", summary="Stop hackathon immediately (Admin only)")
def stop_timer(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    """End countdown immediately and mark hackathon as completed."""
    timer = get_or_create_timer(db)
    now = datetime.now(timezone.utc)

    timer.timer_status = TimerStatus.COMPLETED.value
    timer.remaining_seconds = 0
    timer.last_updated_at = now
    db.commit()
    db.refresh(timer)
    return {"success": True, "message": "Hackathon completed.", "data": sync_timer_state(timer, db)}


@router.post("/reset", summary="Reset hackathon countdown to 24:00:00 (Admin only)")
def reset_timer(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Reset countdown to exactly 24:00:00 and clear active countdown state."""
    timer = get_or_create_timer(db)
    now = datetime.now(timezone.utc)

    timer.timer_status = TimerStatus.NOT_STARTED.value
    timer.hackathon_start_time = None
    timer.hackathon_end_time = None
    timer.remaining_seconds = TOTAL_SECONDS_24H
    timer.total_duration_seconds = TOTAL_SECONDS_24H
    timer.last_updated_at = now

    db.commit()
    db.refresh(timer)
    return {"success": True, "message": "Hackathon countdown reset to 24:00:00.", "data": sync_timer_state(timer, db)}
