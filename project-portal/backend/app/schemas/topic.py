"""Pydantic schemas for topics."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator

from app.models.domain import DomainName


class TopicCreate(BaseModel):
    title: str
    description: Optional[str] = None
    domain: DomainName

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Title cannot be empty")
        if len(v) > 255:
            raise ValueError("Title cannot exceed 255 characters")
        return v


class TopicUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    domain: Optional[DomainName] = None

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Title cannot be empty")
            if len(v) > 255:
                raise ValueError("Title cannot exceed 255 characters")
        return v


class TopicStatusUpdate(BaseModel):
    is_active: bool


class DomainBasic(BaseModel):
    id: int
    name: str
    display_name: str

    model_config = {"from_attributes": True}


class TopicResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    domain_id: int
    domain: DomainBasic
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TopicListResponse(BaseModel):
    success: bool
    message: str
    data: list[TopicResponse]
    total: int


class TopicSingleResponse(BaseModel):
    success: bool
    message: str
    data: TopicResponse


class RandomTopicsResponse(BaseModel):
    success: bool
    message: str
    data: list[TopicResponse]
