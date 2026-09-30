import logging

import httpx
from sqlalchemy.orm import Session

from app import crud, email_messages
from app.config import settings
from app.models.user import User

logger = logging.getLogger(__name__)

BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


def send_email(to: str, subject: str, html_body: str) -> None:
    try:
        response = httpx.post(
            BREVO_API_URL,
            headers={"api-key": settings.brevo_api_key, "Accept": "application/json"},
            json={
                "sender": {"name": settings.email_from_name, "email": settings.email_from_address},
                "to": [{"email": to}],
                "subject": subject,
                "htmlContent": html_body,
            },
            timeout=10,
        )
        response.raise_for_status()
    except Exception:
        # Same reasoning as send_push_to_user: this talks to a third-party
        # service over the network, and a delivery failure here must not
        # bubble up into the caller's HTTP response.
        logger.exception("Email send failed for %s", to)


def send_verification_email(db: Session, user: User) -> None:
    token = crud.email_verification_token.create_token(db, user.id)
    link = f"{settings.frontend_url}/verify-email/{token.token}"
    message = email_messages.build_message(
        "email_verification", user.language, first_name=user.first_name, link=link
    )
    send_email(user.email, message["subject"], message["html"])


def send_password_reset_email(db: Session, user: User) -> None:
    token = crud.password_reset_token.create_token(db, user.id)
    link = f"{settings.frontend_url}/reset-password/{token.token}"
    message = email_messages.build_message(
        "password_reset", user.language, first_name=user.first_name, link=link
    )
    send_email(user.email, message["subject"], message["html"])
