"""
Seed realistic demo data for portfolio/demo purposes (Task Breakdown 6.4).

Deliberately does NOT fabricate scores — every candidate here goes
through the real parser (parse_resume) and the real rule-based scoring
engine (compute_and_save_score), same code path as production. If the
matching engine is weak on some CV shape, this script will show that
weakness rather than paper over it (brief §7).

Run once against a fresh-ish database (safe to re-run — skips users,
jobs (by title), and candidates (by job + email) that already exist):

    cd backend
    python scripts/seed_demo_data.py

Does NOT need Celery/Redis running — parsing and scoring are called
synchronously here rather than via the async task queue, so seeding
is a single deterministic script run.
"""

import asyncio
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import fitz  # noqa: E402

from app.db.session import SessionLocal  # noqa: E402
from app.modules.auth.model import UserRole  # noqa: E402
from app.modules.auth.schema import UserCreate  # noqa: E402
from app.modules.auth.service import create_user, get_user_by_email  # noqa: E402
from app.modules.candidates import service as candidates_service  # noqa: E402
from app.modules.candidates.model import Candidate  # noqa: E402
from app.modules.document_ai.parser import parse_resume  # noqa: E402
from app.modules.jobs import service as jobs_service  # noqa: E402
from app.modules.jobs.model import JobLevel, JobPosting, JobStatus  # noqa: E402
from app.modules.jobs.schema import JobPostingCreate  # noqa: E402
from app.modules.matching_engine.service import compute_and_save_score  # noqa: E402


class _FakeUploadFile:
    """Mimics just enough of fastapi.UploadFile for candidates.service
    to validate/read it, without going through an actual HTTP request."""

    def __init__(self, filename: str, content: bytes, content_type: str):
        self.filename = filename
        self.content_type = content_type
        self._content = content

    async def read(self) -> bytes:
        return self._content


def _pdf_from_text(text: str) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    y = 50
    for line in text.split("\n"):
        page.insert_text((50, y), line, fontsize=11)
        y += 16
    data = doc.tobytes()
    doc.close()
    return data


DEMO_USERS = [
    {"name": "Sarah Hartono", "email": "sarah.recruiter@hirelens.ai", "password": "Recruiter123", "role": UserRole.recruiter},
    {"name": "Dimas Pratama", "email": "dimas.hm@hirelens.ai", "password": "HiringMgr123", "role": UserRole.hiring_manager},
    {"name": "Rani Oktaviani", "email": "rani.interviewer@hirelens.ai", "password": "Interview123", "role": UserRole.interviewer},
]

JOBS = [
    {
        "title": "Backend Engineer",
        "department": "Engineering",
        "description": "Membangun dan memelihara REST API untuk platform inti perusahaan menggunakan Python/FastAPI dan PostgreSQL.",
        "required_skills": ["Python", "SQL", "PostgreSQL"],
        "nice_to_have_skills": ["Docker", "AWS"],
        "min_experience_years": 2,
        "level": JobLevel.mid,
        "weight_skill_fit": 50,
        "weight_experience_fit": 30,
        "weight_values_fit": 20,
    },
    {
        "title": "Product Manager",
        "department": "Product",
        "description": "Memimpin roadmap produk, kerja sama lintas tim engineering/design untuk merilis fitur baru.",
        "required_skills": ["Product Management", "SQL"],
        "nice_to_have_skills": ["Figma", "Agile"],
        "min_experience_years": 1,
        "level": JobLevel.mid,
        "weight_skill_fit": 40,
        "weight_experience_fit": 30,
        "weight_values_fit": 30,
    },
    # "Junior Frontend" — NOT created here on purpose: this one already exists
    # in the DB (created by the user via the UI). Matched by title below so we
    # reuse its real id and just add candidates to it, same as any other job
    # skip-if-exists — never recreate/duplicate a job a human already made.
    {
        "title": "Junior Frontend",
        "department": "IT",
        "description": "placeholder — only used if this job doesn't already exist",
        "required_skills": ["TypeScript", "React.js", "HTML", "CSS", "Next.js"],
        "nice_to_have_skills": ["Team work", "Critical Thinking"],
        "min_experience_years": 0,
        "level": JobLevel.junior,
        "weight_skill_fit": 35,
        "weight_experience_fit": 45,
        "weight_values_fit": 20,
    },
    {
        "title": "Data Analyst",
        "department": "Business Intelligence",
        "description": "Menganalisis data operasional & bisnis untuk mendukung pengambilan keputusan, membuat dashboard dan laporan rutin.",
        "required_skills": ["SQL", "Excel", "Data Visualization"],
        "nice_to_have_skills": ["Python", "Tableau"],
        "min_experience_years": 1,
        "level": JobLevel.junior,
        "weight_skill_fit": 45,
        "weight_experience_fit": 30,
        "weight_values_fit": 25,
    },
    {
        "title": "UX Designer",
        "department": "Product",
        "description": "Merancang pengalaman pengguna produk digital, dari riset hingga wireframe & prototype siap dev.",
        "required_skills": ["Figma", "UI Design", "User Research"],
        "nice_to_have_skills": ["Prototyping", "Wireframing"],
        "min_experience_years": 1,
        "level": JobLevel.mid,
        "weight_skill_fit": 40,
        "weight_experience_fit": 25,
        "weight_values_fit": 35,
    },
]

# (job index, name, email, phone, cv text, assessment or None)
CANDIDATES = [
    (
        0, "Budi Santoso", "budi.santoso@example.com", "0812-3456-7890",
        """Budi Santoso
budi.santoso@example.com | 0812-3456-7890

Pendidikan
S1 Teknik Informatika, Institut Teknologi Bandung (2018-2022)

Pengalaman Kerja
Backend Engineer, PT Teknologi Nusantara (2022-2025)
Membangun dan memelihara REST API menggunakan FastAPI dan PostgreSQL
Software Engineer Intern, Startup Kilat (2021-2022)

Keahlian
Python, SQL, PostgreSQL, Docker, AWS, Git""",
        {"mbti": "INTJ", "competency_scores": {"communication": 4, "leadership": 3, "problem_solving": 5, "teamwork": 4}},
    ),
    (
        0, "Citra Lestari", "citra.lestari@example.com", "0813-1111-2222",
        """Citra Lestari
citra.lestari@example.com | 0813-1111-2222

Pendidikan
S1 Sistem Informasi, Universitas Bina Nusantara (2021-2024)

Pengalaman Kerja
Junior Backend Developer, Agensi Digital Cepat (2024-2025)

Keahlian
Python, Git, HTML, CSS""",
        None,
    ),
    (
        0, "Dedi Kurniawan", "dedi.kurniawan@example.com", "0814-3333-4444",
        """Dedi Kurniawan
dedi.kurniawan@example.com | 0814-3333-4444

Pendidikan
D3 Manajemen Informatika, Politeknik Negeri (2019-2022)

Pengalaman Kerja
Staff Administrasi, PT Sumber Makmur (2022-2025)

Keahlian
Microsoft Excel, Customer Service""",
        None,
    ),
    (
        1, "Sarah Wijaya", "sarah.wijaya@example.com", "0815-5555-6666",
        """Sarah Wijaya
sarah.wijaya@example.com | 0815-5555-6666

Pendidikan
S1 Manajemen Bisnis, Universitas Indonesia (2017-2021)

Pengalaman Kerja
Product Manager, FinTech Berkah (2021-2025)
Memimpin tim 5 engineer merilis fitur pembayaran untuk 200rb pengguna

Keahlian
Product Management, SQL, Figma, Agile, Data Analysis""",
        {"mbti": "ENFJ", "competency_scores": {"communication": 5, "leadership": 5, "problem_solving": 4, "teamwork": 5}},
    ),
    (
        1, "Rudi Hartawan", "rudi.hartawan@example.com", "0816-7777-8888",
        """Rudi Hartawan
rudi.hartawan@example.com | 0816-7777-8888

Pendidikan
S1 Teknik Industri, Institut Teknologi Sepuluh Nopember (2019-2023)

Pengalaman Kerja
Business Analyst, Retail Nusantara (2023-2025)

Keahlian
Excel, SQL, Presentasi""",
        {"mbti": "ISTJ", "competency_scores": {"communication": 3, "leadership": 2, "problem_solving": 3, "teamwork": 3}},
    ),
    # --- Junior Frontend (job idx 2) ---
    (
        2, "Farhan Nugroho", "farhan.nugroho@example.com", "0817-2222-3333",
        """Farhan Nugroho
farhan.nugroho@example.com | 0817-2222-3333

Pendidikan
S1 Ilmu Komputer, Universitas Gadjah Mada (2020-2024)

Pengalaman Kerja
Frontend Developer Intern, Digitalku Studio (2024-2025)
Membangun antarmuka web dengan React.js dan Next.js, styling dengan CSS modules
Asisten Praktikum Pemrograman Web, Fakultas Ilmu Komputer UGM (2023-2024)

Keahlian
TypeScript, React.js, Next.js, HTML, CSS, Git""",
        None,
    ),
    (
        2, "Maya Anindya", "maya.anindya@example.com", "0817-4444-5555",
        """Maya Anindya
maya.anindya@example.com | 0817-4444-5555

Pendidikan
S1 Sistem Informasi, Universitas Telkom (2021-2025)

Pengalaman Kerja
Peserta Bootcamp Web Development, Dicoding (2024)
Membuat beberapa proyek landing page menggunakan React.js dan HTML/CSS

Keahlian
React.js, HTML, CSS, JavaScript""",
        None,
    ),
    (
        2, "Bagas Setiawan", "bagas.setiawan@example.com", "0817-6666-7777",
        """Bagas Setiawan
bagas.setiawan@example.com | 0817-6666-7777

Pendidikan
S1 Desain Komunikasi Visual, Universitas Trisakti (2018-2022)

Pengalaman Kerja
Graphic Designer, Agensi Kreatif Warna (2022-2025)
Membuat materi desain promosi untuk media sosial klien

Keahlian
Adobe Photoshop, Adobe Illustrator, Canva""",
        None,
    ),
    # --- Data Analyst (job idx 3) ---
    (
        3, "Indah Permata", "indah.permata@example.com", "0818-1111-2222",
        """Indah Permata
indah.permata@example.com | 0818-1111-2222

Pendidikan
S1 Statistika, Institut Pertanian Bogor (2018-2022)

Pengalaman Kerja
Data Analyst, Marketplace Nusantara (2022-2025)
Membuat dashboard penjualan mingguan dengan SQL dan Tableau, analisis tren untuk tim marketing
Data Analyst Intern, Bank Digital Amanah (2021-2022)

Keahlian
SQL, Excel, Data Visualization, Python, Tableau""",
        {"mbti": "ISTP", "competency_scores": {"communication": 4, "leadership": 3, "problem_solving": 5, "teamwork": 4}},
    ),
    (
        3, "Yusuf Ramadhan", "yusuf.ramadhan@example.com", "0818-3333-4444",
        """Yusuf Ramadhan
yusuf.ramadhan@example.com | 0818-3333-4444

Pendidikan
S1 Manajemen, Universitas Padjadjaran (2019-2023)

Pengalaman Kerja
Staff Finance, PT Sumber Rejeki (2023-2025)
Menyusun laporan keuangan bulanan menggunakan Excel dan query SQL sederhana

Keahlian
Excel, SQL""",
        None,
    ),
    (
        3, "Wulan Kartika", "wulan.kartika@example.com", "0818-5555-6666",
        """Wulan Kartika
wulan.kartika@example.com | 0818-5555-6666

Pendidikan
D3 Akuntansi, Politeknik Negeri Jakarta (2020-2023)

Pengalaman Kerja
Staff Administrasi, Klinik Sehat Selalu (2023-2025)
Mengelola data pasien dan laporan administrasi harian menggunakan Excel

Keahlian
Microsoft Excel, Microsoft Word""",
        None,
    ),
    # --- UX Designer (job idx 4) ---
    (
        4, "Nadia Kusuma", "nadia.kusuma@example.com", "0819-1111-2222",
        """Nadia Kusuma
nadia.kusuma@example.com | 0819-1111-2222

Pendidikan
S1 Desain Komunikasi Visual, Institut Teknologi Bandung (2018-2022)

Pengalaman Kerja
UX Designer, Aplikasi Kesehatan Sehati (2022-2025)
Melakukan user research, membuat wireframe & prototype interaktif dengan Figma untuk fitur baru
UI Designer Intern, Startup Fintech Cepat (2021-2022)

Keahlian
Figma, UI Design, User Research, Prototyping, Wireframing""",
        {"mbti": "INFP", "competency_scores": {"communication": 5, "leadership": 3, "problem_solving": 4, "teamwork": 5}},
    ),
    (
        4, "Reza Pratama", "reza.pratama@example.com", "0819-3333-4444",
        """Reza Pratama
reza.pratama@example.com | 0819-3333-4444

Pendidikan
S1 Desain Produk, Universitas Multimedia Nusantara (2021-2025)

Pengalaman Kerja
Freelance UI Designer (2024-2025)
Mendesain tampilan aplikasi mobile sederhana menggunakan Figma untuk beberapa klien kecil

Keahlian
Figma, UI Design""",
        None,
    ),
    (
        4, "Dian Saputra", "dian.saputra@example.com", "0819-5555-6666",
        """Dian Saputra
dian.saputra@example.com | 0819-5555-6666

Pendidikan
S1 Manajemen Pemasaran, Universitas Airlangga (2019-2023)

Pengalaman Kerja
Sales Executive, PT Mitra Sejahtera (2023-2025)
Melakukan penjualan dan negosiasi dengan klien korporat

Keahlian
Negosiasi, Presentasi, Microsoft Office""",
        None,
    ),
]


async def main() -> None:
    db = SessionLocal()
    try:
        print("=== Users ===")
        for u in DEMO_USERS:
            if get_user_by_email(db, u["email"]) is not None:
                print(f"  skip (exists): {u['email']}")
                continue
            create_user(db, UserCreate(name=u["name"], email=u["email"], password=u["password"], role=u["role"]))
            print(f"  created: {u['email']} / {u['password']} ({u['role'].value})")

        admin = get_user_by_email(db, "nabilbiel12@gmail.com")
        if admin is None:
            print("\nNo admin found — run scripts/create_admin.py first.")
            return

        print("\n=== Jobs ===")
        job_ids = []
        for j in JOBS:
            existing = db.query(JobPosting).filter(JobPosting.title == j["title"]).first()
            if existing is not None:
                job_ids.append(existing.id)
                print(f"  skip (exists): {existing.title} ({existing.id})")
                continue
            job = jobs_service.create_job(db, JobPostingCreate(**j, status=JobStatus.active), created_by=admin.id)
            job_ids.append(job.id)
            print(f"  created: {job.title} ({job.id})")

        print("\n=== Candidates (real parse + real score) ===")
        for job_idx, name, email, phone, cv_text, assessment in CANDIDATES:
            job_id = job_ids[job_idx]

            existing_candidate = (
                db.query(Candidate)
                .filter(Candidate.job_posting_id == job_id, Candidate.email == email)
                .first()
            )
            if existing_candidate is not None:
                print(f"  skip (exists): {name} -> {JOBS[job_idx]['title']}")
                continue

            cv_bytes = _pdf_from_text(cv_text)
            upload = _FakeUploadFile("cv.pdf", cv_bytes, "application/pdf")

            candidate, _dup = await candidates_service.create_candidate(
                db,
                job_posting_id=job_id,
                full_name=name,
                email=email,
                phone=phone,
                cv_file=upload,
                certificate_files=[],
                assessment_input=assessment,
            )

            profile = parse_resume(cv_bytes, "cv.pdf")
            candidates_service.apply_parsed_profile(db, candidate.id, profile)

            score = compute_and_save_score(db, candidate.id)
            print(f"  {name} -> {JOBS[job_idx]['title']}: {float(score.final_score):.1f} ({score.label.value})")

        print("\nDone. Login as any seeded user (passwords above) or the existing admin account.")
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
