"""Pydantic schemas for admin dashboard."""
from pydantic import BaseModel


class UserStats(BaseModel):
    total: int
    ai: int
    cybersecurity: int
    open_innovation: int
    active: int
    inactive: int


class ProjectStats(BaseModel):
    total: int
    submitted: int
    under_review: int
    in_progress: int
    completed: int
    rejected: int


class RoundStats(BaseModel):
    round: int
    count: int


class DashboardData(BaseModel):
    users: UserStats
    projects: ProjectStats
    rounds: list[RoundStats]


class DashboardResponse(BaseModel):
    success: bool
    message: str
    data: DashboardData
