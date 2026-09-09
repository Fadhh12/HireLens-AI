"""Pydantic schemas for job postings, incl. weight-sum-100 validator (FR-2.3). Phase 2."""

# TODO(Phase 2): JobPostingCreate/Update with a model_validator enforcing
# weight_skill_fit + weight_experience_fit + weight_values_fit == 100
