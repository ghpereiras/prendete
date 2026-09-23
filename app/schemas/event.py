from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class EventCreate(BaseModel):
    title: str
    description: str | None = None
    location: str | None = None
    location_details: str | None = None
    maps_link: str | None = None
    starts_at: datetime
    ends_at: datetime
    max_attendees: int = Field(gt=0)


class EventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    location: str | None
    location_details: str | None
    maps_link: str | None
    starts_at: datetime
    ends_at: datetime
    max_attendees: int
    owner_id: int
    created_at: datetime


class EventInviteLink(BaseModel):
    invite_token: str


class EventInvitePreview(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    location: str | None
    location_details: str | None
    maps_link: str | None
    starts_at: datetime
    ends_at: datetime
    max_attendees: int
    spots_left: int


class EventAttendee(BaseModel):
    user_id: int
    full_name: str
    email: str
    is_owner: bool
