import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.email_verification_token import EmailVerificationToken

TOKEN_TTL = timedelta(days=7)


def create_token(db: Session, user_id: int) -> EmailVerificationToken:
    # Only one outstanding token makes sense per user — drop older ones so a
    # stale link in an earlier email can't be used once a newer one exists.
    db.query(EmailVerificationToken).filter(EmailVerificationToken.user_id == user_id).delete()

    token = EmailVerificationToken(
        user_id=user_id,
        token=secrets.token_urlsafe(32),
        expires_at=datetime.now(timezone.utc) + TOKEN_TTL,
    )
    db.add(token)
    db.commit()
    db.refresh(token)
    return token


def get_valid_by_token(db: Session, token: str) -> EmailVerificationToken | None:
    record = db.scalar(select(EmailVerificationToken).where(EmailVerificationToken.token == token))
    if record is None or record.expires_at < datetime.now(timezone.utc):
        return None
    return record
