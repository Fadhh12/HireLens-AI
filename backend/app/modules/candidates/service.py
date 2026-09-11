"""Candidate business logic: intake, storage upload, manual correction,
status transitions (FR-7.2, BR-1).

The activity-log audit trail for status changes (FR-7.3) is Phase 5
scope (Task Breakdown 5.7, needs the `activity_logs` table) — not
implemented here yet.
"""

import uuid

from fastapi import HTTPException, UploadFile, status as http_status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.storage import delete_files, upload_file
from app.modules.auth.model import User
from app.modules.candidates.model import Candidate, CandidateStatus
from app.modules.candidates.schema import CandidateUpdate
from app.modules.document_ai.parser import ParsedProfile
from app.modules.jobs.model import JobPosting

# --- SRS §4 validation constants ---
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024
MAX_CERTIFICATE_FILES = 5

CV_ALLOWED_EXTENSIONS = {"pdf", "docx"}
CV_ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
CERTIFICATE_ALLOWED_EXTENSIONS = {"pdf", "jpg", "jpeg", "png"}
CERTIFICATE_ALLOWED_CONTENT_TYPES = {"application/pdf", "image/jpeg", "image/png"}


def _extension_of(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


async def _validate_and_read(
    file: UploadFile, allowed_extensions: set[str], allowed_content_types: set[str], label: str
) -> bytes:
    ext = _extension_of(file.filename or "")
    if ext not in allowed_extensions or (file.content_type not in allowed_content_types):
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"{label}: tipe file tidak didukung (izinkan: {', '.join(sorted(allowed_extensions))})",
        )
    content = await file.read()
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"{label}: ukuran file melebihi 5MB",
        )
    if len(content) == 0:
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"{label}: file kosong"
        )
    return content


async def validate_cv(file: UploadFile) -> bytes:
    return await _validate_and_read(file, CV_ALLOWED_EXTENSIONS, CV_ALLOWED_CONTENT_TYPES, "CV")


async def validate_certificate(file: UploadFile) -> bytes:
    return await _validate_and_read(
        file, CERTIFICATE_ALLOWED_EXTENSIONS, CERTIFICATE_ALLOWED_CONTENT_TYPES, "Sertifikat"
    )


def find_duplicate(db: Session, job_posting_id: uuid.UUID, email: str) -> Candidate | None:
    """SRS §7 edge case: same email on the same job is a *warning*, not a
    rejection — could legitimately be a re-apply."""
    return db.scalar(
        select(Candidate).where(
            Candidate.job_posting_id == job_posting_id, Candidate.email == email
        )
    )


async def create_candidate(
    db: Session,
    job_posting_id: uuid.UUID,
    full_name: str,
    email: str,
    phone: str,
    cv_file: UploadFile,
    certificate_files: list[UploadFile],
    assessment_input: dict | None = None,
) -> tuple[Candidate, bool]:
    if len(certificate_files) > MAX_CERTIFICATE_FILES:
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Maksimal {MAX_CERTIFICATE_FILES} file sertifikat",
        )

    cv_content = await validate_cv(cv_file)
    certificate_contents = [(f, await validate_certificate(f)) for f in certificate_files]

    duplicate = find_duplicate(db, job_posting_id, email)

    candidate_id = uuid.uuid4()
    cv_ext = _extension_of(cv_file.filename or "cv.pdf")
    cv_path = f"candidates/{job_posting_id}/{candidate_id}/cv.{cv_ext}"
    upload_file(cv_path, cv_content, cv_file.content_type or "application/octet-stream")

    certificate_paths: list[str] = []
    for i, (f, content) in enumerate(certificate_contents):
        ext = _extension_of(f.filename or f"certificate_{i}")
        path = f"candidates/{job_posting_id}/{candidate_id}/certificates/{i}.{ext}"
        upload_file(path, content, f.content_type or "application/octet-stream")
        certificate_paths.append(path)

    candidate = Candidate(
        id=candidate_id,
        job_posting_id=job_posting_id,
        full_name=full_name,
        email=email,
        phone=phone,
        cv_file_url=cv_path,
        certificate_urls=certificate_paths,
        assessment_input=assessment_input,
        status=CandidateStatus.new,
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    return candidate, duplicate is not None


def list_candidates(db: Session, job_posting_id: uuid.UUID) -> list[Candidate]:
    return list(
        db.scalars(
            select(Candidate)
            .where(Candidate.job_posting_id == job_posting_id)
            .order_by(Candidate.applied_at.desc())
        )
    )


def list_all_candidates(db: Session, job_posting_id: uuid.UUID | None = None) -> list[tuple[Candidate, str]]:
    """Cross-job candidate list for the global "Kandidat" screen — pairs
    each candidate with its job's title so the table doesn't need one
    lookup per row (same denormalization idea as CandidateListItemOut's
    score)."""
    query = select(Candidate, JobPosting.title).join(
        JobPosting, Candidate.job_posting_id == JobPosting.id
    )
    if job_posting_id is not None:
        query = query.where(Candidate.job_posting_id == job_posting_id)
    query = query.order_by(Candidate.applied_at.desc())
    return [(row.Candidate, row.title) for row in db.execute(query)]


def get_candidate(db: Session, candidate_id: uuid.UUID) -> Candidate:
    candidate = db.get(Candidate, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Kandidat tidak ditemukan")
    return candidate


def update_candidate(db: Session, candidate_id: uuid.UUID, data: CandidateUpdate) -> Candidate:
    """FR-4.3: recruiter correction of intake fields / parsed_profile."""
    candidate = get_candidate(db, candidate_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(candidate, field, value)
    db.commit()
    db.refresh(candidate)
    return candidate


def update_status(
    db: Session, candidate_id: uuid.UUID, new_status: CandidateStatus, reason: str, actor: User
) -> Candidate:
    """FR-7.2/BR-1: manual status change, always with a reason. FR-7.3:
    recorded to the activity log (old -> new status; `reason` itself isn't
    a logged column per SDD §3.1's activity_logs shape, so it rides along
    as a suffix on new_value instead of being dropped)."""
    from app.modules.activity_log.service import log_activity

    candidate = get_candidate(db, candidate_id)
    old_status = candidate.status.value
    candidate.status = new_status
    db.commit()
    db.refresh(candidate)

    log_activity(
        db,
        actor_id=actor.id,
        action="status_changed",
        candidate_id=candidate.id,
        old_value=old_status,
        new_value=f"{new_status.value} (alasan: {reason})",
    )

    # Not part of the original SDD — a later feature request: shortlisted/
    # rejected/hired each auto-send a templated email (see messaging/).
    # "interviewed" is deliberately excluded, that transition already gets
    # the Calendar invite from scheduling/service.py's own flow. Local
    # import to avoid a module-load-order cycle (messaging imports
    # candidates.model), and best-effort so a Google/Gmail hiccup never
    # breaks the status change itself.
    from app.modules.messaging.model import EmailTrigger
    from app.modules.messaging.service import send_status_email_best_effort

    if new_status.value in (EmailTrigger.shortlisted, EmailTrigger.rejected, EmailTrigger.hired):
        send_status_email_best_effort(db, candidate, EmailTrigger(new_status.value), actor_id=actor.id)

    return candidate


def apply_parsed_profile(db: Session, candidate_id: uuid.UUID, profile: ParsedProfile) -> Candidate:
    """Called by the background parsing task on a successful parse."""
    candidate = get_candidate(db, candidate_id)
    candidate.parsed_profile = profile.to_dict()
    db.commit()
    db.refresh(candidate)
    return candidate


def mark_needs_manual_review(db: Session, candidate_id: uuid.UUID, reason: str) -> Candidate:
    """FR-3.5: parsing failed outright — keep the candidate, don't reject."""
    candidate = get_candidate(db, candidate_id)
    candidate.status = CandidateStatus.needs_manual_review
    candidate.parsed_profile = {"warnings": [reason]}
    db.commit()
    db.refresh(candidate)
    return candidate


def delete_candidate_files(candidate: Candidate) -> None:
    delete_files([candidate.cv_file_url, *candidate.certificate_urls])
