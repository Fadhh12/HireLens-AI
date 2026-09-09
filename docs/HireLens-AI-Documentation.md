# HireLens AI — Full Product & Engineering Documentation

**Versi:** 1.0
**Dibuat oleh:** Nabil Fadhlur Rahman (Bil)

Dokumen ini merangkum seluruh dokumentasi pra-pengembangan HireLens AI: PRD, SRS, SDD, UI/UX Flow, dan Task Breakdown, dalam satu file agar mudah dibagikan atau dilampirkan ke portofolio/GitHub.

## Daftar Isi
1. [Product Requirements Document (PRD)](#product-requirements-document-prd)
2. [Software Requirements Specification (SRS)](#software-requirements-specification-srs)
3. [System Design Document (SDD)](#system-design-document-sdd)
4. [UI/UX Flow & Design System](#uiux-flow--design-system)
5. [Task Breakdown](#task-breakdown)

---

## Product Requirements Document (PRD)


**Versi:** 1.0
**Status:** Draft untuk pengembangan portofolio
**Dibuat oleh:** Nabil Fadhlur Rahman (Bil)
**Konteks:** Proyek independen yang terinspirasi dari domain masalah rekrutmen berbasis AI (candidate screening, job matching, interview assistance). Seluruh nama produk, branding, skema data, dan spesifikasi teknis pada dokumen ini adalah original dan tidak berasal dari materi milik perusahaan/organisasi manapun.

---

## 1. Latar Belakang

Proses rekrutmen konvensional menghadapi beberapa masalah nyata:

| Masalah | Dampak |
|---|---|
| Volume lamaran tinggi | Recruiter kewalahan menyaring CV secara manual |
| Review CV & sertifikat memakan waktu | Cycle time rekrutmen memanjang |
| Evaluasi kandidat subjektif | Keputusan hiring tidak konsisten antar recruiter |
| Sulit mencocokkan kandidat dengan kebutuhan role | Mismatch antara kandidat dan posisi |
| Tidak ada standar wawancara | Kualitas interview bervariasi tergantung interviewer |

**HireLens AI** dirancang sebagai platform yang membantu tim HR/recruiter melakukan screening, scoring, ranking, dan persiapan interview kandidat secara terstruktur dan berbasis data — bukan menggantikan keputusan manusia, tapi mempercepat dan menstandarkan proses sebelum keputusan akhir diambil recruiter.

---

## 2. Tujuan Produk

### 2.1 Tujuan Utama
1. Mengotomatisasi ekstraksi & analisis data kandidat (CV, sertifikat, hasil asesmen).
2. Mencocokkan kandidat terhadap job description & kebutuhan role secara terukur (scoring, bukan tebakan).
3. Memberi recruiter dashboard ranking kandidat yang jelas dan bisa diaudit (ada alasan di balik skor).
4. Membantu interviewer mempersiapkan pertanyaan wawancara yang relevan berdasarkan gap/kekuatan kandidat.

### 2.2 Tujuan sebagai Portofolio
- Menunjukkan kemampuan end-to-end product thinking: dari masalah bisnis → requirement → arsitektur → UI/UX → eksekusi.
- Menunjukkan penguasaan stack full-stack + AI/LLM integration (bukan sekadar CRUD app).
- Studi kasus yang relevan untuk role Software Engineer / AI Engineer / Product-minded Developer.

### 2.3 Non-Goals (di luar scope MVP)
- Tidak menggantikan keputusan akhir hiring (human-in-the-loop tetap wajib).
- Tidak melakukan background check / verifikasi identitas kandidat.
- Tidak menangani payroll, onboarding, atau HRIS penuh.
- Tidak mendukung multi-tenant SaaS penuh di MVP (cukup single-organization).

---

## 3. Target Pengguna (User & Persona)

### Persona 1 — Recruiter / HR Screener ("Sarah")
- Menerima puluhan–ratusan lamaran per posisi.
- Butuh cara cepat menyaring kandidat yang layak lanjut ke tahap berikutnya.
- Tidak terlalu teknis, butuh dashboard yang jelas, bukan data mentah.

### Persona 2 — Hiring Manager ("Dimas")
- Menentukan requirement teknis/kompetensi untuk suatu role.
- Ingin melihat ranking kandidat beserta alasan skor (transparansi), bukan cuma angka.
- Terlibat di keputusan final hire/consider/reject.

### Persona 3 — Interviewer ("Rani")
- Membutuhkan bahan pertanyaan wawancara yang spesifik ke tiap kandidat (bukan template generik).
- Ingin tahu area yang perlu digali lebih dalam (gap/risk area).

### Persona 4 — Admin Sistem
- Mengatur job posting, kriteria scoring, dan role-based access.

---

## 4. Fitur Produk (MVP Scope)

Menggunakan prioritas **MoSCoW**.

### Must Have
1. **Job Posting Management** — Admin/HR membuat job description + kriteria kompetensi (skill, experience level, values fit).
2. **Candidate Intake** — Upload CV (PDF/DOCX) + sertifikat + hasil asesmen (form input manual untuk MVP, bukan integrasi psikotes eksternal).
3. **Resume Parsing Engine** — Ekstraksi otomatis: data diri, riwayat pendidikan, pengalaman kerja, skill, sertifikasi.
4. **AI Matching Engine** — Menghitung skor kecocokan kandidat vs job requirement (skill match, experience match, overall fit).
5. **Candidate Ranking Dashboard** — Daftar kandidat per job, terurut berdasarkan skor, dengan breakdown alasan skor.
6. **Candidate Detail View** — Ringkasan AI (summary), skill yang terdeteksi, gap yang ditemukan.
7. **AI Interview Question Generator** — Generate pertanyaan wawancara (teknikal + behavioral) berbasis profil kandidat & gap yang ditemukan.
8. **Recommendation Status** — Sistem memberi label *Strong Match / Consider / Not a Fit* (bukan keputusan final, tetap bisa di-override recruiter).
9. **Auth & Role-based Access** — Admin, Recruiter, Interviewer punya akses berbeda.

### Should Have
10. **Candidate Comparison View** — Bandingkan 2–3 kandidat berdampingan.
11. **Export Report** — Export ringkasan kandidat ke PDF untuk dibagikan ke hiring manager.
12. **Activity Log** — Riwayat siapa mengubah status kandidat & kapan.

### Could Have
13. **Bulk Upload CV** (multiple candidates sekaligus, batch processing).
14. **Notes & Collaboration** — Recruiter bisa memberi catatan internal per kandidat.

### Won't Have (MVP ini)
- Video interview recording/analysis.
- Integrasi job board eksternal (LinkedIn, Jobstreet, dll).
- Payroll/HRIS.

---

## 5. Alur Pengguna Utama (High-Level Flow)

### Flow A — HR Membuat Lowongan & Kriteria
```
Login (HR) → Buat Job Posting → Isi Job Description
→ Definisikan kriteria scoring (skill wajib, skill nice-to-have, min. experience, values)
→ Publish job (internal) → Job siap menerima kandidat
```

### Flow B — Intake & Analisis Kandidat
```
HR pilih Job → Upload CV kandidat (+ sertifikat, hasil asesmen opsional)
→ Sistem parsing dokumen (OCR/NLP) → Sistem menjalankan AI Matching Engine
→ Kandidat masuk ke Ranking Dashboard dengan skor & label
```

### Flow C — Review & Shortlist
```
HR/Hiring Manager buka Ranking Dashboard
→ Lihat daftar kandidat terurut skor → Klik kandidat untuk detail
→ Lihat breakdown skor (skill fit, experience fit, values fit) + ringkasan AI
→ Ubah status kandidat (Shortlist / Reject / Hold)
```

### Flow D — Persiapan Interview
```
Interviewer buka kandidat yang sudah Shortlist
→ Klik "Generate Interview Questions"
→ Sistem menghasilkan: pertanyaan teknikal, pertanyaan behavioral, area yang perlu digali
→ Interviewer bisa edit/tambah pertanyaan manual sebelum sesi wawancara
```

### Flow E — Keputusan Akhir
```
Setelah interview → Hiring Manager update status akhir (Hire/Reject)
→ Sistem mencatat outcome (untuk keperluan riwayat, bukan re-training model di MVP)
```

---

## 6. Metrik Keberhasilan (Success Metrics)

| Metrik | Target Indikatif |
|---|---|
| Waktu screening per kandidat | Berkurang signifikan dibanding manual review |
| Akurasi parsing data CV (field terekstrak dengan benar) | ≥ 85% pada dataset uji |
| Recruiter dapat memahami alasan skor tanpa penjelasan tambahan | Ya (diukur via usability testing sederhana) |
| Waktu dari upload CV → kandidat muncul di ranking | < 30 detik per kandidat (MVP, single upload) |

---

## 7. Asumsi & Batasan
- Dataset psikotes/MBTI diinput manual (bukan integrasi API pihak ketiga) untuk MVP.
- Bahasa dokumen kandidat: Bahasa Indonesia & Inggris.
- Skala data MVP: ratusan kandidat per job, bukan jutaan (tidak perlu big-data infra).
- LLM digunakan untuk *ekstraksi terbantu* dan *generation* (summary, interview question), bukan sebagai satu-satunya sumber kebenaran skor — skor akhir tetap kombinasi rule-based scoring + LLM assist agar bisa diaudit.
-e 

---

## Software Requirements Specification (SRS)


**Versi:** 1.0
**Referensi:** Diturunkan dari 01-PRD.md

---

## 1. Ruang Lingkup
Dokumen ini merinci requirement fungsional, aturan validasi, business rules, dan requirement non-fungsional untuk MVP HireLens AI.

---

## 2. Aktor & Role

| Role | Hak Akses |
|---|---|
| **Admin** | Full access: kelola user, kelola job, kelola kriteria scoring, lihat semua data |
| **Recruiter/HR** | Buat job, upload kandidat, lihat ranking, ubah status kandidat, generate report |
| **Hiring Manager** | Lihat ranking & detail kandidat (read-mostly), ubah status shortlist/hire/reject, beri catatan |
| **Interviewer** | Lihat kandidat yang di-assign, generate & edit pertanyaan interview, isi hasil interview |

---

## 3. Functional Requirements (FR)

### FR-1 Modul Autentikasi
- **FR-1.1** Sistem harus mendukung login via email + password.
- **FR-1.2** Password disimpan dalam bentuk hash (bcrypt/argon2), tidak pernah plaintext.
- **FR-1.3** Sistem harus mendukung session/JWT dengan masa berlaku token (access token 15–60 menit, refresh token 7 hari).
- **FR-1.4** Setelah 5 kali gagal login berturut-turut, akun dikunci sementara (15 menit) — mitigasi brute force.
- **FR-1.5** Role pengguna ditentukan saat akun dibuat oleh Admin; user tidak bisa self-register sebagai Admin.

### FR-2 Modul Job Posting
- **FR-2.1** HR/Admin dapat membuat job posting dengan field: judul, department, deskripsi, skill wajib (list), skill nice-to-have (list), min. tahun pengalaman, level (junior/mid/senior), status (draft/active/closed).
- **FR-2.2** Setiap job posting harus memiliki minimal 1 skill wajib sebelum bisa berstatus "active".
- **FR-2.3** HR dapat mendefinisikan bobot scoring per kategori (skill fit, experience fit, values fit) — total bobot harus = 100%.
- **FR-2.4** Job posting berstatus "closed" tidak dapat lagi menerima kandidat baru, tapi data kandidat lama tetap dapat diakses (read-only untuk relasi job tsb).

### FR-3 Modul Candidate Intake
- **FR-3.1** Sistem harus menerima upload CV dalam format PDF dan DOCX, ukuran maksimum 5MB per file.
- **FR-3.2** Sistem harus menerima upload sertifikat (PDF/JPG/PNG), maksimum 5 file per kandidat, masing-masing maksimum 5MB.
- **FR-3.3** Sistem harus menyediakan form input manual untuk hasil asesmen/psikotes (mis. tipe MBTI, skor kompetensi 1–5 per kategori) karena tidak ada integrasi API psikotes eksternal di MVP.
- **FR-3.4** Field wajib saat intake kandidat: nama, email, nomor telepon, job posting tujuan, file CV.
- **FR-3.5** Jika parsing CV gagal total (file corrupt/tidak terbaca), sistem harus tetap menyimpan kandidat dengan status "Needs Manual Review", bukan menolak data.

### FR-4 Modul Resume Parsing Engine
- **FR-4.1** Sistem harus mengekstraksi minimal: nama, email, no. telepon, riwayat pendidikan, riwayat pekerjaan, daftar skill, sertifikasi.
- **FR-4.2** Hasil ekstraksi harus disimpan sebagai data terstruktur (bukan hanya teks mentah) agar bisa digunakan Matching Engine.
- **FR-4.3** Recruiter harus bisa mengedit/mengoreksi hasil ekstraksi otomatis secara manual (karena OCR/NLP tidak akan 100% akurat).
- **FR-4.4** Sistem mencatat *confidence indicator* sederhana per field hasil ekstraksi (mis. "terverifikasi" vs "perlu dicek") — bukan skor probabilistik yang rumit, cukup flag biner untuk MVP.

### FR-5 Modul AI Matching Engine
- **FR-5.1** Sistem menghitung skor kecocokan kandidat terhadap job dengan komponen minimal:
  - Skill Fit (persentase overlap antara skill kandidat vs skill wajib+nice-to-have job, dengan bobot berbeda untuk wajib vs nice-to-have)
  - Experience Fit (perbandingan tahun pengalaman & relevansi role sebelumnya)
  - Values/Behavioral Fit (berdasarkan input asesmen manual, jika tersedia)
- **FR-5.2** Skor akhir = kombinasi berbobot dari ketiga komponen di atas sesuai bobot yang ditentukan HR di job posting (lihat FR-2.3).
- **FR-5.3** Setiap skor akhir harus disertai *breakdown* yang bisa ditampilkan ke user (transparansi/explainability) — tidak boleh berupa angka tanpa penjelasan.
- **FR-5.4** Sistem memetakan skor akhir ke label kualitatif:
  - ≥ 80 → **Strong Match**
  - 60–79 → **Consider**
  - < 60 → **Not a Fit**
  (Threshold dapat dikonfigurasi Admin, nilai di atas adalah default.)
- **FR-5.5** LLM (Generative AI) boleh digunakan untuk membantu penilaian values/behavioral fit dan meringkas profil kandidat, tetapi skor numerik akhir tetap harus melalui perhitungan rule-based yang dapat diaudit (LLM tidak boleh jadi kotak hitam satu-satunya sumber skor).

### FR-6 Modul Ranking Dashboard
- **FR-6.1** Dashboard menampilkan daftar kandidat per job, default terurut skor tertinggi → terendah.
- **FR-6.2** Dashboard mendukung filter: label (Strong Match/Consider/Not a Fit), status (New/Shortlisted/Interviewed/Hired/Rejected), rentang skor.
- **FR-6.3** Dashboard mendukung pencarian nama kandidat.
- **FR-6.4** Setiap baris kandidat menampilkan minimal: nama, skor total, label, status saat ini, tanggal apply.

### FR-7 Modul Candidate Detail
- **FR-7.1** Halaman detail menampilkan: data diri, ringkasan AI (2–4 kalimat), breakdown skor per kategori, skill terdeteksi, riwayat pengalaman, sertifikasi, hasil asesmen (jika ada).
- **FR-7.2** Recruiter/Hiring Manager dapat mengubah status kandidat dari halaman ini (New → Shortlisted → Interviewed → Hired/Rejected).
- **FR-7.3** Perubahan status harus tercatat di activity log (siapa, kapan, status lama → status baru).

### FR-8 Modul AI Interview Question Generator
- **FR-8.1** Sistem dapat menghasilkan minimal: 3 pertanyaan teknikal, 3 pertanyaan behavioral, dan daftar "area yang perlu digali/divalidasi" berdasarkan gap antara profil kandidat dan requirement job.
- **FR-8.2** Interviewer dapat mengedit, menghapus, atau menambah pertanyaan sebelum sesi interview disimpan sebagai "final interview guide" kandidat tsb.
- **FR-8.3** Generate ulang pertanyaan tidak menghapus riwayat versi sebelumnya (disimpan sebagai draft baru).

### FR-9 Modul Report Export
- **FR-9.1** Sistem dapat mengekspor ringkasan kandidat (profil + skor + status) ke PDF.
- **FR-9.2** PDF harus mencantumkan disclaimer bahwa hasil AI adalah alat bantu, bukan keputusan final.

---

## 4. Validasi & Aturan Data

| Field | Aturan Validasi |
|---|---|
| Email kandidat/user | Format email valid, unik per tabel (tidak boleh duplikat di kandidat yang sama untuk job yang sama) |
| No. telepon | Hanya angka, +, spasi, tanda hubung; panjang 8–15 digit |
| File CV | Tipe: `.pdf`, `.docx`; maks 5MB; wajib ada |
| File sertifikat | Tipe: `.pdf`, `.jpg`, `.jpeg`, `.png`; maks 5MB per file; maks 5 file |
| Bobot scoring job (FR-2.3) | Jumlah 3 komponen bobot harus tepat 100%, masing-masing ≥ 0% |
| Skor kandidat | Rentang 0–100, dibulatkan 1 desimal |
| Password | Minimal 8 karakter, kombinasi huruf & angka |
| Status job posting | Enum tetap: `draft`, `active`, `closed` — tidak boleh nilai bebas |
| Status kandidat | Enum tetap: `new`, `screening`, `shortlisted`, `interviewed`, `hired`, `rejected`, `needs_manual_review` |

---

## 5. Business Rules

- **BR-1** Kandidat tidak bisa berpindah status mundur secara otomatis oleh sistem (mis. dari `hired` kembali ke `new`) — hanya perubahan manual oleh Recruiter/Admin dengan alasan wajib diisi.
- **BR-2** Job posting dengan status `closed` tidak dapat diedit kriteria scoring-nya (mencegah inkonsistensi historis skor kandidat lama).
- **BR-3** Recruiter hanya dapat melihat & mengelola kandidat pada job yang mereka miliki akses (jika ke depan ada multi-tim; MVP: semua recruiter internal dapat lihat semua job).
- **BR-4** Interviewer hanya dapat men-generate pertanyaan untuk kandidat berstatus `shortlisted` atau setelahnya.
- **BR-5** Setiap pemanggilan AI Matching Engine dicatat (audit trail): input yang digunakan, output skor, timestamp, versi model/prompt yang dipakai — untuk keperluan explainability & debugging.
- **BR-6** Jika hasil asesmen manual tidak diisi, komponen Values/Behavioral Fit diberi bobot 0 dan bobot dialihkan proporsional ke Skill Fit & Experience Fit (sistem tidak boleh gagal total hanya karena satu komponen kosong).

---

## 6. Non-Functional Requirements (NFR)

| Kategori | Requirement |
|---|---|
| **Performa** | Proses parsing + scoring 1 kandidat selesai < 30 detik (async, non-blocking UI) |
| **Skalabilitas** | Mendukung minimal 500 kandidat aktif & 50 job posting tanpa degradasi signifikan (skala portofolio/demo) |
| **Keamanan** | Data kandidat (PII) dienkripsi at-rest untuk field sensitif (email, no. telp); komunikasi via HTTPS |
| **Ketersediaan** | Target uptime 99% untuk demo/portofolio (bukan SLA enterprise) |
| **Auditability** | Semua perubahan status & hasil AI scoring harus tertelusuri (siapa/kapan/apa) |
| **Usability** | Recruiter non-teknis harus bisa memahami dashboard tanpa training — skor harus disertai penjelasan bahasa natural |
| **Portabilitas** | Backend menggunakan environment terisolasi (Python venv) dan koneksi database via connection string standar (`DATABASE_URL`), sehingga mudah dipindah antar environment (lokal, Railway/Render, Supabase) tanpa containerization |
| **Localization** | UI mendukung Bahasa Indonesia sebagai default; struktur data siap untuk multi-bahasa ke depannya |

---

## 7. Error Handling & Edge Cases

- CV berhasil diupload tapi gagal diparsing → status `needs_manual_review`, notifikasi ke recruiter.
- Upload file melebihi ukuran/format salah → ditolak di sisi client & server dengan pesan error jelas (bukan generic "error 500").
- AI Matching Engine timeout/gagal (mis. LLM API down) → sistem tetap menghitung skor rule-based (skill & experience fit) dan menandai komponen values fit sebagai "pending", bukan gagal total.
- Duplikasi kandidat (email sama pada job sama) → sistem memberi peringatan, bukan otomatis menolak (bisa jadi re-apply yang sah).
-e 

---

## System Design Document (SDD)


**Versi:** 1.0
**Referensi:** 01-PRD.md, 02-SRS.md

---

## 1. Arsitektur Sistem (High-Level)

Pola arsitektur: **Modular Monolith** (bukan microservices) — cocok untuk skala portofolio/MVP, lebih mudah dikembangkan solo, tapi tetap dipisah per domain module agar bisa dipecah jadi service terpisah di masa depan jika perlu.

```
┌──────────────────────────────────────────────────────────────────┐
│                         CLIENT (Browser)                         │
│              Next.js 15 (React 19 + TypeScript)                  │
│        Dashboard Recruiter | Job Management | Candidate View     │
└───────────────────────────┬────────────────────────────────────-─┘
                             │ HTTPS (REST, JWT Bearer)
┌───────────────────────────▼───────────────────────────────────-──┐
│                        API GATEWAY LAYER                         │
│                     FastAPI (Python 3.11+)                       │
│   Auth Middleware → Rate Limiting → Request Validation (Pydantic)│
└───────────┬───────────────┬───────────────┬───────────────────-──┘
            │               │               │
   ┌────────▼──────┐ ┌──────▼───────┐ ┌─────▼────────────┐
   │  Core Service │ │ Document AI  │ │ Matching Engine   │
   │  (Job, User,  │ │  Service     │ │ Service           │
   │  Candidate     │ │ (OCR + NLP   │ │ (Scoring +        │
   │  CRUD, Auth)   │ │  parsing)    │ │  LLM assist)       │
   └────────┬──────┘ └──────┬───────┘ └─────┬────────────┘
            │               │               │
            └───────┬───────┴───────┬───────┘
                     │               │
            ┌────────▼──────┐ ┌──────▼───────────┐
            │  Supabase     │ │  Supabase Storage  │
            │  PostgreSQL   │ │  (CV, sertifikat)   │
            │  (data utama) │ │                     │
            └───────────────┘ └────────────────────┘
                     │
            ┌────────▼──────────────┐
            │  Background Worker     │
            │  (Celery/RQ + Redis)   │
            │  — parsing & scoring   │
            │    dijalankan async    │
            └────────┬───────────────┘
                     │
            ┌────────▼──────────────┐
            │  External AI Provider  │
            │  (LLM API — mis.       │
            │   Gemini/OpenAI API)   │
            │  untuk: summary,       │
            │  values-fit assist,    │
            │  interview question    │
            │  generation            │
            └────────────────────────┘
```

### 1.1 Alasan Desain
- **Async processing (Celery/RQ + Redis)**: parsing CV & pemanggilan LLM butuh waktu (bisa 5–20 detik) → tidak boleh blocking request HTTP utama. User upload → dapat response instan "processing" → dashboard update via polling/websocket saat selesai.
- **Pemisahan Matching Engine dari Document AI Service**: scoring rule-based harus deterministik & bisa diaudit, sedangkan parsing dokumen lebih banyak "best-effort". Memisahkan keduanya memudahkan testing & debugging independen.
- **Object Storage terpisah dari DB**: file CV/sertifikat tidak disimpan sebagai BLOB di PostgreSQL (buruk untuk performa) — cukup simpan path referensinya (Supabase Storage object path) di DB.

---

## 2. Tech Stack

| Layer | Teknologi | Alasan |
|---|---|---|
| Frontend | Next.js 15, React 19, TypeScript, TailwindCSS, Shadcn UI | Familiar, cepat untuk build UI kompleks (dashboard, tabel, form) dengan konsistensi desain |
| Backend API | FastAPI (Python) | Async native, cocok untuk I/O-bound task (LLM call, file processing), auto-docs via OpenAPI |
| Background Job | Celery + Redis (atau RQ untuk versi lebih ringan) | Memisahkan proses berat (parsing, LLM call) dari request-response cycle |
| Database | PostgreSQL | Relasional kuat untuk data job-candidate-scoring yang saling terkait, mendukung JSONB untuk data semi-terstruktur (hasil parsing mentah) |
| Object Storage | **Supabase Storage** (satu platform dengan database — tidak perlu setup layanan storage terpisah) | Menyimpan file CV/sertifikat secara efisien & terpisah dari tabel DB, langsung terintegrasi dengan project Supabase yang sama |
| Resume Parsing | PyMuPDF/pdfplumber (ekstraksi teks) + spaCy/regex (NLP entity extraction) | Kombinasi ekstraksi teks + parsing entitas terstruktur (nama, skill, dsb) |
| Generative AI | LLM API (Gemini API / OpenAI API via LangChain) | Untuk ringkasan kandidat, penilaian values-fit kualitatif, dan generate pertanyaan interview |
| Auth | JWT (access + refresh token) via FastAPI + passlib (bcrypt) | Standar, stateless, mudah diaudit |
| Deployment | Tanpa Docker — jalankan backend langsung via Python venv (`uvicorn`), database pakai PostgreSQL lokal (development) atau **Supabase** (development & production, karena sudah termasuk hosted Postgres + storage + auth-ready) | Setup lebih ringan untuk dikerjakan solo, tanpa overhead containerization |

---

## 3. Skema Database (Entity-Relationship)

### 3.1 Tabel Utama

**`users`**
| Kolom | Tipe | Keterangan |
|---|---|---|
| id | UUID (PK) | |
| name | VARCHAR | |
| email | VARCHAR (unique) | |
| password_hash | VARCHAR | |
| role | ENUM(admin, recruiter, hiring_manager, interviewer) | |
| created_at | TIMESTAMP | |

**`job_postings`**
| Kolom | Tipe | Keterangan |
|---|---|---|
| id | UUID (PK) | |
| title | VARCHAR | |
| department | VARCHAR | |
| description | TEXT | |
| required_skills | JSONB | list of skill string |
| nice_to_have_skills | JSONB | |
| min_experience_years | INT | |
| level | ENUM(junior, mid, senior) | |
| weight_skill_fit | DECIMAL(5,2) | default 50.00 |
| weight_experience_fit | DECIMAL(5,2) | default 30.00 |
| weight_values_fit | DECIMAL(5,2) | default 20.00 |
| status | ENUM(draft, active, closed) | |
| created_by | UUID (FK → users.id) | |
| created_at | TIMESTAMP | |

**`candidates`**
| Kolom | Tipe | Keterangan |
|---|---|---|
| id | UUID (PK) | |
| job_posting_id | UUID (FK → job_postings.id) | |
| full_name | VARCHAR | |
| email | VARCHAR | |
| phone | VARCHAR | |
| cv_file_url | VARCHAR | referensi ke object storage |
| certificate_urls | JSONB | array URL |
| parsed_profile | JSONB | hasil ekstraksi terstruktur (education, experience, skills) |
| assessment_input | JSONB | input manual MBTI/skor kompetensi |
| status | ENUM(new, screening, shortlisted, interviewed, hired, rejected, needs_manual_review) | |
| applied_at | TIMESTAMP | |

**`candidate_scores`**
| Kolom | Tipe | Keterangan |
|---|---|---|
| id | UUID (PK) | |
| candidate_id | UUID (FK) | |
| skill_fit_score | DECIMAL(5,2) | |
| experience_fit_score | DECIMAL(5,2) | |
| values_fit_score | DECIMAL(5,2) | nullable jika assessment kosong |
| final_score | DECIMAL(5,2) | |
| label | ENUM(strong_match, consider, not_a_fit) | |
| score_breakdown | JSONB | detail perhitungan (untuk explainability) |
| model_version | VARCHAR | versi prompt/model yang dipakai — audit trail |
| computed_at | TIMESTAMP | |

**`interview_guides`**
| Kolom | Tipe | Keterangan |
|---|---|---|
| id | UUID (PK) | |
| candidate_id | UUID (FK) | |
| technical_questions | JSONB | |
| behavioral_questions | JSONB | |
| risk_areas | JSONB | area yang perlu digali |
| version | INT | mendukung riwayat generate ulang |
| created_by | UUID (FK → users.id) | |
| created_at | TIMESTAMP | |

**`activity_logs`**
| Kolom | Tipe | Keterangan |
|---|---|---|
| id | UUID (PK) | |
| candidate_id | UUID (FK, nullable) | |
| actor_id | UUID (FK → users.id) | |
| action | VARCHAR | mis. "status_changed", "score_computed" |
| old_value | VARCHAR (nullable) | |
| new_value | VARCHAR (nullable) | |
| created_at | TIMESTAMP | |

### 3.2 Relasi
```
users (1) ───< (N) job_postings
job_postings (1) ───< (N) candidates
candidates (1) ───< (N) candidate_scores   (histori tiap kali dihitung ulang)
candidates (1) ───< (N) interview_guides   (histori tiap generate)
candidates (1) ───< (N) activity_logs
```

---

## 4. API Design (REST)

Base URL: `/api/v1`

### Auth
| Method | Endpoint | Deskripsi |
|---|---|---|
| POST | `/auth/login` | Login, return access + refresh token |
| POST | `/auth/refresh` | Refresh access token |
| POST | `/auth/logout` | Invalidate refresh token |

### Job Postings
| Method | Endpoint | Deskripsi |
|---|---|---|
| GET | `/jobs` | List job posting (filter: status) |
| POST | `/jobs` | Buat job baru (Admin/Recruiter) |
| GET | `/jobs/{job_id}` | Detail job |
| PATCH | `/jobs/{job_id}` | Update job (blocked jika status closed, sesuai BR-2) |
| POST | `/jobs/{job_id}/close` | Tutup job posting |

### Candidates
| Method | Endpoint | Deskripsi |
|---|---|---|
| POST | `/jobs/{job_id}/candidates` | Upload kandidat baru (multipart: CV, sertifikat, data form) |
| GET | `/jobs/{job_id}/candidates` | List kandidat per job (dengan filter & sort skor) |
| GET | `/candidates/{candidate_id}` | Detail kandidat + skor + parsed profile |
| PATCH | `/candidates/{candidate_id}` | Edit hasil parsing manual (koreksi recruiter) |
| PATCH | `/candidates/{candidate_id}/status` | Ubah status kandidat (wajib field `reason` sesuai BR-1) |

### Scoring
| Method | Endpoint | Deskripsi |
|---|---|---|
| POST | `/candidates/{candidate_id}/score` | Trigger ulang perhitungan skor (async job) |
| GET | `/candidates/{candidate_id}/score` | Ambil skor terakhir + breakdown |

### Interview
| Method | Endpoint | Deskripsi |
|---|---|---|
| POST | `/candidates/{candidate_id}/interview-guide` | Generate pertanyaan interview (async) |
| GET | `/candidates/{candidate_id}/interview-guide` | Ambil interview guide terbaru (+ versi sebelumnya) |
| PATCH | `/interview-guide/{guide_id}` | Edit pertanyaan sebelum finalisasi |

### Report
| Method | Endpoint | Deskripsi |
|---|---|---|
| GET | `/candidates/{candidate_id}/report/pdf` | Export ringkasan kandidat sebagai PDF |

### Contoh Response — Detail Skor Kandidat
```json
{
  "candidate_id": "c-001",
  "final_score": 78.5,
  "label": "consider",
  "score_breakdown": {
    "skill_fit": {
      "score": 82,
      "weight": 50,
      "matched_required": ["Python", "SQL"],
      "missing_required": ["Docker"],
      "matched_nice_to_have": ["FastAPI"]
    },
    "experience_fit": {
      "score": 70,
      "weight": 30,
      "candidate_years": 1.5,
      "required_years": 2
    },
    "values_fit": {
      "score": 80,
      "weight": 20,
      "note": "Skor berdasarkan input asesmen manual"
    }
  },
  "model_version": "matching-engine-v1.0"
}
```

---

## 5. Struktur Backend (Folder Structure)

```
backend/
├── app/
│   ├── main.py                  # entrypoint FastAPI
│   ├── core/
│   │   ├── config.py             # env config
│   │   ├── security.py           # JWT, hashing
│   │   └── dependencies.py       # auth dependency, role guard
│   ├── modules/
│   │   ├── auth/
│   │   │   ├── router.py
│   │   │   ├── schema.py
│   │   │   └── service.py
│   │   ├── jobs/
│   │   │   ├── router.py
│   │   │   ├── schema.py
│   │   │   ├── model.py
│   │   │   └── service.py
│   │   ├── candidates/
│   │   │   ├── router.py
│   │   │   ├── schema.py
│   │   │   ├── model.py
│   │   │   └── service.py
│   │   ├── document_ai/
│   │   │   ├── parser.py         # OCR + NLP extraction
│   │   │   └── service.py
│   │   ├── matching_engine/
│   │   │   ├── scoring.py        # rule-based scoring logic
│   │   │   ├── llm_assist.py     # pemanggilan LLM utk values-fit & summary
│   │   │   └── service.py
│   │   └── interview/
│   │       ├── router.py
│   │       ├── question_generator.py
│   │       └── service.py
│   ├── workers/
│   │   ├── celery_app.py
│   │   ├── tasks_parsing.py
│   │   └── tasks_scoring.py
│   └── db/
│       ├── base.py
│       ├── session.py
│       └── migrations/           # Alembic
├── tests/
├── requirements.txt
└── .env.example              # DATABASE_URL, SUPABASE_URL, JWT_SECRET, LLM_API_KEY, dll
```

---

## 6. Keamanan & Privasi Data
- Data kandidat (PII) diperlakukan sensitif: enkripsi field email/telepon at-rest, akses API dibatasi role-based (sesuai SRS §2).
- File CV/sertifikat disimpan di **Supabase Storage bucket privat** (bukan publicly accessible URL) — akses via signed URL berbatas waktu (Supabase mendukung ini secara native lewat `createSignedUrl`).
- Log audit (activity_logs) tidak menyimpan isi dokumen, hanya metadata perubahan.
- LLM API call tidak mengirim data lebih dari yang diperlukan (mis. tidak mengirim seluruh file mentah, cukup teks hasil parsing yang relevan).
-e 

---

## UI/UX Flow & Design System


**Versi:** 1.0
**Referensi:** 01-PRD.md, 02-SRS.md, 03-SDD.md

Preview arah desain (Ranking Dashboard) sudah ditampilkan di chat sebagai referensi tata letak & warna. Dokumen ini merinci seluruh sistem desain dan alur layar agar developer tidak perlu menebak.

---

## 1. Prinsip Desain

HireLens AI adalah **tool kerja untuk recruiter**, bukan produk konsumen. Prinsip:

1. **Trust over trend** — hindari estetika "generic AI SaaS" (gradient ungu-biru, ikon robot, glow neon). Gunakan palet hangat dan serius yang terasa seperti tool profesional (mirip Linear/Notion untuk HR), bukan demo AI generik.
2. **Explainability first** — setiap angka/skor yang tampil harus punya cara untuk "diklik lebih dalam" dan lihat alasannya. Tidak ada angka tanpa konteks.
3. **Scan-ability** — recruiter melihat puluhan kandidat sekaligus; layout harus dioptimalkan untuk table/list scanning, bukan card besar-besar yang boros scroll.
4. **Low cognitive load** — warna status maksimal 3 kategori (Strong Match/Consider/Not a Fit), tidak lebih.

---

## 2. Design System

### 2.1 Palet Warna

Konsep: **"Ink & Amber"** — dasar netral gelap-hangat (bukan biru dingin generic-AI) dipadukan aksen teal untuk kepercayaan dan amber untuk kehangatan manusia (karena ini tool tentang manusia, bukan hanya angka).

| Token | Hex | Penggunaan |
|---|---|---|
| `--color-bg-page` | `#F8F7F4` | Latar halaman utama (warm off-white, bukan putih steril) |
| `--color-surface` | `#FFFFFF` | Card, table, panel |
| `--color-border` | `#E7E3DC` | Border tipis antar elemen |
| `--color-ink-900` | `#1C1F26` | Teks utama (near-black, bukan pure black) |
| `--color-ink-600` | `#5B5F6B` | Teks sekunder/deskripsi |
| `--color-ink-400` | `#9195A0` | Placeholder, teks tersier |
| `--color-primary-700` | `#0E4F4A` | Brand utama — deep teal (tombol utama, link aktif, sidebar aktif) |
| `--color-primary-100` | `#DCEEEC` | Background elemen ber-aksen primary (badge terpilih, hover) |
| `--color-accent-600` | `#C9701A` | Aksen hangat — dipakai terbatas: highlight, CTA sekunder penting |
| `--color-success-700` | `#1F7A4D` | Label "Strong Match" |
| `--color-success-100` | `#E3F3E9` | Background badge Strong Match |
| `--color-warning-700` | `#B5760C` | Label "Consider" |
| `--color-warning-100` | `#FBEEDA` | Background badge Consider |
| `--color-danger-700` | `#A3352A` | Label "Not a Fit" |
| `--color-danger-100` | `#F7E4E1` | Background badge Not a Fit |
| `--color-ink-dark-bg` | `#12161C` | Sidebar (dark mode section, opsional) |

**Aturan pemakaian warna:**
- Deep teal (`primary-700`) HANYA untuk elemen aksi utama (tombol primer, nav aktif) — jangan dipakai berlebihan di body.
- Amber (`accent-600`) dipakai sangat terbatas (mis. ikon "AI-generated" badge) supaya tetap terasa premium, bukan warna dominan.
- Tiga warna status (success/warning/danger) HANYA untuk label Strong Match/Consider/Not a Fit — jangan dipakai untuk elemen UI lain agar tidak membingungkan recruiter.

### 2.2 Tipografi

| Peran | Font | Keterangan |
|---|---|---|
| Heading (H1–H3) | **Fraunces** (serif, weight 500–600) | Memberi kesan editorial/profesional — pembeda dari tampilan "generic AI dashboard" yang biasanya full sans-serif teknis |
| Body & UI Label | **Inter** (sans-serif, weight 400–500) | Keterbacaan tinggi untuk data-dense UI (tabel, form) |
| Angka/skor besar | **Inter, weight 600, tabular numbers** | Konsistensi lebar angka di tabel ranking |

Skala tipografi:
- H1: 28px / Fraunces 600
- H2: 20px / Fraunces 500
- H3: 16px / Fraunces 500
- Body: 14px / Inter 400
- Caption/metadata: 12px / Inter 400, warna `--color-ink-400`

### 2.3 Layout & Spacing
- Grid dasar 8px (spacing 8/16/24/32).
- Sidebar navigasi kiri tetap (240px), konten utama max-width 1200px dengan padding responsif.
- Card radius: 12px. Border 1px solid `--color-border`. Tanpa shadow berat — cukup border tipis (flat, profesional).
- Tabel ranking: baris dengan hover state halus (`--color-primary-100` pada background saat hover, bukan warna mencolok).

### 2.4 Komponen Kunci
- **Score Badge**: pill kecil dengan warna status (success/warning/danger) + label teks (bukan hanya warna, agar accessible untuk color-blind).
- **Score Breakdown Bar**: horizontal stacked bar 3 segmen (Skill Fit / Experience Fit / Values Fit) dengan warna netral berbeda opacity, bukan warna-warni acak.
- **AI Badge**: tanda kecil "Dibantu AI" pada konten yang dihasilkan otomatis (ringkasan, pertanyaan interview) — transparansi ke user bahwa ini bantuan AI, bukan fakta mutlak.

---

## 3. Peta Layar (Screen Inventory)

| # | Layar | Role Akses |
|---|---|---|
| 1 | Login | Semua |
| 2 | Dashboard Overview | Admin, Recruiter, Hiring Manager |
| 3 | Job Posting List | Admin, Recruiter |
| 4 | Job Posting — Create/Edit | Admin, Recruiter |
| 5 | Candidate Intake (Upload) | Recruiter |
| 6 | Candidate Ranking Dashboard | Recruiter, Hiring Manager |
| 7 | Candidate Detail | Recruiter, Hiring Manager, Interviewer |
| 8 | Candidate Comparison | Hiring Manager |
| 9 | Interview Guide Generator | Interviewer |
| 10 | Activity Log | Admin |
| 11 | User Management | Admin |

---

## 4. Detail Layar & Alur

### Layar 1 — Login
- Form sederhana: email, password, tombol "Masuk".
- Kesalahan login menampilkan pesan jelas ("Email atau kata sandi salah"), bukan generic error.
- Setelah 5x gagal → pesan "Akun dikunci sementara, coba lagi dalam 15 menit" (sesuai FR-1.4).

### Layar 2 — Dashboard Overview
- Ringkasan metrik atas: jumlah job aktif, total kandidat baru minggu ini, distribusi label (Strong Match/Consider/Not a Fit) dalam bentuk bar chart horizontal sederhana.
- List "Job aktif" dengan jumlah kandidat per job, klik → masuk ke Ranking Dashboard job tsb.

### Layar 3 — Job Posting List
- Tabel: Judul Job | Department | Status | Jumlah Kandidat | Tanggal Dibuat.
- Filter status (draft/active/closed). Tombol "+ Buat Job Baru" pojok kanan atas (primary button, teal).

### Layar 4 — Job Posting Create/Edit
- Form multi-section:
  1. Info dasar (judul, department, deskripsi — rich text sederhana)
  2. Skill wajib (tag input, multi-add)
  3. Skill nice-to-have (tag input)
  4. Pengalaman minimum (tahun) & level
  5. Bobot scoring (3 slider: Skill Fit / Experience Fit / Values Fit — total harus 100%, ada validasi real-time dengan indikator visual jika ≠ 100%)
- Tombol "Simpan sebagai Draft" (secondary) dan "Publish" (primary, disabled jika skill wajib kosong — sesuai FR-2.2).

### Layar 5 — Candidate Intake
- Drag-and-drop area untuk upload CV (+ progress bar upload).
- Form data diri kandidat (auto-terisi setelah parsing selesai, bisa diedit manual — FR-4.3).
- Section "Hasil Asesmen (opsional)" — input manual tipe MBTI/skor kompetensi 1–5 per kategori.
- Setelah submit: kandidat masuk ke antrian pemrosesan async, muncul badge status "Memproses..." di list, berubah otomatis (polling) menjadi skor final saat selesai.

### Layar 6 — Candidate Ranking Dashboard *(lihat preview visual di atas)*
- Header: nama job + jumlah total kandidat.
- Filter chip (Strong Match/Consider/Not a Fit) — klik untuk filter cepat, menunjukkan jumlah per kategori.
- Search bar nama kandidat.
- Tabel utama: Kandidat (avatar+nama+ringkas pengalaman), Skor, Label kecocokan, Status, aksi "Lihat".
- Default sort: skor tertinggi → terendah (FR-6.1). Bisa diubah user (sort by tanggal apply, nama, dst).

### Layar 7 — Candidate Detail
Layout 2 kolom:
- **Kolom kiri (60%)**: Ringkasan AI (2–4 kalimat, dengan AI Badge), Skill terdeteksi (tag list), Riwayat pengalaman (timeline vertikal), Riwayat pendidikan, Sertifikasi (list dengan link file).
- **Kolom kanan (40%)**: Score Breakdown Bar (3 segmen), detail angka per kategori (skill fit/experience fit/values fit) dengan penjelasan singkat kenapa skor segitu (mis. "2 dari 3 skill wajib terpenuhi"), tombol aksi ubah status (dropdown: New/Screening/Shortlisted/Interviewed/Hired/Rejected) — perubahan status wajib isi alasan singkat (sesuai BR-1).
- Tab tambahan: "Interview Guide" (link ke Layar 9 jika status sudah Shortlisted+).

### Layar 8 — Candidate Comparison
- Pilih 2–3 kandidat dari Ranking Dashboard (checkbox) → tombol "Bandingkan".
- Tampilan tabel side-by-side: skor per kategori, skill overlap/gap, pengalaman — memudahkan hiring manager membuat keputusan relatif.

### Layar 9 — Interview Guide Generator
- Tombol "Generate Pertanyaan" (memicu proses async LLM, ada loading state jelas "Menyusun pertanyaan berdasarkan profil kandidat...").
- Hasil ditampilkan dalam 3 section: Pertanyaan Teknikal, Pertanyaan Behavioral, Area yang Perlu Digali — masing-masing bisa diedit inline, dihapus, atau ditambah manual.
- Tombol "Generate Ulang" tidak menghapus versi lama (riwayat versi bisa dilihat via dropdown "v1, v2, ...").
- Tombol "Finalisasi Guide" mengunci versi yang dipakai untuk sesi interview.

### Layar 10 — Activity Log (Admin)
- Tabel audit: Waktu, Aktor, Aksi, Nilai Lama → Nilai Baru, terkait kandidat/job mana.
- Filter berdasarkan tanggal, aktor, jenis aksi.

### Layar 11 — User Management (Admin)
- Tabel user + role, tombol tambah user baru, ubah role, nonaktifkan akun.

---

## 5. Alur Navigasi Utama (Wireframe Flow)

```
[Login]
   │
   ▼
[Dashboard Overview] ──► [Job Posting List] ──► [Create/Edit Job]
   │                            │
   │                            ▼
   │                   [Candidate Intake] ──► (async processing)
   │                            │
   ▼                            ▼
[Ranking Dashboard] ◄───────────┘
   │
   ├──► [Candidate Detail] ──► [Interview Guide Generator]
   │
   └──► [Candidate Comparison]
```

---

## 6. Aksesibilitas & Konsistensi
- Semua label status memakai warna + teks (tidak mengandalkan warna saja) — penting untuk recruiter dengan color vision deficiency.
- Kontras teks minimal WCAG AA (4.5:1) terhadap background.
- Semua elemen interaktif (tombol, link) memiliki focus state yang terlihat jelas untuk navigasi keyboard.
- Bahasa UI: Bahasa Indonesia, nada profesional tapi tidak kaku (hindari birokratis), contoh: "Kandidat belum ada di tahap ini" bukan "Data tidak ditemukan".
-e 

---

## Task Breakdown


**Versi:** 1.0
**Referensi:** 01-PRD.md, 02-SRS.md, 03-SDD.md, 04-UIUX-Flow.md

Dipecah dalam 6 fase agar bisa dikerjakan solo secara bertahap (cocok untuk timeline portofolio, estimasi asumsi dikerjakan paruh waktu di sela kuliah/kerja).

---

## Fase 0 — Setup & Fondasi (Estimasi: 2–3 hari)

| # | Task | Output |
|---|---|---|
| 0.1 | Setup repo (monorepo: `frontend/` + `backend/`), konvensi commit, `.env.example` | Struktur project siap |
| 0.2 | Setup PostgreSQL: pakai **Supabase project** (rekomendasi — hosted Postgres, gratis untuk skala portofolio, langsung dapat connection string & storage bucket) *atau* PostgreSQL lokal via installer native (bukan Docker). Setup Redis lokal (native install) untuk Celery. | `DATABASE_URL` & `REDIS_URL` di `.env` siap dipakai |
| 0.3 | Setup FastAPI skeleton + struktur folder modular (sesuai SDD §5) | `main.py` jalan, `/health` endpoint OK |
| 0.4 | Setup Next.js 15 + TypeScript + TailwindCSS + Shadcn UI, terapkan design tokens dari UI/UX Flow §2 | Base layout & tema warna siap dipakai semua halaman |
| 0.5 | Setup Alembic migration awal + koneksi SQLAlchemy ke PostgreSQL | Migration pertama jalan |

---

## Fase 1 — Auth & User Management (Estimasi: 2 hari)

| # | Task | Referensi |
|---|---|---|
| 1.1 | Model `users` + migration | SDD §3.1 |
| 1.2 | Endpoint register (Admin-only, internal) & login (JWT) | FR-1.1–1.3, SRS §3 |
| 1.3 | Middleware auth + role guard (dependency injection FastAPI) | SRS §2 |
| 1.4 | Rate limiting login (5x gagal → lock 15 menit) | FR-1.4 |
| 1.5 | Halaman Login (frontend) + state management token (refresh flow) | UI/UX Layar 1 |
| 1.6 | Halaman User Management (Admin) — CRUD user & role | UI/UX Layar 11 |

**Milestone:** Bisa login, role-based access berjalan, Admin bisa kelola user.

---

## Fase 2 — Job Posting Module (Estimasi: 3 hari)

| # | Task | Referensi |
|---|---|---|
| 2.1 | Model `job_postings` + migration | SDD §3.1 |
| 2.2 | Endpoint CRUD job posting + validasi bobot scoring = 100% | FR-2.1–2.3 |
| 2.3 | Business rule: job `closed` tidak bisa diedit kriteria | BR-2 |
| 2.4 | Halaman Job Posting List (frontend) + filter status | UI/UX Layar 3 |
| 2.5 | Halaman Create/Edit Job — form multi-section + slider bobot dengan validasi real-time | UI/UX Layar 4 |

**Milestone:** HR bisa membuat & mengelola lowongan lengkap dengan kriteria scoring.

---

## Fase 3 — Candidate Intake & Document AI (Estimasi: 5–6 hari, fase paling kompleks)

| # | Task | Referensi |
|---|---|---|
| 3.1 | Setup **Supabase Storage bucket** (privat) untuk CV & sertifikat + upload handler dari FastAPI (pakai Supabase Python client / signed upload URL) | FR-3.1–3.2 |
| 3.2 | Model `candidates` + migration | SDD §3.1 |
| 3.3 | Endpoint intake kandidat (multipart form) + validasi ukuran/tipe file | FR-3.4, validasi §4 |
| 3.4 | Setup Celery + Redis worker | SDD §2 |
| 3.5 | Implementasi parser teks (PyMuPDF/pdfplumber) untuk ekstraksi teks mentah dari PDF/DOCX | FR-4.1 |
| 3.6 | Implementasi entity extraction (regex + spaCy/LLM-assisted) → nama, email, telepon, pendidikan, pengalaman, skill | FR-4.1–4.2 |
| 3.7 | Handle kegagalan parsing → status `needs_manual_review` | FR-3.5 |
| 3.8 | Endpoint edit manual hasil parsing (koreksi recruiter) | FR-4.3 |
| 3.9 | Halaman Candidate Intake (frontend) — drag-drop upload, form asesmen manual, polling status | UI/UX Layar 5 |

**Milestone:** Kandidat bisa diupload, CV diparsing otomatis, data terstruktur tersimpan.

---

## Fase 4 — AI Matching Engine & Ranking (Estimasi: 5 hari)

| # | Task | Referensi |
|---|---|---|
| 4.1 | Implementasi scoring rule-based: Skill Fit (overlap wajib/nice-to-have) | FR-5.1 |
| 4.2 | Implementasi scoring Experience Fit (tahun pengalaman vs requirement) | FR-5.1 |
| 4.3 | Integrasi LLM untuk Values/Behavioral Fit assist + ringkasan kandidat (LangChain + Gemini/OpenAI API) | FR-5.5 |
| 4.4 | Kombinasi skor berbobot sesuai job (final_score) + mapping label (Strong Match/Consider/Not a Fit) | FR-5.2–5.4 |
| 4.5 | Handle fallback jika LLM gagal/timeout (skor tetap jalan dengan komponen rule-based) | Edge case SRS §7 |
| 4.6 | Simpan score_breakdown untuk explainability + model_version untuk audit | BR-5 |
| 4.7 | Model `candidate_scores` + migration | SDD §3.1 |
| 4.8 | Endpoint trigger & get skor kandidat | API SDD §4 |
| 4.9 | Halaman Ranking Dashboard (frontend) — tabel, filter, search, sort | UI/UX Layar 6 |
| 4.10 | Halaman Candidate Detail — score breakdown bar, ringkasan AI, ubah status | UI/UX Layar 7 |

**Milestone:** Kandidat otomatis mendapat skor & ranking yang bisa dijelaskan (explainable).

---

## Fase 5 — Interview Assistant & Fitur Pendukung (Estimasi: 4 hari)

| # | Task | Referensi |
|---|---|---|
| 5.1 | Implementasi generator pertanyaan interview via LLM (berbasis gap kandidat vs job) | FR-8.1 |
| 5.2 | Model `interview_guides` + versioning | SDD §3.1 |
| 5.3 | Endpoint generate/edit/get interview guide | API SDD §4 |
| 5.4 | Halaman Interview Guide Generator (frontend) | UI/UX Layar 9 |
| 5.5 | Halaman Candidate Comparison (2–3 kandidat side-by-side) | UI/UX Layar 8 |
| 5.6 | Export laporan kandidat ke PDF + disclaimer | FR-9.1–9.2 |
| 5.7 | Activity log (backend: pencatatan otomatis di setiap perubahan status/skor) + halaman Activity Log (Admin) | FR-7.3, UI/UX Layar 10 |
| 5.8 | Halaman Dashboard Overview (metrik ringkas) | UI/UX Layar 2 |

**Milestone:** Fitur MVP lengkap end-to-end, siap untuk demo penuh.

---

## Fase 6 — Polish, Testing, & Deployment (Estimasi: 3–4 hari)

| # | Task | Output |
|---|---|---|
| 6.1 | Testing manual seluruh user flow (Flow A–E di PRD §5) | Checklist QA lolos |
| 6.2 | Unit test untuk logic scoring (matching engine) — kritikal karena ini "otak" produk | Test coverage scoring ≥ 80% |
| 6.3 | Review UI konsistensi (spacing, warna, tipografi) sesuai design system | Tidak ada elemen "AI-slop"/inconsistent |
| 6.4 | Isi data dummy realistis (seed data) untuk keperluan demo portofolio | Database seed script |
| 6.5 | Deploy backend (Railway/Render, tanpa Docker — deploy langsung dari repo Python) + frontend (Vercel) + database (Supabase, lanjutkan dari yang dipakai sejak Fase 0) | Link demo live |
| 6.6 | Tulis dokumentasi README + rekam demo video singkat (2–3 menit) untuk portofolio | README.md + video link |
| 6.7 | Tulis studi kasus (case study write-up) untuk portofolio: masalah → solusi → hasil → tech stack | Halaman/portofolio case study |

**Milestone:** Produk siap ditampilkan sebagai portofolio dengan demo live + dokumentasi lengkap.

---

## Ringkasan Timeline

| Fase | Fokus | Estimasi |
|---|---|---|
| 0 | Setup & Fondasi | 2–3 hari |
| 1 | Auth & User Management | 2 hari |
| 2 | Job Posting Module | 3 hari |
| 3 | Candidate Intake & Document AI | 5–6 hari |
| 4 | AI Matching Engine & Ranking | 5 hari |
| 5 | Interview Assistant & Fitur Pendukung | 4 hari |
| 6 | Polish, Testing, Deployment | 3–4 hari |
| **Total** | | **~24–28 hari kerja** (bisa lebih lama jika paruh waktu di sela aktivitas lain) |

**Catatan urutan pengerjaan:** Fase 3 & 4 adalah inti nilai jual produk ini (AI-nya) — jangan buru-buru ke Fase 5/6 sebelum scoring engine benar-benar solid dan explainable, karena itu yang paling menarik dijelaskan saat wawancara kerja/portofolio.
-e 

---

