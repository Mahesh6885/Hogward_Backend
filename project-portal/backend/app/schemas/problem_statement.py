"""Pydantic schemas for problem statements."""
from datetime import datetime
import uuid
from typing import Optional
from pydantic import BaseModel, Field

from app.models.problem_statement import RealmEnum, DifficultyEnum


class ProblemStatementBase(BaseModel):
    problem_code: str = Field(..., max_length=20, examples=["AI-PS-01"])
    realm: RealmEnum
    title: str
    description: str
    difficulty: DifficultyEnum = DifficultyEnum.INTERMEDIATE
    status: bool = True


class ProblemStatementCreate(ProblemStatementBase):
    pass


class ProblemStatementUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    difficulty: Optional[DifficultyEnum] = None
    status: Optional[bool] = None
    realm: Optional[RealmEnum] = None


class ProblemStatementResponse(ProblemStatementBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    project_count: Optional[int] = 0

    model_config = {"from_attributes": True}


class ProblemStatementStats(BaseModel):
    total_ai: int
    total_cybersecurity: int
    total_active: int
    total_inactive: int
    total_all: int
