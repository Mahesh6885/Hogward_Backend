"""Review management service."""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.project import Project, ProjectStatus
from app.models.review import Review, ReviewStatus
from app.models.user import User
from app.models.audit_log import AuditLog
from app.schemas.review import ReviewCreate, ReviewUpdate


def create_review(db: Session, project_id: int, data: ReviewCreate, admin: User) -> Review:
    """Admin submits a review for a project round."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "message": "Project not found", "error_code": "NOT_FOUND"},
        )

    # Round validation
    max_rounds = settings.MAX_REVIEW_ROUNDS
    if data.round_number > max_rounds:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "message": f"Round number cannot exceed MAX_REVIEW_ROUNDS ({max_rounds})",
                "error_code": "INVALID_ROUND",
            },
        )

    # Prevent submitting a future round when the current round hasn't been reviewed
    if data.round_number > project.current_round:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "message": f"Cannot submit review for round {data.round_number} — project is currently at round {project.current_round}",
                "error_code": "INVALID_ROUND",
            },
        )

    # Prevent duplicate reviews for same project+round (must use PUT to update)
    existing_review = db.query(Review).filter(
        Review.project_id == project_id,
        Review.round_number == data.round_number,
    ).first()
    if existing_review:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "success": False,
                "message": f"A review for round {data.round_number} already exists. Use PUT to update.",
                "error_code": "REVIEW_EXISTS",
            },
        )

    review = Review(
        project_id=project_id,
        admin_id=admin.id,
        round_number=data.round_number,
        review_text=data.review_text.strip(),
        suggested_improvements=data.suggested_improvements.strip() if data.suggested_improvements else None,
        status=data.status,
    )
    db.add(review)
    db.flush()

    # Update project status
    _update_project_after_review(db, project, review)

    log = AuditLog(
        admin_id=admin.id,
        action="CREATE_REVIEW",
        target_type="project",
        target_id=project_id,
        description=f"Admin '{admin.username}' submitted review for project '{project.project_code}' round {data.round_number} — status: {data.status.value}",
    )
    db.add(log)
    db.commit()
    db.refresh(review)
    return review


def _update_project_after_review(db: Session, project: Project, review: Review) -> None:
    """Update project status and advance round based on review outcome."""
    max_rounds = settings.MAX_REVIEW_ROUNDS

    if review.status == ReviewStatus.PASSED:
        if review.round_number >= max_rounds:
            project.status = ProjectStatus.COMPLETED
        else:
            project.status = ProjectStatus.UNDER_REVIEW
            project.current_round = review.round_number + 1
    elif review.status == ReviewStatus.NEEDS_IMPROVEMENT:
        project.status = ProjectStatus.IN_PROGRESS
    elif review.status == ReviewStatus.REJECTED:
        project.status = ProjectStatus.REJECTED
    elif review.status == ReviewStatus.IN_REVIEW:
        project.status = ProjectStatus.UNDER_REVIEW
    # PENDING stays as-is


def update_review(db: Session, project_id: int, review_id: int, data: ReviewUpdate, admin: User) -> Review:
    """Admin updates an existing review (content/status only — round cannot be changed)."""
    review = db.query(Review).filter(
        Review.id == review_id, Review.project_id == project_id
    ).first()
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "message": "Review not found", "error_code": "NOT_FOUND"},
        )

    if data.review_text is not None:
        review.review_text = data.review_text.strip()
    if data.suggested_improvements is not None:
        review.suggested_improvements = data.suggested_improvements.strip() if data.suggested_improvements else None
    if data.status is not None:
        review.status = data.status
        # Re-evaluate project status
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            _update_project_after_review(db, project, review)

    db.commit()
    db.refresh(review)
    return review


def get_project_reviews(db: Session, project_id: int) -> list[Review]:
    return (
        db.query(Review)
        .filter(Review.project_id == project_id)
        .order_by(Review.round_number.asc())
        .all()
    )
