"""Text extraction (PyMuPDF/pdfplumber for PDF, python-docx for DOCX) +
entity extraction (regex/spaCy) -> structured profile (FR-4.1-4.2). Phase 3.

This is the module the brief calls out as "allowed to take the longest" —
get it working on real sample CVs before moving to Phase 4.
"""

# TODO(Phase 3): extract_text(file_bytes, content_type) -> str
# TODO(Phase 3): extract_entities(text) -> ParsedProfile (name, email, phone, education, experience, skills)
