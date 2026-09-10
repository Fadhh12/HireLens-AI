"""Async task functions for CV parsing, scoring, and interview-guide
generation (brief §7: never run these inline in a request handler).

These originally ran on Celery + Redis. Switched to plain functions
dispatched via FastAPI's BackgroundTasks (app.add_task(fn, ...) at each
call site, e.g. app/modules/candidates/router.py) for Task 6.5 (deploy):
Celery needs an always-on worker process, which every truly free hosting
tier either doesn't offer or charges for — and this is a portfolio demo,
not a production system with real task-queue durability requirements.
BackgroundTasks still runs the work after the HTTP response is sent
(same user-facing "returns immediately, ranking appears within budget"
behavior), just in-process instead of in a separate worker — no retry-
after-crash or multi-worker fan-out, which this project doesn't need.
"""
