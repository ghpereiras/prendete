import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.password_reset_token import PasswordResetToken

TOKEN_TTL = timedelta(hours=1)


def create_token(db: Session, user_id: int) -> PasswordResetToken:
    token = PasswordResetToken(
        user_id=user_id,
        token=secrets.token_urlsafe(32),
        expires_at=datetime.now(timezone.utc) + TOKEN_TTL,
    )
    db.add(token)
    db.commit()
    db.refresh(token)
    return token


def get_valid_by_token(db: Session, token: str) -> PasswordResetToken | None:
    record = db.scalar(select(PasswordResetToken).where(PasswordResetToken.token == token))
    if record is None or record.used_at is not None or record.expires_at < datetime.now(timezone.utc):
        return None
    return record


def mark_used(db: Session, token: PasswordResetToken) -> None:
    token.used_at = datetime.now(timezone.utc)
    db.commit()
