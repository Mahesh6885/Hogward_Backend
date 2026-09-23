"""Pydantic schemas for problem statements."""
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ProblemStatementBase(BaseModel):
    problem_code: str
    detailed_description: str


class ProblemStatementCreate(ProblemStatementBase):
    domain_id: int


class ProblemStatementResponse(ProblemStatementBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    domain_id: int
    is_assigned: bool
    assigned_team_id: int | None = None
    created_at: datetime


class ProblemStatementDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    problem_code: str
    detailed_description: str
    domain: str
    is_assigned: bool
    assigned_team_id: int | None = None
