"""
Text extraction (PyMuPDF, pdfplumber fallback, python-docx) + regex/
heuristic entity extraction (FR-4.1-4.2).

This is a best-effort, rule-based parser — no LLM involved (the LLM
only touches values-fit assist and summaries per FR-5.5, never raw
extraction). Resume layouts vary enormously, so:
- email/phone are extracted with regex and marked `verified: true`
  when the match is well-formed — these are reliable.
- name/education/experience/skills/certifications are heuristic
  (section-header + line-pattern based) and always marked
  `verified: false` — FR-4.4's confidence flag, and FR-4.3 lets the
  recruiter correct them.
This is intentionally not a "solved" NLP problem; see the Phase 3
summary for what's been verified against real-shaped sample CVs and
where it's known to be weak (e.g. heavily templated/graphical CVs,
tables, non-Latin scripts).
"""

import io
import re
from dataclasses import dataclass, field

import fitz  # PyMuPDF
import pdfplumber
from docx import Document

# --- Text extraction ---


class UnsupportedFileTypeError(ValueError):
    pass


class TextExtractionFailedError(RuntimeError):
    """Raised when we genuinely couldn't get usable text out of the file
    (corrupt file, scanned image with no text layer, etc.) — the caller
    (document_ai/service.py) catches this and sets needs_manual_review
    per FR-3.5, instead of raising it out to the API layer."""


_MIN_USABLE_TEXT_LENGTH = 30


def extract_text(content: bytes, filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext == "pdf":
        text = _extract_pdf_text_pymupdf(content)
        if len(text.strip()) < _MIN_USABLE_TEXT_LENGTH:
            # Some PDFs (scanned, oddly encoded) yield near-nothing from
            # PyMuPDF but do better with pdfplumber's layout-aware
            # extraction — worth a second attempt before giving up.
            text = _extract_pdf_text_pdfplumber(content)
        if len(text.strip()) < _MIN_USABLE_TEXT_LENGTH:
            raise TextExtractionFailedError(
                "Tidak ada teks yang bisa diekstrak dari PDF ini (kemungkinan hasil scan tanpa teks)"
            )
        return text

    if ext == "docx":
        text = _extract_docx_text(content)
        if len(text.strip()) < _MIN_USABLE_TEXT_LENGTH:
            raise TextExtractionFailedError("Tidak ada teks yang bisa diekstrak dari file DOCX ini")
        return text

    raise UnsupportedFileTypeError(f"Tipe file .{ext} tidak didukung untuk parsing (hanya PDF/DOCX)")


def _extract_pdf_text_pymupdf(content: bytes) -> str:
    try:
        with fitz.open(stream=content, filetype="pdf") as doc:
            return "\n".join(page.get_text() for page in doc)
    except Exception:
        return ""


def _extract_pdf_text_pdfplumber(content: bytes) -> str:
    try:
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
    except Exception:
        return ""


def _extract_docx_text(content: bytes) -> str:
    try:
        doc = Document(io.BytesIO(content))
        return "\n".join(p.text for p in doc.paragraphs)
    except Exception:
        return ""


# --- Entity extraction ---

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
# Loosely matches Indonesian/international phone formats: +62 812-3456-7890,
# 0812 3456 7890, (021) 555-0100, etc. — final sanity check on digit count.
PHONE_RE = re.compile(r"(\+?\d[\d\s().-]{7,18}\d)")

SECTION_HEADERS: dict[str, list[str]] = {
    "education": ["pendidikan", "riwayat pendidikan", "education"],
    "experience": [
        "pengalaman kerja",
        "pengalaman",
        "riwayat pekerjaan",
        "work experience",
        "experience",
        "employment history",
    ],
    "skills": ["keahlian", "keterampilan", "skill", "skills", "technical skills"],
    "certifications": ["sertifikasi", "sertifikat", "certifications", "certificates"],
}

SKILL_KEYWORDS = [
    "python", "java", "javascript", "typescript", "sql", "postgresql", "mysql", "mongodb",
    "react", "next.js", "nextjs", "vue", "angular", "node.js", "nodejs", "fastapi", "django",
    "flask", "spring", "docker", "kubernetes", "aws", "gcp", "azure", "git", "linux",
    "figma", "excel", "power bi", "tableau", "html", "css", "tailwind", "redux", "graphql",
    "rest api", "microservices", "ci/cd", "agile", "scrum", "machine learning", "data analysis",
]


@dataclass
class Field:
    value: object
    verified: bool = False


@dataclass
class ParsedProfile:
    name: Field
    email: Field
    phone: Field
    education: Field
    experience: Field
    skills: Field
    certifications: Field
    raw_text_length: int = 0
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": {"value": self.name.value, "verified": self.name.verified},
            "email": {"value": self.email.value, "verified": self.email.verified},
            "phone": {"value": self.phone.value, "verified": self.phone.verified},
            "education": {"value": self.education.value, "verified": self.education.verified},
            "experience": {"value": self.experience.value, "verified": self.experience.verified},
            "skills": {"value": self.skills.value, "verified": self.skills.verified},
            "certifications": {"value": self.certifications.value, "verified": self.certifications.verified},
            "raw_text_length": self.raw_text_length,
            "warnings": self.warnings,
        }


def _find_section(text: str, keys: list[str]) -> str | None:
    """Grabs the text block between a header line matching one of `keys`
    and the next header line from any other known section (or the end
    of the document)."""
    lines = text.splitlines()
    all_header_aliases = {alias for aliases in SECTION_HEADERS.values() for alias in aliases}

    start = None
    for i, line in enumerate(lines):
        normalized = line.strip().lower().rstrip(":")
        if normalized in keys:
            start = i + 1
            break
    if start is None:
        return None

    end = len(lines)
    for i in range(start, len(lines)):
        normalized = lines[i].strip().lower().rstrip(":")
        if normalized in all_header_aliases:
            end = i
            break

    block = "\n".join(lines[start:end]).strip()
    return block or None


def _extract_email(text: str) -> Field:
    match = EMAIL_RE.search(text)
    if match:
        return Field(value=match.group(0), verified=True)
    return Field(value=None, verified=False)


def _extract_phone(text: str) -> Field:
    for match in PHONE_RE.finditer(text):
        raw = match.group(1)
        digits = re.sub(r"\D", "", raw)
        if 8 <= len(digits) <= 15:
            return Field(value=raw.strip(), verified=True)
    return Field(value=None, verified=False)


def _extract_name(text: str) -> Field:
    """Heuristic: the first non-empty line that looks like a person's name
    (2-5 title-cased words, no digits/@/section-header words) — resumes
    overwhelmingly put the candidate's name as the very first line."""
    for line in text.splitlines():
        candidate = line.strip()
        if not candidate:
            continue
        if EMAIL_RE.search(candidate) or PHONE_RE.search(candidate):
            continue
        words = candidate.split()
        if 1 < len(words) <= 5 and all(w.replace(".", "").isalpha() for w in words):
            return Field(value=candidate, verified=False)
        # First non-empty line didn't look like a name — stop; scanning
        # deeper risks grabbing a random sentence instead.
        break
    return Field(value=None, verified=False)


def _extract_skills(text: str, section_text: str | None) -> Field:
    if section_text:
        # Split on commas/bullets/newlines, drop empties.
        parts = re.split(r"[,\n•·;]", section_text)
        skills = [p.strip() for p in parts if p.strip() and len(p.strip()) < 40]
        if skills:
            return Field(value=skills, verified=False)

    # Fallback: scan the whole document for known skill keywords.
    lowered = text.lower()
    found = [kw for kw in SKILL_KEYWORDS if kw in lowered]
    return Field(value=found, verified=False)


def _extract_list_section(section_text: str | None) -> Field:
    if not section_text:
        return Field(value=[], verified=False)
    entries = [line.strip("-•· \t") for line in section_text.splitlines() if line.strip()]
    return Field(value=entries, verified=False)


def parse_resume(content: bytes, filename: str) -> ParsedProfile:
    text = extract_text(content, filename)

    education_block = _find_section(text, SECTION_HEADERS["education"])
    experience_block = _find_section(text, SECTION_HEADERS["experience"])
    skills_block = _find_section(text, SECTION_HEADERS["skills"])
    certifications_block = _find_section(text, SECTION_HEADERS["certifications"])

    warnings = []
    if not education_block:
        warnings.append("Bagian riwayat pendidikan tidak terdeteksi otomatis")
    if not experience_block:
        warnings.append("Bagian pengalaman kerja tidak terdeteksi otomatis")

    return ParsedProfile(
        name=_extract_name(text),
        email=_extract_email(text),
        phone=_extract_phone(text),
        education=_extract_list_section(education_block),
        experience=_extract_list_section(experience_block),
        skills=_extract_skills(text, skills_block),
        certifications=_extract_list_section(certifications_block),
        raw_text_length=len(text),
        warnings=warnings,
    )
