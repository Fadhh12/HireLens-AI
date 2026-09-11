"""Thin wrapper around Google's OAuth + Calendar API — isolates every bit
of google-auth-oauthlib/google-api-python-client usage in one file, the
same way llm_assist.py isolates the Gemini SDK from the rest of the app.

Requires GOOGLE_OAUTH_CLIENT_ID / GOOGLE_OAUTH_CLIENT_SECRET /
GOOGLE_OAUTH_REDIRECT_URI (see app/core/config.py) — these come from a
Google Cloud project the user creates themselves (OAuth consent screen +
a Web application OAuth client with the Calendar API enabled). Every
function here raises GoogleCalendarError on failure so callers
(service.py) can turn it into a clean HTTP error instead of a raw
googleapiclient traceback.
"""

import uuid
from datetime import datetime, timedelta, timezone

from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2.credentials import Credentials
from google.oauth2.id_token import verify_oauth2_token
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.core.config import get_settings

# calendar.events (create/manage events) + openid/email (identify which
# Google account got connected, shown back to the recruiter in the UI).
SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
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
) -> CreatedEvent:
    """Creates a Calendar event with an auto-generated Google Meet link and
    invites `attendee_emails` — Calendar sends its own invite email to each
    attendee (sendUpdates="all"), which is the "auto pesan ke Gmail mereka"
    behavior; no separate Gmail API send needed."""
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
            .insert(calendarId="primary", body=body, conferenceDataVersion=1, sendUpdates="all")
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
