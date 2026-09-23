"""Topics routes — random selection for users, CRUD for admins."""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.core.dependencies import get_current_user, require_admin
from app.models.user import User
from app.schemas.topic import TopicCreate, TopicUpdate, TopicStatusUpdate
from app.services.topic_service import (
    get_random_topics_for_user,
    list_topics_admin,
    get_topic_by_id,
    create_topic,
    update_topic,
    update_topic_status,
    delete_topic,
)

router = APIRouter(tags=["Topics"])


def _topic_dict(topic) -> dict:
    domain_map = {"AI": "AI", "CYBERSECURITY": "Cybersecurity", "OPEN_INNOVATION": "Open Innovation"}
    return {
        "id": topic.id,
        "title": topic.title,
        "description": topic.description,
        "domain_id": topic.domain_id,
        "domain": {"id": topic.domain.id, "name": topic.domain.name, "display_name": domain_map.get(topic.domain.name, topic.domain.name)},
        "is_active": topic.is_active,
        "created_at": topic.created_at.isoformat(),
        "updated_at": topic.updated_at.isoformat(),
    }


# ─── User endpoint ──────────────────────────────────────────────────────────

@router.get("/api/topics/random", status_code=200)
def get_random_topics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return exactly 10 random active topics for the authenticated user's domain.
    Domain is resolved server-side from JWT — frontend cannot specify the domain.
    """
    topics = get_random_topics_for_user(db, current_user)
    return {
        "success": True,
        "message": "Random topics retrieved",
        "data": [_topic_dict(t) for t in topics],
    }


# ─── Admin endpoints ─────────────────────────────────────────────────────────

@router.get("/api/admin/topics", status_code=200)
def admin_list_topics(
    domain: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    items, total, total_pages = list_topics_admin(db, domain, is_active, page, page_size)
    return {
        "success": True,
        "message": "Topics retrieved",
        "data": [_topic_dict(t) for t in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


@router.post("/api/admin/topics", status_code=201)
def admin_create_topic(
    data: TopicCreate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    topic = create_topic(db, data, admin)
    return {"success": True, "message": "Topic created", "data": _topic_dict(topic)}


@router.get("/api/admin/topics/{topic_id}", status_code=200)
def admin_get_topic(
    topic_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    topic = get_topic_by_id(db, topic_id)
    return {"success": True, "message": "Topic retrieved", "data": _topic_dict(topic)}


@router.put("/api/admin/topics/{topic_id}", status_code=200)
def admin_update_topic(
    topic_id: int,
    data: TopicUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    topic = update_topic(db, topic_id, data, admin)
    return {"success": True, "message": "Topic updated", "data": _topic_dict(topic)}


@router.patch("/api/admin/topics/{topic_id}/status", status_code=200)
def admin_update_topic_status(
    topic_id: int,
    data: TopicStatusUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    topic = update_topic_status(db, topic_id, data, admin)
    return {"success": True, "message": "Topic status updated", "data": _topic_dict(topic)}


@router.delete("/api/admin/topics/{topic_id}", status_code=200)
def admin_delete_topic(
    topic_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    delete_topic(db, topic_id, admin)
    return {"success": True, "message": "Topic deleted", "data": None}
