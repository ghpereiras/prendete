from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.invitation import InvitationStatus


class InvitationJoinInput(BaseModel):
    comment: str | None = Field(default=None, max_length=500)


class InvitationUpdate(BaseModel):
    status: InvitationStatus
    comment: str | None = Field(default=None, max_length=500)


class InvitationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: int
    invitee_id: int
    status: InvitationStatus
    comment: str | None
    invited_at: datetime
    responded_at: datetime | None
