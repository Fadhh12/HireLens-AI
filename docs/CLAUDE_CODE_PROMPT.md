# Claude Code — Project Brief: HireLens AI

Read this entire file before writing any code. This is the single source of truth for what to build, how, and in what order. Do not start coding until you've also read `docs/HireLens-AI-Documentation.md` (the full PRD/SRS/SDD/UI-UX/Task Breakdown), which sits alongside this file in the repo.

---

## 1. What you're building

**HireLens AI** — an AI-powered talent screening and matching platform. Recruiters upload candidate CVs/certificates against a job posting; the system parses the documents, scores candidates against the job's requirements (skill fit, experience fit, values fit), ranks them with a fully explainable breakdown, and generates candidate-specific interview questions.

This is a **portfolio project**, not a production SaaS. Optimize for: a working, demoable end-to-end flow, clean and defensible architecture, and code you (the author) can explain confidently in a job interview. Do not over-engineer for scale that doesn't exist yet (no need for microservices, Kubernetes, multi-tenancy, etc. — see PRD "Non-Goals").

## 2. Source of truth documents

All product/engineering decisions are already made in `docs/HireLens-AI-Documentation.md`. Specifically:
- **PRD** → what to build and why, personas, MoSCoW feature list, high-level flows (Flow A–E)
- **SRS** → exact functional requirements (FR-x), validation rules, business rules (BR-x), non-functional requirements
- **SDD** → architecture diagram, tech stack, database schema, REST API contract, backend folder structure
- **UI/UX Flow** → design system (colors, typography, spacing), full screen inventory, per-screen layout spec

**Do not invent new requirements, rename entities, or change the data model without flagging it to me first.** If something in the docs is ambiguous or you think a better approach exists, stop and ask — don't silently deviate.

## 3. Tech stack (fixed — do not substitute)

| Layer | Choice |
|---|---|
| Frontend | Next.js 15, React 19, TypeScript, TailwindCSS, Shadcn UI |
| Backend | FastAPI (Python 3.11+), Pydantic v2 |
| Background jobs | Celery + Redis (resume parsing & LLM calls must be async, never block the request) |
| Database | PostgreSQL + SQLAlchemy + Alembic migrations |
| Object storage | **Supabase Storage** (private bucket, same project as the database — no separate storage service to stand up) |
| Resume parsing | PyMuPDF/pdfplumber for text extraction + spaCy/regex for entity extraction |
| Generative AI | LangChain + an LLM API (Gemini or OpenAI — use whichever key is available in `.env`; keep the provider swappable behind one interface) |
| Auth | JWT (access + refresh), passlib/bcrypt for hashing |
| Database hosting | **Supabase** (hosted PostgreSQL — use it from day one for both dev and prod; gives connection string + storage bucket without extra setup). Local PostgreSQL install is a fallback only if Supabase isn't available. |
| Infra | **No Docker.** Run the backend directly with a Python venv + `uvicorn`, and Redis via a native local install (for Celery). Keep everything runnable with plain `pip install` / `npm install` — no containerization. |

If a package listed here is deprecated or clearly wrong for a task, tell me before swapping it.

## 4. Design system — non-negotiable

Read UI/UX Flow §2 in the docs in full before building **any** component. In short:
- Palette: warm off-white background (`#F8F7F4`), near-black ink text (`#1C1F26`), deep teal primary (`#0E4F4A`), amber used sparingly as accent (`#C9701A`), and three status colors (green/amber/red) reserved *only* for the Strong Match / Consider / Not a Fit labels.
- Typography: **Fraunces** (serif) for headings, **Inter** for body/UI text — this is intentional, do not default to an all-sans-serif generic SaaS look.
- No purple-blue gradients, no glassmorphism, no neon glows, no robot/sparkle icons. This should look like a serious internal tool (think Linear/Notion for HR), not a generic "AI product" landing page.
- Status labels always show color + text together (accessibility).
- Set up the design tokens (Tailwind theme extension or CSS variables) as one of the very first frontend tasks, so every screen after that pulls from the same source instead of hardcoded hex values scattered around.

If you're about to generate a component and it starts looking like a templated shadcn demo with default blue buttons and no personality, stop and re-check the palette/typography above.

## 5. Build order — follow the phases, don't skip ahead

Follow `Task Breakdown` in the docs phase by phase (Phase 0 through Phase 6). Specifically:

1. **Phase 0–1** first: repo scaffolding, Supabase project setup (or local PostgreSQL as fallback) + `.env` with `DATABASE_URL`, auth, role-based access. Get a login screen and a protected route working before anything else. No Docker, no docker-compose file.
2. **Phase 2**: job posting CRUD, including the 100%-weight validation on the scoring sliders.
3. **Phase 3**: candidate intake + resume parsing. This is allowed to take the longest — get text extraction and entity extraction genuinely working on a few real sample CVs before moving on, don't fake it with hardcoded mock data and call it done.
4. **Phase 4**: the matching engine (skill fit / experience fit / values fit → weighted final score → label) and the ranking dashboard. This is the core value of the product — the scoring logic must be rule-based and auditable (store `score_breakdown` as structured JSON, not just a final number), with LLM used only to assist values-fit and summaries, never as the sole source of the score (SRS FR-5.5, BR-5).
5. **Phase 5**: interview question generator, candidate comparison, PDF export, activity log.
6. **Phase 6**: seed data, polish, tests on the scoring logic specifically, README, deploy.

At the end of each phase, give me a short summary of what was built, what deviated from the docs (if anything) and why, and what's left — don't silently roll multiple phases together into one giant commit.

## 6. Quality bar

- Every FR/BR/validation rule in the SRS should be traceable to actual code (validation, error handling, or a test) — not just implied.
- Write unit tests for the matching engine scoring logic specifically (SRS calls this out as critical — this is the part I'll be asked about in interviews).
- Handle the edge cases listed in SRS §7 (parsing failure, LLM timeout, duplicate candidate, oversized/invalid file) — don't leave them as TODOs.
- Keep the backend folder structure exactly as laid out in SDD §5 (modular by domain: `auth`, `jobs`, `candidates`, `document_ai`, `matching_engine`, `interview`) so the codebase reads like a real product, not a tutorial dump.
- Commit in small, logical chunks with clear messages — this repo's history should also look presentable if a recruiter skims it.

## 7. What not to do

- Don't add features not in the MVP scope (PRD §4 "Won't Have") — no video interview analysis, no external job board integration, no full HRIS/payroll.
- Don't let the LLM be the only source of the final numeric score.
- Don't hardcode the color palette/fonts inline everywhere instead of using design tokens.
- Don't skip the async job queue and call LLM/parsing synchronously "for now" — do it right from Phase 3 onward, retrofitting it later is wasted work.
- Don't introduce Docker/docker-compose — this project intentionally runs with a plain Python venv + native Redis, and PostgreSQL via Supabase (or local install as fallback).
- Don't fabricate demo data that makes the scoring look better than the logic actually produces — if the matching engine is weak on some CV formats, tell me, don't paper over it.

## 8. How to work with me

- Ask before making an architectural decision that isn't already specified in the docs (e.g., how to structure JWT refresh rotation, which LLM provider's SDK to standardize on).
- If you hit something genuinely ambiguous in the docs, quote the ambiguous part and propose your interpretation rather than guessing silently.
- Prefer working, incrementally testable code over large speculative scaffolding.

Start with Phase 0. Confirm you've read `docs/HireLens-AI-Documentation.md` and summarize the architecture back to me in a few sentences before writing the first line of code.
