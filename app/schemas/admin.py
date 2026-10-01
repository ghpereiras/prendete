from datetime import date, datetime

from pydantic import BaseModel


class WindowCounts(BaseModel):
    total: int
    last_24h: int
    last_7d: int
    last_30d: int


class DailyCount(BaseModel):
    date: date
    count: int


class RecentSignup(BaseModel):
    id: int
    full_name: str
    email: str
    created_at: datetime
    # "google" = no password set (assumed to have signed up through Google).
    login_method: str
    email_verified: bool


class UserStats(BaseModel):
    registered: WindowCounts
    active: WindowCounts
    with_password: int
    google_only: int
    email_verified: int
    email_unverified: int
    locked_out: int
    with_avatar: int
    with_push: int
    language_es: int
    language_en: int
    never_engaged: int
    signups_by_day: list[DailyCount]
    recent_signups: list[RecentSignup]


class EventStats(BaseModel):
    created: WindowCounts
    upcoming: int
    past: int
    limited_capacity: int
    avg_attendees: float


class PollStats(BaseModel):
    created: WindowCounts
    open: int
    resolved: int
    avg_participants: float


class AdminStats(BaseModel):
    generated_at: datetime
    users: UserStats
    events: EventStats
    polls: PollStats
    attendances: WindowCounts
