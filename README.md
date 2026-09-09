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
alembic upgrade head           # creates the schema in your Supabase DB
python scripts/create_admin.py --name "Your Name" --email you@example.com --password "ChangeMe123"
uvicorn app.main:app --reload
```

> **DATABASE_URL note:** use Supabase's **Session pooler** connection string
> (`postgres.<project-ref>@aws-0-<region>.pooler.supabase.com:5432`), not
> "Direct connection" — the direct host is IPv6-only and fails to resolve
> on many networks.

API docs at `http://localhost:8000/docs`, health check at `http://localhost:8000/health`.

There's no self-register endpoint by design (FR-1.5) — every account
after the first is created by an Admin via `POST /api/v1/users` (or the
User Management screen once logged in). `scripts/create_admin.py` only
exists to bootstrap that first account.

### Background worker (candidate parsing, from Phase 3)

Resume parsing runs async via Celery + Redis — never inline in the
upload request.

```bash
cd backend
celery -A app.workers.celery_app worker --loglevel=info --pool=solo   # --pool=solo is a Windows requirement
```

Needs Redis reachable at `REDIS_URL`. Redis has no official Windows
build; see `backend/.redis-portable/README.md` for a no-admin-rights
way to run it on Windows (or use WSL2 / a normal Linux box, where
`redis-server` just works).

### Frontend

```bash
cd frontend
npm install
copy .env.example .env.local   # NEXT_PUBLIC_API_URL, defaults to the local backend above
npm run dev
```

App at `http://localhost:3000` — redirects to `/login`.

## Status

Phase 3 of 6 done (candidate intake + resume parsing). See
`docs/HireLens-AI-Documentation.md` §Task Breakdown for the full plan.

- [x] Phase 0 — repo scaffolding, design tokens, FastAPI + Next.js skeletons
- [x] Phase 1 — auth (JWT, lockout), role guard, user management
- [x] Phase 2 — job posting module (CRUD, weight validation, BR-2 lock)
- [x] Phase 3 — candidate intake, Supabase Storage, async resume parsing
- [ ] Phase 4 — matching engine + ranking dashboard
- [ ] Phase 5 — interview assistant, comparison, export, activity log
- [ ] Phase 6 — polish, tests, deploy

## License

Not yet decided (portfolio project).
