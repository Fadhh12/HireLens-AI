"""
Rule-based scoring — the core value of the product (FR-5, BR-5, BR-6).

Deterministic and auditable: skill fit (required vs nice-to-have overlap),
experience fit (years + relevance), values fit (from manual assessment
input, weight redistributed proportionally if absent per BR-6). LLM is
NEVER the source of the numeric score (SRS FR-5.5) — see llm_assist.py
for where LLM only assists values-fit qualitative notes and summaries.

This file gets the heaviest unit-test coverage (brief §6 / Task 6.2).
Phase 4.
"""

# TODO(Phase 4): score_skill_fit(candidate_skills, required_skills, nice_to_have_skills) -> dict
# TODO(Phase 4): score_experience_fit(candidate_years, required_years) -> dict
# TODO(Phase 4): score_values_fit(assessment_input) -> dict | None
# TODO(Phase 4): compute_final_score(skill, experience, values, weights) -> (final_score, label, breakdown)
# TODO(Phase 4): label_for_score(score, thresholds) -> "strong_match" | "consider" | "not_a_fit"  (FR-5.4)
