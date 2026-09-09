"""Orchestrates scoring.py (numeric, rule-based) + llm_assist.py
(qualitative text only), persists a new `candidate_scores` row every
time (SDD §3.2: history, not an overwrite)."""

import uuid
from concurrent.futures import ThreadPoolExecutor

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.candidates.model import Candidate
from app.modules.candidates.service import get_candidate
from app.modules.jobs.service import get_job
from app.modules.matching_engine import llm_assist, scoring
from app.modules.matching_engine.model import CandidateScore

LLM_MODEL_LABEL_UNAVAILABLE = "llm-unavailable"


def compute_and_save_score(db: Session, candidate_id: uuid.UUID) -> CandidateScore:
    candidate = get_candidate(db, candidate_id)
    job = get_job(db, candidate.job_posting_id)

    profile = candidate.parsed_profile or {}
    candidate_skills = (profile.get("skills") or {}).get("value") or []
    candidate_years = (profile.get("experience_years") or {}).get("value") or 0.0

    result = scoring.compute_final_score(
        job=job,
        candidate_skills=candidate_skills,
        candidate_years=candidate_years,
        assessment_input=candidate.assessment_input,
    )

    # LLM-assisted text only — never touches the numbers computed above
    # (FR-5.5). Failure here doesn't affect the score at all. Run both
    # calls concurrently — sequential blocking calls could add up to
    # 2x LLM_TIMEOUT_SECONDS and blow past the PRD's <30s upload-to-
    # ranking budget on their own.
    with ThreadPoolExecutor(max_workers=2) as pool:
        summary_future = pool.submit(llm_assist.generate_candidate_summary, candidate, job)
        values_note_future = pool.submit(llm_assist.generate_values_fit_note, candidate.assessment_input, job)
        summary = summary_future.result()
        values_note = values_note_future.result()
    llm_used = summary is not None or values_note is not None

    if result["values_fit"]["score"] is not None:
        result["values_fit"]["note"] = values_note or "Skor berdasarkan input asesmen manual."
    elif candidate.assessment_input:
        # Assessment exists (e.g. MBTI only) but yielded no numeric score.
        result["values_fit"]["note"] = values_note or "Belum ada skor kompetensi numerik untuk dihitung."
    else:
        result["values_fit"]["note"] = "Tidak ada hasil asesmen manual — bobot dialihkan ke skill & experience fit (BR-6)."

    model_version = f"{scoring.MODEL_VERSION}+{_llm_label(llm_used)}"

    # BR-5 audit trail: snapshot the inputs alongside the outputs so this
    # row stays self-explanatory even if the candidate/job record changes.
    score_breakdown = {
        "skill_fit": result["skill_fit"],
        "experience_fit": result["experience_fit"],
        "values_fit": result["values_fit"],
        "candidate_summary": summary,
        "inputs_snapshot": {
            "candidate_skills": candidate_skills,
            "candidate_years": candidate_years,
            "job_required_skills": job.required_skills,
            "job_nice_to_have_skills": job.nice_to_have_skills,
            "job_min_experience_years": job.min_experience_years,
            "job_weights": {
                "skill_fit": float(job.weight_skill_fit),
                "experience_fit": float(job.weight_experience_fit),
                "values_fit": float(job.weight_values_fit),
            },
            "assessment_input": candidate.assessment_input,
        },
    }

    score = CandidateScore(
        id=uuid.uuid4(),
        candidate_id=candidate.id,
        skill_fit_score=result["skill_fit"]["score"],
        experience_fit_score=result["experience_fit"]["score"],
        values_fit_score=result["values_fit"]["score"],
        final_score=result["final_score"],
        label=result["label"],
        score_breakdown=score_breakdown,
        model_version=model_version,
    )
    db.add(score)
    db.commit()
    db.refresh(score)
    return score


def _llm_label(llm_used: bool) -> str:
    from app.core.config import get_settings

    settings = get_settings()
    return settings.llm_model_name if llm_used else LLM_MODEL_LABEL_UNAVAILABLE


def get_latest_score(db: Session, candidate_id: uuid.UUID) -> CandidateScore:
    score = db.scalar(
        select(CandidateScore)
        .where(CandidateScore.candidate_id == candidate_id)
        .order_by(CandidateScore.computed_at.desc())
        .limit(1)
    )
    if score is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kandidat ini belum punya skor — trigger dulu lewat POST /candidates/{id}/score",
        )
    return score


def get_latest_scores_for_job(db: Session, candidate_ids: list[uuid.UUID]) -> dict[uuid.UUID, CandidateScore]:
    """Bulk-fetch each candidate's most recent score, for the ranking dashboard."""
    if not candidate_ids:
        return {}
    rows = db.scalars(
        select(CandidateScore)
        .where(CandidateScore.candidate_id.in_(candidate_ids))
        .order_by(CandidateScore.computed_at.desc())
    )
    latest: dict[uuid.UUID, CandidateScore] = {}
    for row in rows:
        if row.candidate_id not in latest:
            latest[row.candidate_id] = row
    return latest
