"""
LLM-assisted pieces only: values-fit qualitative note + candidate summary
(FR-5.5). Never produces the final numeric score.

Provider-agnostic interface (project default: Gemini via
langchain-google-genai, per .env LLM_PROVIDER) so swapping to OpenAI
later is a matter of adding an adapter here, not touching scoring.py
or any caller.

Must degrade gracefully on timeout/failure — scoring.py keeps computing
skill/experience fit and marks values fit as "pending" (SRS §7 edge case).
Phase 4.
"""

# TODO(Phase 4): class LLMProvider(Protocol): summarize_candidate(...), assist_values_fit(...)
# TODO(Phase 4): GeminiProvider(LLMProvider) using langchain_google_genai.ChatGoogleGenerativeAI
# TODO(Phase 4): get_llm_provider() -> LLMProvider, selected via settings.llm_provider
