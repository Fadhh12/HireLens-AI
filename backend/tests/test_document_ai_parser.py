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
