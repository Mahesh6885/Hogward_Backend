"""Pydantic schemas for projects."""
from datetime import datetime
from typing import Optional, Any, Union
from pydantic import BaseModel, field_validator

from app.models.project import ProjectStatus


class ProjectDraftRequest(BaseModel):
    """Save draft request for editable blocks."""
    topic_id: Optional[int] = None
    custom_topic: Optional[str] = None
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
    topic_id: Optional[int] = None
    custom_topic: Optional[str] = None
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

    @field_validator("custom_topic")
    @classmethod
    def custom_topic_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Custom topic cannot be empty")
            if len(v) < 10:
                raise ValueError("Custom topic must be at least 10 characters")
            if len(v) > 500:
                raise ValueError("Custom topic cannot exceed 500 characters")
        return v

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
    domain_id: Optional[int] = None
    assigned_problem_statement_id: Optional[int] = None

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
    """Admin update domain for project and team."""
    domain: str


class DomainBasic(BaseModel):
    id: int
    name: str
    display_name: str

    model_config = {"from_attributes": True}


class TopicBasic(BaseModel):
    id: int
    title: str
    description: Optional[str]

    model_config = {"from_attributes": True}


class ProblemStatementBasic(BaseModel):
    id: int
    problem_code: str
    detailed_description: str

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
    academic_year: Optional[str] = None

    model_config = {"from_attributes": True}


class ProjectResponse(BaseModel):
    id: int
    project_code: str
    user_id: int
    user: TeamUserBasic
    domain_id: int
    domain: DomainBasic
    topic_id: Optional[int]
    topic: Optional[TopicBasic]
    assigned_problem_statement_id: Optional[int] = None
    assigned_problem_statement: Optional[ProblemStatementBasic] = None
    custom_topic: Optional[str]
    project_title: Optional[str]
    abstract: Optional[str]
    problem_statement: Optional[str]
    objectives: Optional[str]
    proposed_solution: Optional[str]
    technologies: Optional[str]
    technology_stack: Optional[str] = None
    expected_outcome: Optional[str]
    project_description: Optional[str]
    github_url: Optional[str]
    demo_url: Optional[str]
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
