"""Thin wrapper around Google's OAuth + Calendar/Gmail APIs — isolates
every bit of google-auth-oauthlib/google-api-python-client usage in one
file, the same way llm_assist.py isolates the Gemini SDK from the rest
of the app.

Requires GOOGLE_OAUTH_CLIENT_ID / GOOGLE_OAUTH_CLIENT_SECRET /
GOOGLE_OAUTH_REDIRECT_URI (see app/core/config.py) — these come from a
Google Cloud project the user creates themselves (OAuth consent screen +
a Web application OAuth client with the Calendar API and Gmail API both
enabled). Every function here raises GoogleCalendarError on failure so
callers (service.py) can turn it into a clean HTTP error instead of a
raw googleapiclient traceback.

gmail.send/gmail.readonly were added after calendar.events was already
shipped (see messaging/ module) — an account connected before that
addition only granted the old, narrower scope, so it must reconnect
("Hubungkan Google Calendar") to pick up email sending/reply-detection;
there's no way to silently widen an already-issued grant.
"""

import base64
import uuid
from datetime import datetime, timedelta, timezone
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2.credentials import Credentials
from google.oauth2.id_token import verify_oauth2_token
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.core.config import get_settings

# calendar.events (create/manage events), gmail.send (status-change
# notifications), gmail.readonly (detect a candidate's reply in that
# thread — see messaging/service.py's poll_replies), openid/email
# (identify which Google account got connected, shown in the UI).
SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
    "openid",
    "email",
]


class GoogleCalendarError(Exception):
    """Any failure talking to Google (not configured, expired grant, API error)."""


def _require_configured() -> None:
    settings = get_settings()
    if not (settings.google_oauth_client_id and settings.google_oauth_client_secret and settings.google_oauth_redirect_uri):
        raise GoogleCalendarError(
            "Integrasi Google Calendar belum dikonfigurasi "
            "(GOOGLE_OAUTH_CLIENT_ID/SECRET/REDIRECT_URI kosong)"
        )


def _client_config() -> dict:
    settings = get_settings()
    return {
        "web": {
            "client_id": settings.google_oauth_client_id,
            "client_secret": settings.google_oauth_client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [settings.google_oauth_redirect_uri],
        }
    }


def build_authorization_url(state: str) -> str:
    """`state` carries the recruiter's user id through Google's redirect
    so the callback knows whose GoogleCredential row to write."""
    _require_configured()
    flow = Flow.from_client_config(_client_config(), scopes=SCOPES, state=state)
    flow.redirect_uri = get_settings().google_oauth_redirect_uri
    # access_type=offline + prompt=consent: Google only returns a
    # refresh_token on first consent by default — forcing the consent
    # screen every time guarantees one even on a reconnect.
    url, _ = flow.authorization_url(access_type="offline", prompt="consent", include_granted_scopes="true")
    return url


class ExchangedTokens:
    def __init__(self, refresh_token: str, access_token: str, expires_at: datetime, google_email: str):
        self.refresh_token = refresh_token
        self.access_token = access_token
        self.expires_at = expires_at
        self.google_email = google_email


def exchange_code(code: str) -> ExchangedTokens:
    _require_configured()
    settings = get_settings()
    flow = Flow.from_client_config(_client_config(), scopes=SCOPES)
    flow.redirect_uri = settings.google_oauth_redirect_uri
    try:
        flow.fetch_token(code=code)
    except Exception as exc:  # noqa: BLE001 - googleapiclient/oauthlib raise assorted types here
        raise GoogleCalendarError(f"Gagal menukar kode otorisasi Google: {exc}") from exc

    creds = flow.credentials
    if not creds.refresh_token:
        raise GoogleCalendarError(
            "Google tidak mengirim refresh token — coba hubungkan ulang "
            "(pastikan akses sebelumnya sudah dicabut di myaccount.google.com/permissions)"
        )

    email = None
    if creds.id_token:
        try:
            claims = verify_oauth2_token(creds.id_token, GoogleAuthRequest(), settings.google_oauth_client_id)
            email = claims.get("email")
        except Exception:  # noqa: BLE001 - id_token is optional context, never fatal
            email = None

    expires_at = creds.expiry.replace(tzinfo=timezone.utc) if creds.expiry else datetime.now(timezone.utc)
    return ExchangedTokens(
        refresh_token=creds.refresh_token,
        access_token=creds.token,
        expires_at=expires_at,
        google_email=email or "",
    )


def _credentials_from_refresh_token(refresh_token: str) -> Credentials:
    settings = get_settings()
    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.google_oauth_client_id,
        client_secret=settings.google_oauth_client_secret,
        scopes=SCOPES,
    )
    try:
        creds.refresh(GoogleAuthRequest())
    except Exception as exc:  # noqa: BLE001 - refresh failures are all "reconnect" cases
        raise GoogleCalendarError(
            f"Gagal me-refresh akses Google Calendar — coba hubungkan ulang akun ({exc})"
        ) from exc
    return creds


class CreatedEvent:
    def __init__(self, event_id: str, meet_link: str, html_link: str | None):
        self.event_id = event_id
        self.meet_link = meet_link
        self.html_link = html_link


def create_interview_event(
    refresh_token: str,
    summary: str,
    description: str,
    start: datetime,
    end: datetime,
    attendee_emails: list[str],
    send_updates: str = "none",
) -> CreatedEvent:
    """Creates a Calendar event with an auto-generated Google Meet link and
    adds `attendee_emails`. `send_updates` defaults to "none" — the
    interview trigger's own templated Gmail send (messaging/service.py,
    with the Meet link filled into {{meet_link}}) is what notifies the
    candidate now, so Calendar's own bare invite email would just be a
    redundant, differently-worded second message. Pass "all" to fall
    back to Calendar's own invite email instead."""
    _require_configured()
    creds = _credentials_from_refresh_token(refresh_token)
    service = build("calendar", "v3", credentials=creds, cache_discovery=False)

    request_id = str(uuid.uuid4())
    body = {
        "summary": summary,
        "description": description,
        "start": {"dateTime": start.isoformat()},
        "end": {"dateTime": end.isoformat()},
        "attendees": [{"email": email} for email in attendee_emails],
        "conferenceData": {
            "createRequest": {
                "requestId": request_id,
                "conferenceSolutionKey": {"type": "hangoutsMeet"},
            }
        },
    }

    try:
        event = (
            service.events()
            .insert(calendarId="primary", body=body, conferenceDataVersion=1, sendUpdates=send_updates)
            .execute()
        )
    except HttpError as exc:
        raise GoogleCalendarError(f"Google Calendar menolak permintaan: {exc}") from exc

    meet_link = event.get("hangoutLink", "")
    if not meet_link:
        for entry_point in event.get("conferenceData", {}).get("entryPoints", []):
            if entry_point.get("entryPointType") == "video":
                meet_link = entry_point.get("uri", "")
                break

    return CreatedEvent(event_id=event["id"], meet_link=meet_link, html_link=event.get("htmlLink"))


def default_interview_window(scheduled_at: datetime, duration_minutes: int) -> tuple[datetime, datetime]:
    return scheduled_at, scheduled_at + timedelta(minutes=duration_minutes)


class SentEmail:
    def __init__(self, message_id: str, thread_id: str):
        self.message_id = message_id
        self.thread_id = thread_id


def send_email(
    refresh_token: str,
    to: str,
    subject: str,
    body_text: str,
    attachment: tuple[str, str, bytes] | None = None,
) -> SentEmail:
    """Sends from the connected recruiter's own Gmail — replies land in
    their real inbox, which is what makes poll-for-replies below work.
    `attachment` is (filename, mime_type, content) — the optional
    assessment/contract PDF an HR can attach when re-sending (see
    messaging/router.py's send endpoint)."""
    _require_configured()
    creds = _credentials_from_refresh_token(refresh_token)
    service = build("gmail", "v1", credentials=creds, cache_discovery=False)

    message = MIMEMultipart() if attachment else MIMEText(body_text)
    if attachment:
        message.attach(MIMEText(body_text))
        filename, mime_type, content = attachment
        maintype, _, subtype = mime_type.partition("/")
        part = MIMEApplication(content, _subtype=subtype or "octet-stream")
        part.add_header("Content-Disposition", "attachment", filename=filename)
        message.attach(part)
    message["to"] = to
    message["subject"] = subject

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    try:
        sent = service.users().messages().send(userId="me", body={"raw": raw}).execute()
    except HttpError as exc:
        raise GoogleCalendarError(f"Gmail menolak permintaan kirim: {exc}") from exc

    return SentEmail(message_id=sent["id"], thread_id=sent["threadId"])


def thread_has_reply(refresh_token: str, thread_id: str, our_message_id: str) -> str | None:
    """Returns the latest reply's snippet if the thread has any message
    besides the one we sent (our_message_id), else None. Used by
    messaging/service.py's periodic poll_replies — there's no push
    notification path here (would need a Cloud Pub/Sub topic + a
    publicly reachable webhook, more GCP setup than this project
    assumes), so replies show up on the next poll instead of instantly.
    """
    _require_configured()
    creds = _credentials_from_refresh_token(refresh_token)
    service = build("gmail", "v1", credentials=creds, cache_discovery=False)

    try:
        thread = service.users().threads().get(userId="me", id=thread_id, format="metadata").execute()
    except HttpError as exc:
        raise GoogleCalendarError(f"Gagal membaca thread Gmail: {exc}") from exc

    messages = thread.get("messages", [])
    others = [m for m in messages if m.get("id") != our_message_id]
    if not others:
        return None
    latest = others[-1]
    return latest.get("snippet", "") or "(tidak ada isi ringkas)"
