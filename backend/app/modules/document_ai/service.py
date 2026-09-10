"""Orchestrates parsing for one candidate: downloads the CV from storage,
runs parser.parse_resume(), and reports success/failure. Failure handling
itself (setting status=needs_manual_review) lives in the background task
(workers/tasks_parsing.py) so this module stays testable in isolation —
see FR-3.5.
"""

from app.core.storage import get_supabase
from app.core.config import get_settings
from app.modules.document_ai.parser import ParsedProfile, parse_resume

settings = get_settings()


def parse_candidate_cv(cv_file_path: str, cv_filename: str) -> ParsedProfile:
    """Downloads the CV bytes from the private bucket and parses them.
    Raises whatever parser.extract_text() raises (UnsupportedFileTypeError,
    TextExtractionFailedError) — callers decide how to handle that."""
    client = get_supabase()
    content = client.storage.from_(settings.supabase_storage_bucket).download(cv_file_path)
    return parse_resume(content, cv_filename)
