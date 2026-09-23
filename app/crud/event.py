from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.event import Event, generate_invite_token
from app.models.invitation import Invitation, InvitationStatus
from app.schemas.event import EventCreate


def create_event(db: Session, event_in: EventCreate, owner_id: int) -> Event:
    event = Event(**event_in.model_dump(), owner_id=owner_id)
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def get_event(db: Session, event_id: int) -> Event | None:
    return db.get(Event, event_id)


def get_event_by_token(db: Session, invite_token: str) -> Event | None:
    return db.scalar(select(Event).where(Event.invite_token == invite_token))


def list_events_for_user(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> list[Event]:
    joined_event_ids = select(Invitation.event_id).where(
        Invitation.invitee_id == user_id, Invitation.status == InvitationStatus.ACCEPTED
    )
    stmt = (
        select(Event)
        .where((Event.owner_id == user_id) | (Event.id.in_(joined_event_ids)))
        .offset(skip)
        .limit(limit)
    )
    return list(db.scalars(stmt))


def can_view_event(db: Session, event: Event, user_id: int) -> bool:
    if event.owner_id == user_id:
        return True
    invitation = db.scalar(
        select(Invitation).where(
            Invitation.event_id == event.id,
            Invitation.invitee_id == user_id,
            Invitation.status == InvitationStatus.ACCEPTED,
        )
    )
    return invitation is not None


def is_registration_open(event: Event) -> bool:
    if event.registration_deadline_minutes_before is None:
        return True
    deadline = event.starts_at - timedelta(minutes=event.registration_deadline_minutes_before)
    return datetime.now(timezone.utc) < deadline


def regenerate_invite_token(db: Session, event: Event) -> Event:
    event.invite_token = generate_invite_token()
    db.commit()
    db.refresh(event)
    return event


def delete_event(db: Session, event: Event) -> None:
    db.delete(event)
    db.commit()
