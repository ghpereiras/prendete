from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class JoinInput(BaseModel):
    comment: str | None = Field(default=None, max_length=500)


class AttendanceUpdate(BaseModel):
    comment: str | None = Field(default=None, max_length=500)


class AttendeeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: int
    user_id: int
    comment: str | None
    joined_at: datetime
