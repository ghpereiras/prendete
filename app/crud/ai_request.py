from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.ai_request import AiRequest

WINDOW = timedelta(hours=24)


def _since() -> datetime:
    return datetime.now(timezone.utc) - WINDOW


def count_for_user(db: Session, user_id: int) -> int:
    return db.scalar(
        select(func.count()).select_from(AiRequest).where(AiRequest.user_id == user_id, AiRequest.created_at >= _since())
    ) or 0


def count_all(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(AiRequest).where(AiRequest.created_at >= _since())) or 0


def record(
    db: Session,
    user_id: int,
    *,
    ok: bool,
    input_tokens: int = 0,
    output_tokens: int = 0,
    latency_ms: int = 0,
    kind: str = "plan_draft",
) -> AiRequest:
    row = AiRequest(
        user_id=user_id,
        kind=kind,
        ok=ok,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        latency_ms=latency_ms,
    )
    db.add(row)
    db.commit()
    return row
