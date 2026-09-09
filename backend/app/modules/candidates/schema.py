"""Pydantic schemas for candidate intake/update (SRS §4 validation table)."""

import re
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.modules.candidates.model import CandidateStatus

_PHONE_ALLOWED_CHARS_RE = re.compile(r"^[0-9+\-\s]+$")


def validate_phone(phone: str) -> str:
    """SRS §4: "Hanya angka, +, spasi, tanda hubung; panjang 8-15 digit" —
    the digit COUNT must be 8-15 (not the total string length), so a
    formatted international number like "+62 813-9988-7766" (11 digits,
    17 chars with formatting) is valid."""
    if not _PHONE_ALLOWED_CHARS_RE.fullmatch(phone):
        raise ValueError("Nomor telepon hanya boleh berisi angka, +, spasi, dan tanda hubung")
    digit_count = sum(1 for c in phone if c.isdigit())
    if not (8 <= digit_count <= 15):
        raise ValueError(f"Nomor telepon harus berisi 8-15 digit (saat ini {digit_count} digit)")
    return phone


class CandidateIntakeForm(BaseModel):
    """Validates the plain form fields of a multipart intake request — the
    CV/certificate files themselves are handled separately as UploadFile
    params (see router.py)."""

    full_name: str
    email: EmailStr
    phone: str

    @field_validator("phone")
    @classmethod
    def _check_phone(cls, v: str) -> str:
        return validate_phone(v)


class CandidateUpdate(BaseModel):
    """Manual correction of intake fields and/or parsed_profile (FR-4.3)."""

    full_name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    parsed_profile: dict | None = None
    assessment_input: dict | None = None

    @field_validator("phone")
    @classmethod
    def _check_phone(cls, v: str | None) -> str | None:
        return validate_phone(v) if v is not None else v


class CandidateStatusUpdate(BaseModel):
    """FR-7.2 + BR-1: status changes are always manual and always carry a
    reason — including backward ones (the system itself never regresses a
    status automatically; a human can, but has to say why)."""

    status: CandidateStatus
    reason: str = Field(min_length=1, max_length=500)


class CandidateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    job_posting_id: uuid.UUID
    full_name: str
    email: str
    phone: str
    cv_file_url: str
    certificate_urls: list[str]
    parsed_profile: dict | None
    assessment_input: dict | None
    status: CandidateStatus
    applied_at: datetime


class CandidateCreateResponse(CandidateOut):
    duplicate_warning: bool = False


class CandidateListItemOut(CandidateOut):
    """Candidate + its latest score, denormalized for the Ranking Dashboard
    (FR-6.1) so it doesn't need one request per row."""

    final_score: float | None = None
    label: str | None = None
    score_computed_at: datetime | None = None
