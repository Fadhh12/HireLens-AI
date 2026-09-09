"""Pydantic schemas for job postings, incl. weight-sum-100 validator (FR-2.3)
and the FR-2.2 "active needs >=1 required skill" rule."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.jobs.model import JobLevel, JobStatus

_WEIGHT_SUM_TOLERANCE = 0.01


def _check_weight_sum(skill: float, experience: float, values: float) -> None:
    total = skill + experience + values
    if abs(total - 100) > _WEIGHT_SUM_TOLERANCE:
        raise ValueError(f"Total bobot scoring harus tepat 100% (saat ini {total:.2f}%)")


def _check_active_needs_required_skill(status: JobStatus, required_skills: list[str]) -> None:
    if status == JobStatus.active and len(required_skills) == 0:
        raise ValueError("Job harus punya minimal 1 skill wajib sebelum bisa berstatus aktif")


class JobPostingCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    department: str = Field(min_length=1, max_length=255)
    description: str = ""
    required_skills: list[str] = Field(default_factory=list)
    nice_to_have_skills: list[str] = Field(default_factory=list)
    min_experience_years: int = Field(default=0, ge=0)
    level: JobLevel
    weight_skill_fit: float = Field(default=50, ge=0, le=100)
    weight_experience_fit: float = Field(default=30, ge=0, le=100)
    weight_values_fit: float = Field(default=20, ge=0, le=100)
    status: JobStatus = JobStatus.draft

    @model_validator(mode="after")
    def _validate(self) -> "JobPostingCreate":
        _check_weight_sum(self.weight_skill_fit, self.weight_experience_fit, self.weight_values_fit)
        _check_active_needs_required_skill(self.status, self.required_skills)
        return self


class JobPostingUpdate(BaseModel):
    """All fields optional (partial update). Cross-field checks (weight sum,
    FR-2.2) run in service.update_job against the merged, post-update values
    — a partial payload alone can't be validated in isolation."""

    title: str | None = Field(default=None, min_length=1, max_length=255)
    department: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    required_skills: list[str] | None = None
    nice_to_have_skills: list[str] | None = None
    min_experience_years: int | None = Field(default=None, ge=0)
    level: JobLevel | None = None
    weight_skill_fit: float | None = Field(default=None, ge=0, le=100)
    weight_experience_fit: float | None = Field(default=None, ge=0, le=100)
    weight_values_fit: float | None = Field(default=None, ge=0, le=100)
    status: JobStatus | None = None


class JobPostingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    department: str
    description: str
    required_skills: list[str]
    nice_to_have_skills: list[str]
    min_experience_years: int
    level: JobLevel
    weight_skill_fit: float
    weight_experience_fit: float
    weight_values_fit: float
    status: JobStatus
    created_by: uuid.UUID
    created_at: datetime
