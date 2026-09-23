from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.invitation import InvitationStatus


class InvitationUpdate(BaseModel):
    status: InvitationStatus


class InvitationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: int
    invitee_id: int
    status: InvitationStatus
    invited_at: datetime
    responded_at: datetime | None
