"""LLM-based interview question generation (FR-8.1) — Gemini, via the
same get_llm() used for matching_engine's summary/values-fit assist.

Unlike scoring, there's no rule-based fallback here: generating actual
interview questions is inherently a generation task, not something
FR-5.5's "LLM must not be the sole source of the score" restricts (that
rule is scoped to the numeric match score specifically). If the LLM
call fails outright, the caller just doesn't get a guide this attempt —
there's nothing rule-based to fall back to, so the Celery task simply
logs the failure and produces no row (candidate keeps whatever earlier
version already existed, if any).
"""

import json
import logging
import re

from app.modules.candidates.model import Candidate
from app.modules.jobs.model import JobPosting
from app.modules.matching_engine.llm_assist import get_llm

logger = logging.getLogger(__name__)

MIN_QUESTIONS = 3


class QuestionGenerationError(RuntimeError):
    pass


def _extract_json(text: str) -> dict:
    # Gemini often wraps JSON in ```json ... ``` fences despite instructions not to.
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise QuestionGenerationError("Respons LLM tidak mengandung JSON yang bisa di-parse")
    return json.loads(match.group(0))


def generate_interview_guide(candidate: Candidate, job: JobPosting, score_breakdown: dict | None) -> dict:
    llm = get_llm()
    if llm is None:
        raise QuestionGenerationError("LLM tidak tersedia (GOOGLE_API_KEY belum diset)")

    profile = candidate.parsed_profile or {}
    skills = ", ".join((profile.get("skills") or {}).get("value") or []) or "tidak terdeteksi"
    experience = "; ".join((profile.get("experience") or {}).get("value") or []) or "tidak terdeteksi"
    missing_required = (
        ((score_breakdown or {}).get("skill_fit") or {}).get("missing_required") or []
    )

    prompt = f"""Kamu adalah asisten interviewer teknis. Berdasarkan profil kandidat dan kebutuhan job berikut,
buat panduan wawancara dalam format JSON (HANYA JSON, tanpa markdown/teks lain) dengan struktur persis:
{{"technical_questions": ["...", "...", "..."], "behavioral_questions": ["...", "...", "..."], "risk_areas": ["...", "..."]}}

Ketentuan:
- Minimal {MIN_QUESTIONS} pertanyaan teknikal (spesifik ke skill & gap kandidat, bukan generik)
- Minimal {MIN_QUESTIONS} pertanyaan behavioral
- risk_areas: area yang perlu digali/divalidasi lebih lanjut berdasarkan gap kandidat vs job
- Bahasa Indonesia, pertanyaan konkret dan bisa langsung dipakai interviewer

Job: {job.title} ({job.level.value}), department {job.department}
Deskripsi job: {job.description or "-"}
Skill wajib job: {", ".join(job.required_skills) or "-"}
Skill kandidat yang terdeteksi: {skills}
Skill wajib yang BELUM dimiliki kandidat: {", ".join(missing_required) or "tidak ada"}
Pengalaman kandidat: {experience}
"""
    try:
        response = llm.invoke(prompt)
        text = (response.content or "").strip()
        data = _extract_json(text)
    except QuestionGenerationError:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.warning("Interview guide generation failed: %s", exc)
        raise QuestionGenerationError(str(exc)) from exc

    technical = data.get("technical_questions") or []
    behavioral = data.get("behavioral_questions") or []
    risk_areas = data.get("risk_areas") or []
    if len(technical) < 1 or len(behavioral) < 1:
        raise QuestionGenerationError("LLM tidak menghasilkan pertanyaan yang cukup")

    return {
        "technical_questions": technical,
        "behavioral_questions": behavioral,
        "risk_areas": risk_areas,
    }
