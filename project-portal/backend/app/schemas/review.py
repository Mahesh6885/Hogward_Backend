"""Pydantic schemas for reviews."""
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, field_validator, model_validator

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


# ─── Phase 3: Round 1, 2, 3 Evaluation Schemas ────────────────────────────────

class ReviewRound1Submit(BaseModel):
    evaluator_name: Optional[str] = "Chief Arbiter"
    score_problem_clarity: int
    score_solution_quality: int
    score_tech_stack: int
    score_idea_presentation: int
    score_feasibility: int
    score_confidence_qa: int
    comments: Optional[str] = None
    suggestions: Optional[str] = None
    is_draft: bool = False

    @model_validator(mode="before")
    @classmethod
    def reconcile_r1_fields(cls, values: Any) -> Any:
        if isinstance(values, dict):
            if "score_proposed_solution" in values and "score_solution_quality" not in values:
                values["score_solution_quality"] = values["score_proposed_solution"]
            elif "score_solution_quality" in values and "score_proposed_solution" not in values:
                values["score_proposed_solution"] = values["score_solution_quality"]

            if "score_team_confidence_qa" in values and "score_confidence_qa" not in values:
                values["score_confidence_qa"] = values["score_team_confidence_qa"]
            elif "score_confidence_qa" in values and "score_team_confidence_qa" not in values:
                values["score_team_confidence_qa"] = values["score_confidence_qa"]

            if "suggestions_next_round" in values and "suggestions" not in values:
                values["suggestions"] = values["suggestions_next_round"]
            elif "suggestions" in values and "suggestions_next_round" not in values:
                values["suggestions_next_round"] = values["suggestions"]
        return values

    @field_validator(
        "score_problem_clarity",
        "score_solution_quality",
        "score_tech_stack",
        "score_idea_presentation",
        "score_feasibility",
        "score_confidence_qa",
    )
    @classmethod
    def check_score_1_to_10(cls, v: int) -> int:
        if v < 0 or v > 10:
            raise ValueError("Criteria scores must be between 1 and 10")
        return v

    def calculate_total(self) -> int:
        return (
            self.score_problem_clarity
            + self.score_solution_quality
            + self.score_tech_stack
            + self.score_idea_presentation
            + self.score_feasibility
            + self.score_confidence_qa
        )


class ReviewRound2Submit(BaseModel):
    evaluator_name: Optional[str] = "Chief Arbiter"
    score_planning_workflow: int
    score_frontend_progress: int
    score_backend_progress: int
    score_prototype_progress: int
    score_technical_quality: int
    score_team_collaboration: int
    score_milestone_completion: int
    review_notes: Optional[str] = None
    improvement_suggestions: Optional[str] = None
    is_draft: bool = False

    @field_validator(
        "score_planning_workflow",
        "score_frontend_progress",
        "score_backend_progress",
        "score_prototype_progress",
        "score_technical_quality",
        "score_team_collaboration",
        "score_milestone_completion",
    )
    @classmethod
    def check_score_1_to_10(cls, v: int) -> int:
        if v < 0 or v > 10:
            raise ValueError("Criteria scores must be between 1 and 10")
        return v

    def calculate_total(self) -> int:
        return (
            self.score_planning_workflow
            + self.score_frontend_progress
            + self.score_backend_progress
            + self.score_prototype_progress
            + self.score_technical_quality
            + self.score_team_collaboration
            + self.score_milestone_completion
        )


class ReviewRound3Submit(BaseModel):
    evaluator_name: Optional[str] = "Chief Arbiter"
    score_tech_understanding: int
    score_problem_solution_fit: int
    score_innovation_creativity: int
    score_prototype_functionality: int
    score_solution_completeness: int
    score_teamwork_execution: int
    score_qa_handling: int
    final_remarks: Optional[str] = None
    strengths: Optional[str] = None
    weaknesses: Optional[str] = None
    recommendation: Optional[str] = None
    is_draft: bool = False

    @model_validator(mode="before")
    @classmethod
    def reconcile_r3_fields(cls, values: Any) -> Any:
        if isinstance(values, dict):
            if "score_tech_stack_understanding" in values and "score_tech_understanding" not in values:
                values["score_tech_understanding"] = values["score_tech_stack_understanding"]
            elif "score_tech_understanding" in values and "score_tech_stack_understanding" not in values:
                values["score_tech_stack_understanding"] = values["score_tech_understanding"]
        return values

    @field_validator(
        "score_tech_understanding",
        "score_problem_solution_fit",
        "score_innovation_creativity",
        "score_prototype_functionality",
        "score_solution_completeness",
        "score_teamwork_execution",
        "score_qa_handling",
    )
    @classmethod
    def check_score_1_to_10(cls, v: int) -> int:
        if v < 0 or v > 10:
            raise ValueError("Criteria scores must be between 1 and 10")
        return v

    def calculate_total(self) -> int:
        return (
            self.score_tech_understanding
            + self.score_problem_solution_fit
            + self.score_innovation_creativity
            + self.score_prototype_functionality
            + self.score_solution_completeness
            + self.score_teamwork_execution
            + self.score_qa_handling
        )
