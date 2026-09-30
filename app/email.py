import logging

import httpx
from sqlalchemy.orm import Session

from app import crud, email_messages
from app.config import settings
from app.models.user import User

logger = logging.getLogger(__name__)

BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


def send_email(to: str, subject: str, html_body: str, text_body: str) -> None:
    try:
        response = httpx.post(
            BREVO_API_URL,
            headers={"api-key": settings.brevo_api_key, "Accept": "application/json"},
            json={
                "sender": {"name": settings.email_from_name, "email": settings.email_from_address},
                "to": [{"email": to}],
                "subject": subject,
                "htmlContent": html_body,
                # A plain-text alternative alongside the HTML part is a basic
                # deliverability signal — html-only mail is more likely to be
                # flagged as spam, especially from a brand-new sending domain.
                "textContent": text_body,
            },
            timeout=10,
        )
        response.raise_for_status()
    except Exception:
        # Same reasoning as send_push_to_user: this talks to a third-party
        # service over the network, and a delivery failure here must not
        # bubble up into the caller's HTTP response.
        logger.exception("Email send failed for %s", to)


def send_verification_email(db: Session, user: User, language: str | None = None) -> None:
    # `language` is the page's language right now (if the caller has it) —
    # preferred over the account's saved language, which may be stale.
    token = crud.email_verification_token.create_token(db, user.id)
    link = f"{settings.frontend_url}/verify-email/{token.token}"
    message = email_messages.build_message(
        "email_verification", language or user.language, first_name=user.first_name, link=link
    )
    send_email(user.email, message["subject"], message["html"], message["text"])


def send_password_reset_email(db: Session, user: User, language: str | None = None) -> None:
    token = crud.password_reset_token.create_token(db, user.id)
    link = f"{settings.frontend_url}/reset-password/{token.token}"
    message = email_messages.build_message(
        "password_reset", language or user.language, first_name=user.first_name, link=link
    )
    send_email(user.email, message["subject"], message["html"], message["text"])
