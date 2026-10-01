from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import distinct, func, literal, select, union
from sqlalchemy.orm import Session

from app.auth import require_admin
from app.database import get_db
from app.models.attendee import Attendee
from app.models.event import Event
from app.models.event_poll import EventPoll, EventPollDateOption, EventPollVote
from app.models.push_subscription import PushSubscription
from app.models.user import User
from app.schemas.admin import (
    AdminStats,
    DailyCount,
    EventStats,
    PollStats,
    RecentSignup,
    UserStats,
    WindowCounts,
)

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])

EMAIL_VERIFICATION_GRACE_DAYS = 7
SIGNUPS_CHART_DAYS = 30
RECENT_SIGNUPS_LIMIT = 10
REPORT_TIMEZONE = "America/Argentina/Buenos_Aires"


def _window_counts(db: Session, created_at_column, now: datetime) -> WindowCounts:
    row = db.execute(
        select(
            func.count(),
            func.count().filter(created_at_column >= now - timedelta(days=1)),
            func.count().filter(created_at_column >= now - timedelta(days=7)),
            func.count().filter(created_at_column >= now - timedelta(days=30)),
        )
    ).one()
    return WindowCounts(total=row[0], last_24h=row[1], last_7d=row[2], last_30d=row[3])


def _activity_rows():
    """(user_id, happened_at) for everything a user can do in the app."""
    return union(
        select(Event.owner_id.label("user_id"), Event.created_at.label("at")),
        select(Attendee.user_id.label("user_id"), Attendee.joined_at.label("at")),
        select(EventPoll.owner_id.label("user_id"), EventPoll.created_at.label("at")),
        select(EventPollVote.user_id.label("user_id"), EventPollVote.created_at.label("at")),
    ).subquery()


def _active_users(db: Session, now: datetime) -> WindowCounts:
    activity = _activity_rows()

    def distinct_users_since(since: datetime | None) -> int:
        query = select(func.count(distinct(activity.c.user_id)))
        if since is not None:
            query = query.where(activity.c.at >= since)
        return db.scalar(query) or 0

    return WindowCounts(
        total=distinct_users_since(None),
        last_24h=distinct_users_since(now - timedelta(days=1)),
        last_7d=distinct_users_since(now - timedelta(days=7)),
        last_30d=distinct_users_since(now - timedelta(days=30)),
    )


def _signups_by_day(db: Session, now: datetime) -> list[DailyCount]:
    local_day = func.date_trunc("day", func.timezone(REPORT_TIMEZONE, User.created_at))
    rows = db.execute(
        select(local_day, func.count())
        .where(User.created_at >= now - timedelta(days=SIGNUPS_CHART_DAYS + 1))
        .group_by(local_day)
    ).all()
    counts = {row[0].date(): row[1] for row in rows}

    today = db.scalar(select(func.timezone(REPORT_TIMEZONE, literal(now)))).date()
    days = [today - timedelta(days=offset) for offset in range(SIGNUPS_CHART_DAYS - 1, -1, -1)]
    return [DailyCount(date=day, count=counts.get(day, 0)) for day in days]


def _user_stats(db: Session, now: datetime) -> UserStats:
    activity_user_ids = select(_activity_rows().c.user_id)
    row = db.execute(
        select(
            func.count().filter(User.hashed_password.is_not(None)),
            func.count().filter(User.hashed_password.is_(None)),
            func.count().filter(User.email_verified_at.is_not(None)),
            func.count().filter(User.email_verified_at.is_(None)),
            func.count().filter(
                User.email_verified_at.is_(None),
                User.created_at < now - timedelta(days=EMAIL_VERIFICATION_GRACE_DAYS),
            ),
            func.count().filter(User.avatar.is_not(None)),
            func.count().filter(User.language == "es"),
            func.count().filter(User.language == "en"),
            func.count().filter(User.id.not_in(activity_user_ids)),
        )
    ).one()
    with_push = db.scalar(select(func.count(distinct(PushSubscription.user_id)))) or 0

    recent = db.scalars(select(User).order_by(User.created_at.desc()).limit(RECENT_SIGNUPS_LIMIT))
    return UserStats(
        registered=_window_counts(db, User.created_at, now),
        active=_active_users(db, now),
        with_password=row[0],
        google_only=row[1],
        email_verified=row[2],
        email_unverified=row[3],
        locked_out=row[4],
        with_avatar=row[5],
        with_push=with_push,
        language_es=row[6],
        language_en=row[7],
        never_engaged=row[8],
        signups_by_day=_signups_by_day(db, now),
        recent_signups=[
            RecentSignup(
                id=user.id,
                full_name=user.full_name,
                email=user.email,
                created_at=user.created_at,
                login_method="password" if user.has_password else "google",
                email_verified=user.email_verified_at is not None,
            )
            for user in recent
        ],
    )


def _event_stats(db: Session, now: datetime) -> EventStats:
    row = db.execute(
        select(
            func.count().filter(Event.starts_at >= now),
            func.count().filter(Event.starts_at < now),
            func.count().filter(Event.max_attendees.is_not(None)),
            func.count(),
        )
    ).one()
    total_attendances = db.scalar(select(func.count()).select_from(Attendee)) or 0
    return EventStats(
        created=_window_counts(db, Event.created_at, now),
        upcoming=row[0],
        past=row[1],
        limited_capacity=row[2],
        avg_attendees=round(total_attendances / row[3], 1) if row[3] else 0.0,
    )


def _poll_stats(db: Session, now: datetime) -> PollStats:
    row = db.execute(
        select(
            func.count().filter(EventPoll.resulting_event_id.is_(None)),
            func.count().filter(EventPoll.resulting_event_id.is_not(None)),
            func.count(),
        )
    ).one()
    participations = db.scalar(
        select(func.count()).select_from(
            select(EventPollDateOption.poll_id, EventPollVote.user_id)
            .join(EventPollVote, EventPollVote.date_option_id == EventPollDateOption.id)
            .distinct()
            .subquery()
        )
    ) or 0
    return PollStats(
        created=_window_counts(db, EventPoll.created_at, now),
        open=row[0],
        resolved=row[1],
        avg_participants=round(participations / row[2], 1) if row[2] else 0.0,
    )


@router.get("/stats", response_model=AdminStats)
def get_stats(db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    return AdminStats(
        generated_at=now,
        users=_user_stats(db, now),
        events=_event_stats(db, now),
        polls=_poll_stats(db, now),
        attendances=_window_counts(db, Attendee.joined_at, now),
    )
