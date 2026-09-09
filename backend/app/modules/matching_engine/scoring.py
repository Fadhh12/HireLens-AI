"""
Rule-based scoring — the core value of the product (FR-5, BR-5, BR-6).

Deterministic and auditable: every function here is a pure function of
its inputs, so a given candidate+job snapshot always produces the same
score, and every component can be explained. LLM never touches this
file — see llm_assist.py for where it only adds a qualitative note and
a candidate summary, never a number (FR-5.5).

Weighting choices the docs leave unspecified, made explicit here so
they're easy to find and tune:
- Skill Fit sub-weights required vs nice-to-have skills 70/30 (FR-5.1
  says "bobot berbeda" without giving numbers).
- Experience Fit is years-only (candidate years / required years,
  capped at 100%) — no "role relevance" scoring, since that would need
  semantic matching and FR-5.5 scopes LLM assistance to values-fit and
  summaries only, not skill/experience fit.
"""

from app.modules.jobs.model import JobPosting
from app.modules.matching_engine.model import MatchLabel

MODEL_VERSION = "matching-engine-v1.0"

SKILL_REQUIRED_SUBWEIGHT = 0.7
SKILL_NICE_TO_HAVE_SUBWEIGHT = 0.3

# FR-5.4 defaults — "dapat dikonfigurasi Admin" isn't wired to a settings
# UI yet, so these are the fixed defaults for now.
STRONG_MATCH_THRESHOLD = 80.0
CONSIDER_THRESHOLD = 60.0

# BR-6: values-fit competency scores are 1-5; map linearly to 0-100.
COMPETENCY_SCORE_MIN = 1
COMPETENCY_SCORE_MAX = 5


def _normalize(skills: list[str]) -> set[str]:
    return {s.strip().lower() for s in skills if s.strip()}


def score_skill_fit(
    candidate_skills: list[str], required_skills: list[str], nice_to_have_skills: list[str]
) -> dict:
    """FR-5.1: overlap between candidate skills and job's required +
    nice-to-have skills, required weighted higher."""
    cand = _normalize(candidate_skills)
    required = _normalize(required_skills)
    nice_to_have = _normalize(nice_to_have_skills)

    matched_required = sorted(required & cand)
    missing_required = sorted(required - cand)
    matched_nice_to_have = sorted(nice_to_have & cand)

    required_ratio = len(matched_required) / len(required) if required else 1.0
    nice_to_have_ratio = len(matched_nice_to_have) / len(nice_to_have) if nice_to_have else None

    if nice_to_have_ratio is None:
        score = required_ratio * 100
    else:
        score = (
            required_ratio * SKILL_REQUIRED_SUBWEIGHT + nice_to_have_ratio * SKILL_NICE_TO_HAVE_SUBWEIGHT
        ) * 100

    return {
        "score": round(score, 1),
        "matched_required": matched_required,
        "missing_required": missing_required,
        "matched_nice_to_have": matched_nice_to_have,
    }


def score_experience_fit(candidate_years: float, required_years: int) -> dict:
    """FR-5.1: candidate years vs job's minimum — linear ratio, capped at 100."""
    if required_years <= 0:
        score = 100.0
    else:
        score = min(100.0, (candidate_years / required_years) * 100)

    return {
        "score": round(score, 1),
        "candidate_years": candidate_years,
        "required_years": required_years,
    }


def score_values_fit_from_assessment(assessment_input: dict | None) -> dict | None:
    """BR-6: only produces a score when a manual assessment was filled in
    (competency_scores present). MBTI alone doesn't yield a number — it's
    descriptive, not a 1-5 scale — so it's passed through for the LLM
    note (see llm_assist.py) but doesn't affect the numeric score."""
    if not assessment_input:
        return None
    competency_scores = assessment_input.get("competency_scores") or {}
    numeric_scores = [v for v in competency_scores.values() if isinstance(v, (int, float))]
    if not numeric_scores:
        return None

    avg = sum(numeric_scores) / len(numeric_scores)
    span = COMPETENCY_SCORE_MAX - COMPETENCY_SCORE_MIN
    score = ((avg - COMPETENCY_SCORE_MIN) / span) * 100 if span else 0.0
    score = max(0.0, min(100.0, score))

    return {
        "score": round(score, 1),
        "competency_scores": competency_scores,
        "mbti": assessment_input.get("mbti"),
    }


def redistribute_weights(
    weight_skill: float, weight_experience: float, weight_values: float, values_available: bool
) -> tuple[float, float, float]:
    """BR-6: no assessment -> values-fit weight (0) is redistributed
    proportionally to skill/experience by their existing relative share."""
    if values_available:
        return weight_skill, weight_experience, weight_values

    total_other = weight_skill + weight_experience
    if total_other <= 0:
        # Degenerate case (all weight was on values) — split evenly rather
        # than divide by zero.
        return 50.0, 50.0, 0.0

    new_skill = weight_skill + weight_values * (weight_skill / total_other)
    new_experience = weight_experience + weight_values * (weight_experience / total_other)
    return new_skill, new_experience, 0.0


def label_for_score(score: float) -> MatchLabel:
    """FR-5.4."""
    if score >= STRONG_MATCH_THRESHOLD:
        return MatchLabel.strong_match
    if score >= CONSIDER_THRESHOLD:
        return MatchLabel.consider
    return MatchLabel.not_a_fit


def compute_final_score(
    job: JobPosting,
    candidate_skills: list[str],
    candidate_years: float,
    assessment_input: dict | None,
) -> dict:
    """FR-5.2: weighted combination of the three components, using the
    job's configured weights (redistributed per BR-6 when values-fit is
    unavailable). Returns everything needed to build score_breakdown —
    callers add the LLM-assisted note/summary on top (never the number)."""
    skill = score_skill_fit(candidate_skills, job.required_skills, job.nice_to_have_skills)
    experience = score_experience_fit(candidate_years, job.min_experience_years)
    values = score_values_fit_from_assessment(assessment_input)

    eff_skill_w, eff_experience_w, eff_values_w = redistribute_weights(
        float(job.weight_skill_fit),
        float(job.weight_experience_fit),
        float(job.weight_values_fit),
        values_available=values is not None,
    )

    final = (
        skill["score"] * eff_skill_w
        + experience["score"] * eff_experience_w
        + (values["score"] if values else 0.0) * eff_values_w
    ) / 100
    final = round(max(0.0, min(100.0, final)), 1)

    return {
        "final_score": final,
        "label": label_for_score(final),
        "skill_fit": {**skill, "weight": round(eff_skill_w, 2)},
        "experience_fit": {**experience, "weight": round(eff_experience_w, 2)},
        "values_fit": (
            {**values, "weight": round(eff_values_w, 2)} if values else {"score": None, "weight": 0.0}
        ),
    }
