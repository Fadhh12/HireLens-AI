"""Unit tests for resume text/entity extraction (FR-4.1-4.2, FR-3.5).

Builds small real PDF/DOCX files in-memory (via PyMuPDF/python-docx)
rather than hardcoding parser output — these exercise the actual
extraction path end to end, same as the manual runs against the
generated sample CVs described in the Phase 3 summary.
"""

import io

import fitz
import pytest
from docx import Document

from app.modules.document_ai.parser import (
    TextExtractionFailedError,
    UnsupportedFileTypeError,
    _estimate_experience_years,
    parse_resume,
)

CV_TEXT = """Budi Santoso
budi.santoso@gmail.com | 0812-3456-7890

Pendidikan
S1 Teknik Informatika, Institut Teknologi Bandung (2018-2022)

Pengalaman Kerja
Backend Engineer, PT Teknologi Nusantara (2022-2025)

Keahlian
Python, FastAPI, PostgreSQL
"""


def _make_pdf_bytes(text: str) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    y = 50
    for line in text.split("\n"):
        page.insert_text((50, y), line, fontsize=11)
        y += 16
    data = doc.tobytes()
    doc.close()
    return data


def _make_docx_bytes(text: str) -> bytes:
    doc = Document()
    for line in text.split("\n"):
        doc.add_paragraph(line)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def test_parse_resume_pdf_extracts_all_fields() -> None:
    profile = parse_resume(_make_pdf_bytes(CV_TEXT), "cv.pdf")
    d = profile.to_dict()

    assert d["name"]["value"] == "Budi Santoso"
    assert d["email"]["value"] == "budi.santoso@gmail.com"
    assert d["email"]["verified"] is True
    assert d["phone"]["value"] == "0812-3456-7890"
    assert d["phone"]["verified"] is True
    assert "Institut Teknologi Bandung" in d["education"]["value"][0]
    assert "PT Teknologi Nusantara" in d["experience"]["value"][0]
    assert "Python" in d["skills"]["value"]
    assert d["warnings"] == []


def test_parse_resume_docx_extracts_all_fields() -> None:
    profile = parse_resume(_make_docx_bytes(CV_TEXT), "cv.docx")
    d = profile.to_dict()

    assert d["name"]["value"] == "Budi Santoso"
    assert d["email"]["value"] == "budi.santoso@gmail.com"


def test_parse_resume_missing_sections_flags_warnings_not_crash() -> None:
    unstructured = "Rina Kusuma\nrina@example.com, 081234567890\nMarketing professional."
    profile = parse_resume(_make_pdf_bytes(unstructured), "cv.pdf")
    d = profile.to_dict()

    assert d["email"]["value"] == "rina@example.com"
    assert d["education"]["value"] == []
    assert "pendidikan" in d["warnings"][0].lower()


def test_extract_text_corrupt_pdf_raises_text_extraction_failed() -> None:
    with pytest.raises(TextExtractionFailedError):
        parse_resume(b"not a real pdf at all", "corrupt.pdf")


def test_extract_text_unsupported_type_raises() -> None:
    with pytest.raises(UnsupportedFileTypeError):
        parse_resume(b"hello", "resume.txt")


def test_estimate_experience_years_plain_year_range_unchanged() -> None:
    # The original supported shape — must keep working exactly as before.
    result = _estimate_experience_years("Backend Engineer (2022-2025)", current_year=2026)
    assert result.value == 3.0


def test_estimate_experience_years_counts_month_to_month_same_year_ranges() -> None:
    # Real bug: "Jun-Aug 2026" (no year next to the first month) used to
    # match nothing at all and silently contribute zero — undercounting
    # every internship/bootcamp-style entry a CV lists this way.
    result = _estimate_experience_years("AI Bootcamp\nJun - Aug 2026", current_year=2026, current_month=9)
    assert result.value == 0.2  # 3/12 months, rounded to 1 decimal like the rest of this function


def test_estimate_experience_years_counts_month_present_ranges() -> None:
    # "Mon YYYY - Present" should count the partial year already elapsed,
    # not just whole calendar years.
    result = _estimate_experience_years("Ambassador\nApr 2026 - Present", current_year=2026, current_month=9)
    assert result.value == 0.4  # 5/12 months elapsed, rounded to 1 decimal


def test_estimate_experience_years_does_not_double_count_overlapping_matches() -> None:
    # "Sep 2025 - Present" matches the year-range pattern; it must not
    # also get picked up by the month-range pattern.
    result = _estimate_experience_years("Role\nSep 2025 - Present", current_year=2026, current_month=9)
    assert result.value == 1.0


def test_find_section_projects_header_stops_certifications_bleed() -> None:
    # Real bug: an unrecognized "PROJECTS" header let _find_section's
    # certifications block run past it and swallow every project bullet.
    text = (
        "Sertifikasi\nAWS Certified Developer\n\n"
        "PROJECTS\nBuilt a hotel reservation system\nBuilt a waste detection model"
    )
    profile = parse_resume(_make_pdf_bytes(text), "cv.pdf")
    certs = profile.to_dict()["certifications"]["value"]
    assert certs == ["AWS Certified Developer"]
    assert not any("hotel reservation" in c.lower() for c in certs)
