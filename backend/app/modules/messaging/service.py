"""Template rendering, sending status-change emails, and polling for
candidate replies.

Trigger is deliberately narrower than CandidateStatus: only shortlisted/
rejected/hired send an email from here. "interviewed" already gets its
own notification — the Google Calendar invite from scheduling/service.py
— sending a second, different email for the same transition would be
confusing, not helpful (this exact trade-off was confirmed with the
user rather than assumed).
"""

import logging
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.activity_log.service import log_activity
from app.modules.candidates.model import Candidate
from app.modules.jobs.service import get_job
from app.modules.messaging.model import CandidateEmail, EmailTemplate, EmailTrigger
from app.modules.messaging.schema import EmailTemplateUpdate
from app.modules.scheduling import google_client
from app.modules.scheduling.google_client import GoogleCalendarError
from app.modules.scheduling.model import GoogleCredential

logger = logging.getLogger(__name__)

# Polite Indonesian defaults, editable by admin/recruiter (see router.py) —
# {{full_name}}/{{job_title}}/{{department}} are filled in per candidate,
# which is what covers "menyesuaikan isi dari bidang yang dilamar" without
# needing one template per job.
DEFAULT_TEMPLATES: dict[EmailTrigger, tuple[str, str]] = {
    EmailTrigger.shortlisted: (
        "Update Lamaran Anda — Posisi {{job_title}}",
        "Halo {{full_name}},\n\n"
        "Terima kasih telah melamar posisi {{job_title}} di {{department}}. "
        "Kami senang menginformasikan bahwa Anda lolos tahap screening awal "
        "dan akan melanjutkan ke tahap berikutnya.\n\n"
        "Tim kami akan menghubungi Anda untuk informasi lebih lanjut mengenai "
        "tahapan selanjutnya.\n\n"
        "Salam,\nTim Rekrutmen",
    ),
    EmailTrigger.rejected: (
        "Update Lamaran Anda — Posisi {{job_title}}",
        "Halo {{full_name}},\n\n"
        "Terima kasih atas waktu dan minat Anda melamar posisi {{job_title}} "
        "di {{department}}. Setelah mempertimbangkan dengan saksama, kami "
        "memutuskan untuk melanjutkan proses dengan kandidat lain yang saat "
        "ini paling sesuai dengan kebutuhan kami.\n\n"
        "Kami sangat menghargai usaha dan waktu Anda, dan berharap dapat "
        "berkesempatan bekerja sama di lain waktu.\n\n"
        "Salam,\nTim Rekrutmen",
    ),
    EmailTrigger.hired: (
        "Selamat! Anda Diterima — Posisi {{job_title}}",
        "Halo {{full_name}},\n\n"
        "Selamat! Kami dengan senang hati menginformasikan bahwa Anda "
        "diterima untuk posisi {{job_title}} di {{department}}.\n\n"
        "Tim kami akan segera menghubungi Anda untuk proses selanjutnya, "
        "termasuk dokumen administrasi.\n\n"
        "Selamat bergabung, dan sampai jumpa!\n\nSalam,\nTim Rekrutmen",
    ),
}


def _placeholders(candidate: Candidate, job_title: str, department: str) -> dict[str, str]:
    return {"full_name": candidate.full_name, "job_title": job_title, "department": department}


def _render(text: str, values: dict[str, str]) -> str:
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def get_or_create_template(db: Session, trigger: EmailTrigger) -> EmailTemplate:
    template = db.get(EmailTemplate, trigger)
    if template is None:
        subject, body = DEFAULT_TEMPLATES[trigger]
        template = EmailTemplate(trigger=trigger, subject=subject, body=body)
        db.add(template)
        db.commit()
        db.refresh(template)
    return template


def list_templates(db: Session) -> list[EmailTemplate]:
    return [get_or_create_template(db, t) for t in EmailTrigger]


def update_template(db: Session, trigger: EmailTrigger, data: EmailTemplateUpdate, actor_id: uuid.UUID) -> EmailTemplate:
    template = get_or_create_template(db, trigger)
    template.subject = data.subject
    template.body = data.body
    template.updated_by = actor_id
    db.commit()
    db.refresh(template)
    return template


def _send(
    db: Session,
    candidate: Candidate,
    trigger: EmailTrigger,
    actor_id: uuid.UUID,
    attachment: tuple[str, str, bytes] | None,
) -> CandidateEmail:
    if not candidate.email:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Kandidat tidak punya alamat email")

    credential = db.get(GoogleCredential, actor_id)
    if credential is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hubungkan Google Calendar/Gmail Anda dulu sebelum mengirim email",
        )

    job = get_job(db, candidate.job_posting_id)
    template = get_or_create_template(db, trigger)
    values = _placeholders(candidate, job.title, job.department)
    subject = _render(template.subject, values)
    body = _render(template.body, values)

    try:
        sent = google_client.send_email(
            refresh_token=credential.refresh_token,
            to=candidate.email,
            subject=subject,
            body_text=body,
            attachment=attachment,
        )
    except GoogleCalendarError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    record = CandidateEmail(
        id=uuid.uuid4(),
        candidate_id=candidate.id,
        sent_by=actor_id,
        trigger=trigger,
        subject=subject,
        body=body,
        attachment_filename=attachment[0] if attachment else None,
        gmail_thread_id=sent.thread_id,
        gmail_message_id=sent.message_id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    log_activity(
        db,
        actor_id=actor_id,
        action=f"email_{trigger.value}_sent",
        candidate_id=candidate.id,
        new_value=subject,
    )
    return record


def send_status_email(
    db: Session,
    candidate: Candidate,
    trigger: EmailTrigger,
    actor_id: uuid.UUID,
    attachment: tuple[str, str, bytes] | None = None,
) -> CandidateEmail:
    """Raises HTTPException on any failure — used by the explicit
    'Kirim ulang + lampirkan PDF' action, where the HR clicking it
    needs to see why it failed."""
    return _send(db, candidate, trigger, actor_id, attachment)


def send_status_email_best_effort(db: Session, candidate: Candidate, trigger: EmailTrigger, actor_id: uuid.UUID) -> None:
    """Used from candidates/service.py's update_status — a status change
    must never fail just because the auto-email couldn't go out (no
    Google connection yet, Gmail hiccup, candidate has no email, ...).
    Silently no-ops on failure; HR can always use the explicit send
    action afterward once whatever was wrong is fixed."""
    try:
        _send(db, candidate, trigger, actor_id, attachment=None)
    except HTTPException as exc:
        logger.info("Auto status-email skipped for candidate %s: %s", candidate.id, exc.detail)
    except Exception:  # noqa: BLE001 - must never break the status change itself
        logger.exception("Auto status-email failed unexpectedly for candidate %s", candidate.id)


def list_candidate_emails(db: Session, candidate_id: uuid.UUID) -> list[CandidateEmail]:
    return list(
        db.scalars(
            select(CandidateEmail)
            .where(CandidateEmail.candidate_id == candidate_id)
            .order_by(CandidateEmail.sent_at.desc())
        )
    )


def poll_replies(db: Session) -> int:
    """Checks every not-yet-replied CandidateEmail's Gmail thread for a
    reply. No push notification path (would need a Cloud Pub/Sub topic +
    a publicly reachable webhook) — called on a periodic best-effort
    loop from app startup (see main.py) and can also be triggered
    manually (POST /email-templates/poll-replies) since that background
    loop's reliability depends on the host process staying warm, which
    this project can't guarantee on every hosting platform.

    Returns how many new replies were found."""
    pending = list(db.scalars(select(CandidateEmail).where(CandidateEmail.has_reply.is_(False))))
    if not pending:
        return 0

    # Group by sender so each recruiter's Google credential is only
    # fetched/refreshed once per poll, not once per pending email.
    by_sender: dict[uuid.UUID, list[CandidateEmail]] = {}
    for email in pending:
        by_sender.setdefault(email.sent_by, []).append(email)

    found = 0
    for sender_id, emails in by_sender.items():
        credential = db.get(GoogleCredential, sender_id)
        if credential is None:
            continue  # disconnected since sending — nothing to poll with
        for email in emails:
            try:
                snippet = google_client.thread_has_reply(
                    credential.refresh_token, email.gmail_thread_id, email.gmail_message_id
                )
            except GoogleCalendarError as exc:
                logger.warning("poll_replies: failed reading thread %s: %s", email.gmail_thread_id, exc)
                continue
            if snippet is not None:
                email.has_reply = True
                email.reply_snippet = snippet
                email.reply_detected_at = datetime.now(timezone.utc)
                db.commit()
                log_activity(
                    db,
                    actor_id=sender_id,
                    action="candidate_replied",
                    candidate_id=email.candidate_id,
                    new_value=snippet[:500],
                )
                found += 1
    return found
