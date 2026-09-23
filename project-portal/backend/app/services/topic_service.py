"""Topic service — random selection with locking and admin topic management."""
import random
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.domain import Domain, DomainName
from app.models.topic import Topic
from app.models.user import User
from app.models.audit_log import AuditLog
from app.models.topic_lock import TeamTopicLock
from app.schemas.topic import TopicCreate, TopicUpdate, TopicStatusUpdate
from app.utils.helpers import paginate

RANDOM_TOPIC_COUNT = 10


def get_random_topics_for_user(db: Session, user: User) -> list[Topic]:
    """
    Get exactly 10 random active topics for the authenticated user's domain.
    Domain is determined server-side from the JWT — frontend cannot influence this.
    Open Innovation users are not allowed to use this endpoint.
    
    Topic Locking Requirement:
    - Generates 10 topics and temporarily saves them for this user.
    - Refreshing the page does NOT generate a new list.
    - The team retains the same 10 topics until submission.
    """
    if user.domain is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "message": "User has no domain assigned", "error_code": "NO_DOMAIN"},
        )

    domain_name = user.domain.name
    if domain_name == DomainName.OPEN_INNOVATION.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "message": "Open Innovation users submit a custom topic, not a predefined one",
                "error_code": "FORBIDDEN",
            },
        )

    # Check if this team already has locked topics
    existing_locks = (
        db.query(TeamTopicLock)
        .filter(TeamTopicLock.user_id == user.id)
        .order_by(TeamTopicLock.id.asc())
        .all()
    )

    if existing_locks and len(existing_locks) == RANDOM_TOPIC_COUNT:
        locked_ids = [lock.topic_id for lock in existing_locks]
        topics = (
            db.query(Topic)
            .filter(Topic.id.in_(locked_ids), Topic.is_active == True)  # noqa: E712
            .all()
        )
        # Verify all locked topics still exist and are active
        if len(topics) == RANDOM_TOPIC_COUNT:
            # Preserve original locked order
            topic_dict = {t.id: t for t in topics}
            return [topic_dict[tid] for tid in locked_ids if tid in topic_dict]
        else:
            # Clean up stale locks if topics became inactive
            db.query(TeamTopicLock).filter(TeamTopicLock.user_id == user.id).delete()
            db.commit()

    # If no locks or stale locks, pick 10 random active topics for the domain
    available_topics = (
        db.query(Topic)
        .filter(Topic.domain_id == user.domain_id, Topic.is_active == True)  # noqa: E712
        .all()
    )

    if len(available_topics) < RANDOM_TOPIC_COUNT:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "success": False,
                "message": f"Not enough active topics in domain. Need {RANDOM_TOPIC_COUNT}, found {len(available_topics)}",
                "error_code": "INSUFFICIENT_TOPICS",
            },
        )

    chosen_topics = random.sample(available_topics, RANDOM_TOPIC_COUNT)

    # Save locks to database
    # Clean any leftover locks first
    db.query(TeamTopicLock).filter(TeamTopicLock.user_id == user.id).delete()
    for topic in chosen_topics:
        db.add(TeamTopicLock(user_id=user.id, topic_id=topic.id))
    db.commit()

    return chosen_topics


def list_topics_admin(
    db: Session,
    domain_name: Optional[str] = None,
    is_active: Optional[bool] = None,
    page: int = 1,
    page_size: int = 20,
):
    query = db.query(Topic)
    if domain_name:
        query = query.join(Domain).filter(Domain.name == domain_name)
    if is_active is not None:
        query = query.filter(Topic.is_active == is_active)
    return paginate(query, page, page_size)


def get_topic_by_id(db: Session, topic_id: int) -> Topic:
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "message": "Topic not found", "error_code": "NOT_FOUND"},
        )
    return topic


def create_topic(db: Session, data: TopicCreate, admin: User) -> Topic:
    domain = db.query(Domain).filter(Domain.name == data.domain.value).first()
    if not domain:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "message": "Domain not found", "error_code": "DOMAIN_NOT_FOUND"},
        )

    topic = Topic(
        title=data.title.strip(),
        description=data.description.strip() if data.description else None,
        domain_id=domain.id,
    )
    db.add(topic)
    db.flush()

    log = AuditLog(
        admin_id=admin.id,
        action="CREATE_TOPIC",
        target_type="topic",
        target_id=topic.id,
        description=f"Admin '{admin.username}' created topic '{topic.title}' in domain '{data.domain.value}'",
    )
    db.add(log)
    db.commit()
    db.refresh(topic)
    return topic


def update_topic(db: Session, topic_id: int, data: TopicUpdate, admin: User) -> Topic:
    topic = get_topic_by_id(db, topic_id)
    if data.title is not None:
        topic.title = data.title.strip()
    if data.description is not None:
        topic.description = data.description.strip()
    if data.domain is not None:
        domain = db.query(Domain).filter(Domain.name == data.domain.value).first()
        if not domain:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"success": False, "message": "Domain not found", "error_code": "DOMAIN_NOT_FOUND"},
            )
        topic.domain_id = domain.id
    db.commit()
    db.refresh(topic)
    return topic


def update_topic_status(db: Session, topic_id: int, data: TopicStatusUpdate, admin: User) -> Topic:
    topic = get_topic_by_id(db, topic_id)
    topic.is_active = data.is_active
    db.commit()
    db.refresh(topic)
    return topic


def delete_topic(db: Session, topic_id: int, admin: User) -> None:
    topic = get_topic_by_id(db, topic_id)
    db.delete(topic)
    db.commit()
