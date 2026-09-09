# HireLens AI

AI-powered talent screening & matching platform. Recruiters upload candidate CVs/certificates against a job posting; the system parses the documents, scores candidates against the job's requirements (skill fit, experience fit, values fit), ranks them with a fully explainable breakdown, and generates candidate-specific interview questions — no black-box.

> Portfolio project by **Nabil Fadhlur Rahman**. Full product/engineering docs (PRD, SRS, SDD, UI/UX, task breakdown) live in [`docs/HireLens-AI-Documentation.md`](docs/HireLens-AI-Documentation.md).

## Why

Conventional CV screening is slow, subjective, and inconsistent across recruiters. HireLens AI doesn't replace the hiring decision — it standardizes and speeds up everything before it: structured extraction from CVs, auditable rule-based scoring against job criteria, and AI-assisted interview prep.

## Tech stack

| Layer | Choice |
|---|---|
| Frontend | Next.js 15, React 19, TypeScript, TailwindCSS, Shadcn UI |
| Backend | FastAPI (Python 3.11+), Pydantic v2 |
| Background jobs | Celery + Redis (resume parsing & LLM calls are async, never block a request) |
| Database | PostgreSQL (Supabase-hosted) + SQLAlchemy + Alembic |
| Object storage | Supabase Storage (private bucket, signed URLs) |
| Resume parsing | PyMuPDF/pdfplumber + spaCy/regex entity extraction |
| Generative AI | LangChain + Gemini API (provider swappable behind one interface) |
| Auth | JWT (access + refresh), passlib/bcrypt |
| Infra | No Docker — plain Python venv + `uvicorn`, native Redis |

## Architecture

Modular monolith, not microservices — right-sized for a solo-built portfolio project while staying split by domain so it could be pulled apart later if needed.

```
Next.js client → FastAPI (auth, rate limit, validation)
                     ├── Core Service (jobs, candidates, auth)
                     ├── Document AI Service (parsing)
                     └── Matching Engine (rule-based scoring + LLM assist)
                              │
                     Celery/Redis background workers
                              │
                     Supabase Postgres + Supabase Storage
                              │
                     Gemini API (summary, values-fit assist, interview questions)
```

The matching engine is rule-based and deterministic (skill fit / experience fit / values fit → weighted final score, stored as structured `score_breakdown` JSON). The LLM only assists values-fit notes, candidate summaries, and interview question generation — it is never the sole source of the numeric score.

## Project structure

```
├── docs/                          # PRD / SRS / SDD / UI-UX / task breakdown — source of truth
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI entrypoint
│   │   ├── core/                  # config, security (JWT/hashing), auth dependencies
│   │   ├── modules/                # domain modules: auth, jobs, candidates, document_ai, matching_engine, interview
│   │   ├── workers/                # Celery app + tasks (parsing, scoring)
│   │   └── db/                     # SQLAlchemy base/session, Alembic migrations
│   ├── tests/
│   └── requirements.txt
└── frontend/                       # Next.js 15 app (App Router, TS, Tailwind, Shadcn)
```

## Getting started

### Prerequisites
- Python 3.11+
- Node.js 20+
- A [Supabase](https://supabase.com) project (Postgres + Storage) — or local PostgreSQL as a fallback
- Redis (native install — no Docker)
- A Gemini API key ([Google AI Studio](https://aistudio.google.com/app/apikey))

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows; use `source .venv/bin/activate` on macOS/Linux
pip install -r requirements.txt
copy .env.example .env        # then fill in DATABASE_URL, SUPABASE_URL, SUPABASE_KEY, GOOGLE_API_KEY, JWT_SECRET_KEY
uvicorn app.main:app --reload
```

API docs at `http://localhost:8000/docs`, health check at `http://localhost:8000/health`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App at `http://localhost:3000`.

## Status

Early scaffolding (Phase 0 of the build order in `docs/HireLens-AI-Documentation.md` §Task Breakdown). See that file for the full 0–6 phase plan.

## License

Not yet decided (portfolio project).
