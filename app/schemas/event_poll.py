from datetime import datetime, timezone

from pydantic import BaseModel, Field, model_validator


class EventPollCreate(BaseModel):
    title: str
    description: str | None = None
    location: str | None = None
    location_details: str | None = None
    maps_link: str | None = None
    duration_minutes: int = Field(gt=0)
    date_options: list[datetime] = Field(min_length=2)

    @model_validator(mode="after")
    def validate_date_options(self) -> "EventPollCreate":
        now = datetime.now(timezone.utc)
        if any(option <= now for option in self.date_options):
            raise ValueError("date_options must all be in the future")
        if len(set(self.date_options)) != len(self.date_options):
            raise ValueError("date_options must not contain duplicates")
        return self


class EventPollVoterRead(BaseModel):
    user_id: int
    full_name: str
    avatar_url: str | None = None


class EventPollDateOptionRead(BaseModel):
    id: int
    starts_at: datetime
    voters: list[EventPollVoterRead]
    voted_by_me: bool


class EventPollRead(BaseModel):
    id: int
    title: str
    description: str | None
    location: str | None
    location_details: str | None
    maps_link: str | None
    duration_minutes: int
    owner_id: int
    owner_name: str
    resulting_event_id: int | None
    date_options: list[EventPollDateOptionRead]
    created_at: datetime


class EventPollDateOptionPreview(BaseModel):
    id: int
    starts_at: datetime
    vote_count: int


class EventPollInvitePreview(BaseModel):
    id: int
    title: str
    description: str | None
    location: str | None
    location_details: str | None
    maps_link: str | None
    duration_minutes: int
    owner_id: int
    date_options: list[EventPollDateOptionPreview]


class EventPollInviteLink(BaseModel):
    invite_token: str


class PollDateVotesInput(BaseModel):
    option_ids: list[int]


class EventPollResolve(BaseModel):
    resulting_event_id: int
    date_option_id: int
