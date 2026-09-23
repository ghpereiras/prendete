from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EventCreate(BaseModel):
    title: str
    description: str | None = None
    location: str | None = None
    starts_at: datetime
    ends_at: datetime


class EventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    location: str | None
    starts_at: datetime
    ends_at: datetime
    owner_id: int
    created_at: datetime
