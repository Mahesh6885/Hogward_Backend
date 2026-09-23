"""Pydantic schemas for domains."""
from datetime import datetime
from pydantic import BaseModel

from app.models.domain import DomainName


class DomainResponse(BaseModel):
    id: int
    name: DomainName
    display_name: str
    description: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DomainListResponse(BaseModel):
    success: bool
    message: str
    data: list[DomainResponse]
