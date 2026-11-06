from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

# Codes, not sentences: the frontend turns them into text in the user's language.
Warning = Literal["default_time", "estimated_time", "past_dates_dropped", "no_dates", "too_many_dates"]


class PlanDraftRequest(BaseModel):
    text: str = Field(min_length=1, max_length=600)
    # IANA name from the browser (Intl.DateTimeFormat().resolvedOptions().timeZone); anything unknown falls back.
    timezone: str | None = Field(default=None, max_length=64)

    @field_validator("text")
    @classmethod
    def strip_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("text must not be blank")
        return value


class PlanDraft(BaseModel):
    """A suggestion to prefill the create-event or create-poll form. Nothing is saved from it."""

    kind: Literal["event", "poll"]
    title: str
    description: str | None = None
    location: str | None = None
    duration_minutes: int
    max_attendees: int | None = None
    # UTC, ascending. One date means an event; two or more mean a poll.
    dates: list[datetime]
    warnings: list[Warning] = []
