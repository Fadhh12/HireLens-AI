"""
LLM-assisted pieces only: a qualitative values-fit note + a candidate
summary (FR-5.5). Never produces the final numeric score — scoring.py
computes every number, this file only adds natural-language text on
top of what's already been computed.

Provider is Gemini via langchain-google-genai, selected through one
function (get_llm) so swapping providers later means adding an adapter
here, not touching scoring.py, service.py, or any caller.

Must degrade gracefully: any failure (timeout, API error, missing key)
returns None and the caller proceeds with the rule-based score alone,
marking the LLM piece as unavailable in score_breakdown (SRS §7 edge
case, applied here to the assist calls rather than the score itself,
which was never LLM-derived to begin with — see scoring.py).

Known pinning quirk: langchain-google-genai==2.0.7 (paired with
langchain==0.3.13, both pinned for the rest of the app) still imports
the now-deprecated `google.generativeai` SDK and prints a FutureWarning
on first use. A newer langchain-google-genai needs langchain-core 1.x,
a breaking rewrite that would ripple through every other LangChain
pin in this project — evaluated and deliberately not done for that
reason. Revisit if/when the whole LangChain stack is bumped together.
"""

import logging
from functools import lru_cache

from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.config import get_settings
from app.modules.candidates.model import Candidate
from app.modules.jobs.model import JobPosting

logger = logging.getLogger(__name__)

LLM_TIMEOUT_SECONDS = 10


@lru_cache
def get_llm() -> ChatGoogleGenerativeAI | None:
    settings = get_settings()
    if not settings.google_api_key:
        return None
    return ChatGoogleGenerativeAI(
        model=settings.llm_model_name,
        google_api_key=settings.google_api_key,
        timeout=LLM_TIMEOUT_SECONDS,
        temperature=0.3,
    )


def _safe_invoke(prompt: str) -> str | None:
    llm = get_llm()
    if llm is None:
        return None
    try:
        response = llm.invoke(prompt)
        text = (response.content or "").strip()
        return text or None
    except Exception as exc:  # noqa: BLE001 - deliberately broad, see module docstring
        logger.warning("LLM call failed, falling back to rule-based-only: %s", exc)
        return None


def generate_candidate_summary(candidate: Candidate, job: JobPosting) -> str | None:
    """UI/UX Layar 7: 2-4 sentence AI summary shown with an "AI-generated" badge."""
    profile = candidate.parsed_profile or {}
    skills = ", ".join((profile.get("skills") or {}).get("value") or []) or "tidak terdeteksi"
    experience = "; ".join((profile.get("experience") or {}).get("value") or []) or "tidak terdeteksi"
    education = "; ".join((profile.get("education") or {}).get("value") or []) or "tidak terdeteksi"

    prompt = f"""Kamu adalah asisten recruiter. Tulis ringkasan singkat (2-4 kalimat, Bahasa Indonesia)
tentang kandidat berikut untuk posisi "{job.title}" di departemen {job.department}.
Fokus pada kecocokan dan hal yang menonjol. Jangan mengarang informasi yang tidak ada di data berikut.

Nama: {candidate.full_name}
Skill terdeteksi: {skills}
Pengalaman: {experience}
Pendidikan: {education}

Ringkasan:"""
    return _safe_invoke(prompt)


def generate_values_fit_note(assessment_input: dict | None, job: JobPosting) -> str | None:
    """Qualitative note explaining the values-fit *number* scoring.py already
    computed — this text never determines the score itself (FR-5.5)."""
    if not assessment_input:
        return None

    mbti = assessment_input.get("mbti")
    competency_scores = assessment_input.get("competency_scores") or {}

    prompt = f"""Kamu adalah asisten recruiter. Berdasarkan hasil asesmen manual kandidat berikut,
tulis catatan singkat (1-2 kalimat, Bahasa Indonesia) tentang values/behavioral fit kandidat
terhadap posisi "{job.title}" level {job.level.value}. Jangan sebutkan angka skor akhir, cukup
jelaskan kekuatan/area yang perlu digali dari data asesmen ini.

Tipe MBTI: {mbti or "tidak diisi"}
Skor kompetensi (1-5): {competency_scores or "tidak diisi"}

Catatan:"""
    return _safe_invoke(prompt)
