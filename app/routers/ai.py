import logging
import time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, llm, plan_draft
from app.auth import get_current_user
from app.config import settings
from app.database import get_db
from app.models.user import User
from app.schemas.ai import PlanDraft, PlanDraftRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/plan-draft", response_model=PlanDraft)
def create_plan_draft(
    body: PlanDraftRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not settings.bedrock_model_id:
        raise HTTPException(status_code=503, detail="ai_unavailable")

    # The limits are the spending ceiling, so they are checked before the model is ever called.
    if crud.ai_request.count_for_user(db, current_user.id) >= settings.ai_daily_limit_per_user:
        raise HTTPException(status_code=429, detail="ai_limit_reached")
    if crud.ai_request.count_all(db) >= settings.ai_daily_limit_global:
        raise HTTPException(status_code=429, detail="ai_busy")

    started = time.monotonic()
    try:
        draft, usage = plan_draft.generate(body.text, tz_name=body.timezone)
    except (llm.LlmError, plan_draft.DraftError) as exc:
        # A failed call still counts against the limit, so a retry loop cannot run up the bill.
        crud.ai_request.record(db, current_user.id, ok=False, latency_ms=int((time.monotonic() - started) * 1000))
        logger.warning("AI plan draft failed for user %s: %s", current_user.id, exc)
        raise HTTPException(status_code=502, detail="ai_failed")

    crud.ai_request.record(
        db,
        current_user.id,
        ok=True,
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        latency_ms=usage.latency_ms,
    )
    logger.info(
        "AI plan draft user=%s kind=%s dates=%s in=%s out=%s latency_ms=%s",
        current_user.id, draft.kind, len(draft.dates), usage.input_tokens, usage.output_tokens, usage.latency_ms,
    )
    return draft
