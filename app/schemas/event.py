from datetime import datetime, timedelta, timezone

from pydantic import BaseModel, ConfigDict, Field, model_validator


class EventCreate(BaseModel):
    title: str
    description: str | None = None
    location: str | None = None
    location_details: str | None = None
    maps_link: str | None = None
    starts_at: datetime
    duration_minutes: int = Field(gt=0)
    registration_deadline_minutes_before: int | None = Field(default=None, gt=0)
    max_attendees: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_start_and_registration_window(self) -> "EventCreate":
        now = datetime.now(timezone.utc)
        if self.starts_at <= now:
            raise ValueError("starts_at must be in the future")

        minutes_before = self.registration_deadline_minutes_before or 0
        deadline = self.starts_at - timedelta(minutes=minutes_before)
        if deadline <= now:
            raise ValueError(
                "registration_deadline_minutes_before would already be closed at creation time"
            )
        return self


class EventUpdate(EventCreate):
    notify_attendees: bool = True


class EventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    location: str | None
    location_details: str | None
    maps_link: str | None
    starts_at: datetime
    duration_minutes: int
    registration_deadline_minutes_before: int | None
    max_attendees: int
    owner_id: int
    owner_name: str
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
    duration_minutes: int
    registration_deadline_minutes_before: int | None
    max_attendees: int
    spots_left: int
    registration_open: bool
    owner_id: int


class EventAttendee(BaseModel):
    user_id: int
    full_name: str
    email: str
    avatar_url: str | None = None
    is_owner: bool
    comment: str | None = None
