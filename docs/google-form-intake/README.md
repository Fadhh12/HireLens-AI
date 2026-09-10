# Google Form → HireLens AI intake bridge

A way to test candidate intake from *outside* the app: a public Google
Form an applicant fills in (with their CV attached) auto-submits into
the same real parser + real scorer pipeline recruiters use, via a new
backend endpoint (`POST /api/v1/public/apply`, see
`backend/app/modules/candidates/router.py`).

This is a test/demo channel, not a production integration — no retry
queue, no delivery guarantees beyond what Apps Script itself gives you.

## 1. Create the Form

Go to [forms.google.com](https://forms.google.com) → blank form. Add
these questions with **these exact titles** (the script below matches
on them verbatim):

| Question title | Type | Required |
|---|---|---|
| Nama Lengkap | Short answer | Yes |
| Email | Short answer | Yes |
| No. Telepon | Short answer | Yes |
| Posisi yang Dilamar | Dropdown | Yes |
| CV (PDF/DOCX) | File upload | Yes |

For **Posisi yang Dilamar**, add one option per *currently active* job
title — check `/dashboard/jobs` for the live list (as of this write-up:
Backend Engineer, Product Manager, Junior Frontend, Data Analyst, UX
Designer). The option text must match the job's title **exactly** —
the backend looks the job up by exact title match.

For **CV (PDF/DOCX)**: in the file-upload question's settings, set
"Maximum number of files" to 1 and allowed file types to PDF/document
types. Google will ask you to enable file uploads for the form (this
creates a Drive folder it stores submissions in) — allow it.

## 2. Add the Apps Script

On the Form, open the **⋮** (more) menu → **Script editor**. Delete
any starter code and paste in `apply-webhook.gs` from this folder.
Fill in the two constants at the top:

- `BACKEND_URL` — see §4 below, this can't be `localhost` as-is.
- `API_KEY` — the value of `PUBLIC_APPLY_API_KEY` in `backend/.env`.

## 3. Wire up the trigger

In the Apps Script editor: clock icon (**Triggers**) on the left →
**+ Add Trigger** →
- Function: `onFormSubmit`
- Event source: **From form**
- Event type: **On form submit**

Save — Google will ask you to authorize the script (it needs Drive
read access for the CV file, and Gmail send access for the
failure-notification email). This is a one-time consent screen for
your own Google account.

## 4. Getting a public URL to your local backend

Apps Script runs on Google's servers, not your machine — it can't
reach `http://localhost:8000` directly. Two options:

- **Deploy first** (Task 6.5) and point `BACKEND_URL` at the real
  Railway/Render URL — the natural long-term setup, no extra step.
- **Temporary tunnel for testing today** — e.g.
  [ngrok](https://ngrok.com): `ngrok http 8000` gives you a temporary
  `https://xxxx.ngrok-free.app` URL that forwards to your local
  backend. Put that in `BACKEND_URL`. The URL changes every time you
  restart ngrok on the free tier, so you'd update the script's
  constant each session.

## 5. Test it

Submit the Form yourself with a real CV attached. Within a few
seconds:
- A new candidate should appear under the job you picked, at
  `/dashboard/jobs/{job-id}/candidates` — with a real parsed profile
  and real score, same as an upload through the recruiter UI.
- If something failed (bad job title, wrong API key, backend
  unreachable), you'll get an email at your own Google account from
  the script's error handler instead of a silent drop.

You can also check the Apps Script editor's **Executions** tab (clock
icon → Executions) for a log of every run and its result.
