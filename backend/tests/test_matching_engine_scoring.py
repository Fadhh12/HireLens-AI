"""Unit tests for the rule-based matching engine (FR-5, BR-6) — the part
of the product the brief calls out as most important to test well.
scoring.py never imports llm_assist.py, so none of this touches the
network or Gemini."""

import uuid

import pytest

from app.modules.jobs.model import JobLevel, JobPosting, JobStatus
from app.modules.matching_engine.model import MatchLabel
from app.modules.matching_engine.scoring import (
    compute_final_score,
    label_for_score,
    redistribute_weights,
    score_experience_fit,
    score_skill_fit,
    score_values_fit_from_assessment,
)


# --- score_skill_fit ---


def test_skill_fit_full_match_scores_100() -> None:
    result = score_skill_fit(["Python", "SQL"], required_skills=["Python", "SQL"], nice_to_have_skills=[])
    assert result["score"] == 100.0
    assert result["missing_required"] == []


def test_skill_fit_partial_required_match() -> None:
    result = score_skill_fit(["Python"], required_skills=["Python", "SQL"], nice_to_have_skills=[])
    assert result["score"] == 50.0
    assert result["missing_required"] == ["sql"]


def test_skill_fit_is_case_insensitive() -> None:
    result = score_skill_fit(["PYTHON"], required_skills=["python"], nice_to_have_skills=[])
    assert result["score"] == 100.0


def test_skill_fit_weights_required_higher_than_nice_to_have() -> None:
    # All required matched, no nice-to-have matched -> 0.7 * 100 = 70
    result = score_skill_fit(
        ["Python"], required_skills=["Python"], nice_to_have_skills=["Docker"]
    )
    assert result["score"] == 70.0

    # All required AND all nice-to-have matched -> 100
    result_full = score_skill_fit(
        ["Python", "Docker"], required_skills=["Python"], nice_to_have_skills=["Docker"]
    )
    assert result_full["score"] == 100.0


def test_skill_fit_no_required_skills_treated_as_satisfied() -> None:
    result = score_skill_fit(["Python"], required_skills=[], nice_to_have_skills=[])
    assert result["score"] == 100.0


def test_skill_fit_no_candidate_skills_scores_zero() -> None:
    result = score_skill_fit([], required_skills=["Python"], nice_to_have_skills=[])
    assert result["score"] == 0.0
    assert result["missing_required"] == ["python"]


# --- score_experience_fit ---


def test_experience_fit_meets_requirement_exactly() -> None:
    assert score_experience_fit(2.0, 2)["score"] == 100.0


def test_experience_fit_exceeds_requirement_caps_at_100() -> None:
    assert score_experience_fit(10.0, 2)["score"] == 100.0


def test_experience_fit_below_requirement_is_proportional() -> None:
    assert score_experience_fit(1.0, 2)["score"] == 50.0


def test_experience_fit_zero_required_years_always_100() -> None:
    assert score_experience_fit(0.0, 0)["score"] == 100.0


# --- score_values_fit_from_assessment ---


def test_values_fit_none_without_assessment() -> None:
    assert score_values_fit_from_assessment(None) is None
    assert score_values_fit_from_assessment({}) is None


def test_values_fit_none_when_no_numeric_competency_scores() -> None:
    assert score_values_fit_from_assessment({"mbti": "INTJ"}) is None


def test_values_fit_scales_1_to_5_onto_0_to_100() -> None:
    # avg score 3 (midpoint of 1-5) -> 50
    result = score_values_fit_from_assessment({"competency_scores": {"a": 3, "b": 3}})
    assert result["score"] == 50.0

    # avg score 5 (max) -> 100
    result_max = score_values_fit_from_assessment({"competency_scores": {"a": 5}})
    assert result_max["score"] == 100.0

    # avg score 1 (min) -> 0
    result_min = score_values_fit_from_assessment({"competency_scores": {"a": 1}})
    assert result_min["score"] == 0.0


# --- redistribute_weights (BR-6) ---


def test_redistribute_weights_unchanged_when_values_available() -> None:
    assert redistribute_weights(50, 30, 20, values_available=True) == (50, 30, 20)


def test_redistribute_weights_proportional_when_values_missing() -> None:
    skill, experience, values = redistribute_weights(50, 30, 20, values_available=False)
    assert values == 0.0
    assert skill == pytest.approx(50 + 20 * (50 / 80))  # 62.5
    assert experience == pytest.approx(30 + 20 * (30 / 80))  # 37.5
    assert skill + experience == pytest.approx(100.0)


def test_redistribute_weights_degenerate_all_weight_on_values() -> None:
    skill, experience, values = redistribute_weights(0, 0, 100, values_available=False)
    assert (skill, experience, values) == (50.0, 50.0, 0.0)


# --- label_for_score (FR-5.4) ---


@pytest.mark.parametrize(
    "score,expected",
    [
        (100.0, MatchLabel.strong_match),
        (80.0, MatchLabel.strong_match),
        (79.9, MatchLabel.consider),
        (60.0, MatchLabel.consider),
        (59.9, MatchLabel.not_a_fit),
        (0.0, MatchLabel.not_a_fit),
    ],
)
def test_label_thresholds(score: float, expected: MatchLabel) -> None:
    assert label_for_score(score) == expected


# --- compute_final_score (integration of the above) ---


def _make_job(**overrides) -> JobPosting:
    defaults = dict(
        id=uuid.uuid4(),
        title="Backend Engineer",
        department="Engineering",
        description="",
        required_skills=["Python", "SQL"],
        nice_to_have_skills=["Docker"],
        min_experience_years=2,
        level=JobLevel.mid,
        weight_skill_fit=50,
        weight_experience_fit=30,
        weight_values_fit=20,
        status=JobStatus.active,
        created_by=uuid.uuid4(),
    )
    defaults.update(overrides)
    return JobPosting(**defaults)


def test_compute_final_score_with_full_assessment() -> None:
    job = _make_job()
    result = compute_final_score(
        job=job,
        candidate_skills=["Python", "SQL", "Docker"],  # 100 skill fit
        candidate_years=2.0,  # 100 experience fit
        assessment_input={"competency_scores": {"a": 5}},  # 100 values fit
    )
    assert result["final_score"] == 100.0
    assert result["label"] == MatchLabel.strong_match
    # Weights unchanged since values-fit was available.
    assert result["skill_fit"]["weight"] == 50
    assert result["values_fit"]["weight"] == 20


def test_compute_final_score_without_assessment_redistributes_weights() -> None:
    job = _make_job()
    result = compute_final_score(
        job=job,
        candidate_skills=["Python", "SQL", "Docker"],  # 100 skill fit
        candidate_years=2.0,  # 100 experience fit
        assessment_input=None,
    )
    # No values-fit component -> weight redistributed to skill+experience,
    # both maxed out -> final score still 100 despite missing assessment.
    assert result["final_score"] == 100.0
    assert result["values_fit"]["weight"] == 0.0
    assert result["values_fit"]["score"] is None


def test_compute_final_score_partial_match_lands_in_consider() -> None:
    job = _make_job()
    result = compute_final_score(
        job=job,
        candidate_skills=["Python"],  # missing SQL (required) and Docker (nice-to-have)
        candidate_years=1.0,  # half of required 2 years
        assessment_input={"competency_scores": {"a": 4}},  # (4-1)/4*100 = 75
    )
    # skill: (0.5 required * 0.7 + 0 nice-to-have * 0.3) * 100 = 35
    # experience: 1/2 * 100 = 50
    # values: 75
    # final = (35*50 + 50*30 + 75*20) / 100 = (1750+1500+1500)/100 = 47.5
    assert result["skill_fit"]["score"] == 35.0
    assert result["experience_fit"]["score"] == 50.0
    assert result["values_fit"]["score"] == 75.0
    assert result["final_score"] == 47.5
    assert result["label"] == MatchLabel.not_a_fit


def test_compute_final_score_never_negative_or_above_100() -> None:
    job = _make_job(weight_skill_fit=100, weight_experience_fit=0, weight_values_fit=0)
    result = compute_final_score(job=job, candidate_skills=[], candidate_years=0, assessment_input=None)
    assert 0.0 <= result["final_score"] <= 100.0
