"""Pydantic schemas for projects."""
import uuid
from datetime import datetime
from typing import Optional, Any, Union
from pydantic import BaseModel, field_validator

from app.models.project import ProjectStatus
from app.models.problem_statement import RealmEnum


class ProjectDraftRequest(BaseModel):
    """Save draft request for editable blocks."""
    project_title: Optional[str] = None
    abstract: Optional[str] = None
    problem_statement: Optional[str] = None
    objectives: Optional[Union[str, list[str]]] = None
    proposed_solution: Optional[str] = None
    technologies: Optional[str] = None
    technology_stack: Optional[Union[str, list[str]]] = None
    expected_outcome: Optional[str] = None
    project_description: Optional[str] = None
    github_url: Optional[str] = None
    demo_url: Optional[str] = None

    @field_validator("github_url")
    @classmethod
    def validate_github(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if v and not v.startswith("https://github.com/"):
                raise ValueError("GitHub URL must start with https://github.com/")
        return v


class ProjectSubmitRequest(BaseModel):
    """Universal final project submission."""
    project_title: Optional[str] = None
    abstract: Optional[str] = None
    problem_statement: Optional[str] = None
    objectives: Optional[Union[str, list[str]]] = None
    proposed_solution: Optional[str] = None
    technologies: Optional[str] = None
    technology_stack: Optional[Union[str, list[str]]] = None
    expected_outcome: Optional[str] = None
    project_description: Optional[str] = None
    github_url: Optional[str] = None
    demo_url: Optional[str] = None

    @field_validator("github_url")
    @classmethod
    def validate_github(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if v and not v.startswith("https://github.com/"):
                raise ValueError("GitHub URL must start with https://github.com/")
        return v


class AdminProjectUpdateRequest(BaseModel):
    """Admin update full project fields."""
    project_title: Optional[str] = None
    problem_statement: Optional[str] = None
    abstract: Optional[str] = None
    objectives: Optional[str] = None
    proposed_solution: Optional[str] = None
    technologies: Optional[str] = None
    technology_stack: Optional[str] = None
    expected_outcome: Optional[str] = None
    project_description: Optional[str] = None
    github_url: Optional[str] = None
    demo_url: Optional[str] = None
    status: Optional[ProjectStatus] = None
    current_round: Optional[int] = None
    realm: Optional[RealmEnum] = None
    problem_statement_id: Optional[uuid.UUID] = None
    domain: Optional[str] = None

    @field_validator("github_url")
    @classmethod
    def validate_github(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if v and not v.startswith("https://github.com/"):
                raise ValueError("GitHub URL must start with https://github.com/")
        return v


class AdminGithubUpdateRequest(BaseModel):
    """Admin update locked github URL."""
    github_url: str

    @field_validator("github_url")
    @classmethod
    def validate_github(cls, v: str) -> str:
        v = v.strip()
        if not v.startswith("https://github.com/"):
            raise ValueError("GitHub URL must start with https://github.com/")
        return v


class AdminDomainUpdateRequest(BaseModel):
    """Admin update realm/domain for project and team."""
    domain: str


class DomainBasic(BaseModel):
    id: Optional[int] = None
    name: str
    display_name: str

    model_config = {"from_attributes": True}


class ProblemStatementSummary(BaseModel):
    id: uuid.UUID
    problem_code: str
    realm: RealmEnum
    title: str
    description: str
    difficulty: str

    model_config = {"from_attributes": True}


class TeamUserBasic(BaseModel):
    id: int
    name: str
    username: str
    team_name: Optional[str] = None
    team_leader: Optional[str] = None
    member_one: Optional[str] = None
    member_two: Optional[str] = None
    member_three: Optional[str] = None
    college_name: Optional[str] = None
    organization: Optional[str] = None
    department: Optional[str] = None

    model_config = {"from_attributes": True}


class ProjectResponse(BaseModel):
    id: int
    project_code: str
    user_id: int
    user: TeamUserBasic
    realm: Optional[str] = None
    domain_id: Optional[int] = None
    domain: Optional[DomainBasic] = None
    problem_statement_id: Optional[uuid.UUID] = None
    problem_statement: Optional[ProblemStatementSummary] = None
    problem_code: Optional[str] = None
    project_title: Optional[str] = None
    abstract: Optional[str] = None
    objectives: Optional[str] = None
    proposed_solution: Optional[str] = None
    technologies: Optional[str] = None
    technology_stack: Optional[str] = None
    expected_outcome: Optional[str] = None
    project_description: Optional[str] = None
    github_url: Optional[str] = None
    demo_url: Optional[str] = None
    is_submitted: bool = False
    status: ProjectStatus
    current_round: int
    draft_saved_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    updated_at: datetime

    model_config = {"from_attributes": True}


class TimelineEvent(BaseModel):
    round_number: Optional[int]
    event_type: str
    title: str
    status: str
    comments: Optional[str]
    suggested_improvements: Optional[str] = None
    date: str


class ProjectTimelineResponse(BaseModel):
    success: bool
    message: str
    data: list[TimelineEvent]


class ProjectSingleResponse(BaseModel):
    success: bool
    message: str
    data: ProjectResponse


class ProjectListResponse(BaseModel):
    success: bool
    message: str
    data: list[ProjectResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
