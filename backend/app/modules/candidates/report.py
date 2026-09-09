"""PDF report export (FR-9). Built with PyMuPDF (already a dependency
for resume parsing) rather than adding reportlab/fpdf2 just for this —
a simple text-layout report doesn't need much more.
"""

import io

import fitz

from app.modules.candidates.model import Candidate
from app.modules.jobs.model import JobPosting
from app.modules.matching_engine.model import CandidateScore

_PAGE_WIDTH, _PAGE_HEIGHT = 595, 842  # A4 in points
_MARGIN = 50
_LINE_HEIGHT = 16

STATUS_LABEL = {
    "new": "Baru",
    "screening": "Screening",
    "shortlisted": "Shortlisted",
    "interviewed": "Interviewed",
    "hired": "Hired",
    "rejected": "Rejected",
    "needs_manual_review": "Perlu Ditinjau Manual",
}
LABEL_TEXT = {"strong_match": "Strong Match", "consider": "Consider", "not_a_fit": "Not a Fit"}


class _Writer:
    """Tiny helper: writes lines top-to-bottom, starting a new page on overflow."""

    def __init__(self, doc: fitz.Document):
        self.doc = doc
        self.page = doc.new_page(width=_PAGE_WIDTH, height=_PAGE_HEIGHT)
        self.y = _MARGIN

    def _ensure_space(self):
        if self.y > _PAGE_HEIGHT - _MARGIN:
            self.page = self.doc.new_page(width=_PAGE_WIDTH, height=_PAGE_HEIGHT)
            self.y = _MARGIN

    def line(self, text: str, size: float = 10, bold: bool = False, color=(0.11, 0.12, 0.15)):
        self._ensure_space()
        self.page.insert_text(
            (_MARGIN, self.y), text, fontsize=size, color=color, fontname="helv" if not bold else "hebo"
        )
        self.y += _LINE_HEIGHT * (size / 10)

    def gap(self, amount: float = 8):
        self.y += amount


def build_candidate_report_pdf(candidate: Candidate, job: JobPosting, score: CandidateScore | None) -> bytes:
    doc = fitz.open()
    w = _Writer(doc)

    w.line("HireLens AI — Ringkasan Kandidat", size=16, bold=True, color=(0.055, 0.31, 0.29))
    w.gap(6)

    w.line(f"Kandidat: {candidate.full_name}", bold=True)
    w.line(f"Email: {candidate.email}    Telepon: {candidate.phone}")
    w.line(f"Job posting: {job.title} ({job.department})")
    w.line(f"Status: {STATUS_LABEL.get(candidate.status.value, candidate.status.value)}")
    w.line(f"Tanggal apply: {candidate.applied_at.strftime('%d %B %Y')}")
    w.gap(10)

    if score:
        w.line("Skor Kecocokan", size=13, bold=True, color=(0.055, 0.31, 0.29))
        w.line(f"Skor akhir: {float(score.final_score):.1f} — {LABEL_TEXT.get(score.label.value, score.label.value)}")
        breakdown = score.score_breakdown or {}
        skill = breakdown.get("skill_fit", {})
        experience = breakdown.get("experience_fit", {})
        values = breakdown.get("values_fit", {})
        w.line(
            f"  Skill Fit: {skill.get('score')} (bobot {skill.get('weight')}%) — "
            f"skill wajib belum terpenuhi: {', '.join(skill.get('missing_required') or []) or 'tidak ada'}"
        )
        w.line(
            f"  Experience Fit: {experience.get('score')} (bobot {experience.get('weight')}%) — "
            f"{experience.get('candidate_years')} thn (min. {experience.get('required_years')} thn)"
        )
        if values.get("score") is not None:
            w.line(f"  Values Fit: {values.get('score')} (bobot {values.get('weight')}%)")
        if breakdown.get("candidate_summary"):
            w.gap(6)
            w.line("Ringkasan AI:", bold=True)
            for chunk in _wrap(breakdown["candidate_summary"], 95):
                w.line(f"  {chunk}")
        w.gap(10)
    else:
        w.line("Skor belum tersedia untuk kandidat ini.")
        w.gap(10)

    profile = candidate.parsed_profile or {}
    skills = (profile.get("skills") or {}).get("value") or []
    if skills:
        w.line("Skill terdeteksi:", bold=True)
        w.line(f"  {', '.join(skills)}")
        w.gap(6)

    w.gap(14)
    w.line("=" * 90, size=8, color=(0.6, 0.6, 0.6))
    for chunk in _wrap(
        "Disclaimer: Skor dan ringkasan pada laporan ini dihasilkan oleh alat bantu AI (HireLens AI) "
        "dan TIDAK merupakan keputusan hiring final. Keputusan akhir tetap berada di tangan recruiter/"
        "hiring manager berdasarkan pertimbangan menyeluruh.",
        100,
    ):
        w.line(chunk, size=8, color=(0.4, 0.4, 0.45))

    buf = io.BytesIO()
    doc.save(buf)
    doc.close()
    return buf.getvalue()


def _wrap(text: str, width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate_line = f"{current} {word}".strip()
        if len(candidate_line) > width:
            lines.append(current)
            current = word
        else:
            current = candidate_line
    if current:
        lines.append(current)
    return lines
