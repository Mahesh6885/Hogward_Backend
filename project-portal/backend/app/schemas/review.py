"""Pydantic schemas for reviews."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator

from app.models.review import ReviewStatus


class ReviewCreate(BaseModel):
    round_number: int
    review_text: str
    suggested_improvements: Optional[str] = None
    status: ReviewStatus

    @field_validator("round_number")
    @classmethod
    def round_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Round number must be at least 1")
        return v

    @field_validator("review_text")
    @classmethod
    def review_text_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Review text cannot be empty")
        if len(v) < 10:
            raise ValueError("Review text must be at least 10 characters")
        if len(v) > 5000:
            raise ValueError("Review text cannot exceed 5000 characters")
        return v


class ReviewUpdate(BaseModel):
    review_text: Optional[str] = None
    suggested_improvements: Optional[str] = None
    status: Optional[ReviewStatus] = None

    @field_validator("review_text")
    @classmethod
    def review_text_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Review text cannot be empty")
            if len(v) < 10:
                raise ValueError("Review text must be at least 10 characters")
            if len(v) > 5000:
                raise ValueError("Review text cannot exceed 5000 characters")
        return v


class AdminBasic(BaseModel):
    id: int
    name: str
    username: str

    model_config = {"from_attributes": True}


class ReviewResponse(BaseModel):
    id: int
    project_id: int
    admin_id: int
    admin: AdminBasic
    round_number: int
    review_text: str
    suggested_improvements: Optional[str] = None
    status: ReviewStatus
    reviewed_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReviewListResponse(BaseModel):
    success: bool
    message: str
    data: list[ReviewResponse]


class ReviewSingleResponse(BaseModel):
    success: bool
    message: str
    data: ReviewResponse
