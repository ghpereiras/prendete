from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.attendee import Attendee


def get_attendee(db: Session, event_id: int, user_id: int) -> Attendee | None:
    return db.scalar(select(Attendee).where(Attendee.event_id == event_id, Attendee.user_id == user_id))


def list_attendees_for_event(db: Session, event_id: int) -> list[Attendee]:
    stmt = (
        select(Attendee)
        .options(joinedload(Attendee.user))
        .where(Attendee.event_id == event_id)
        .order_by(Attendee.joined_at)
    )
    return list(db.scalars(stmt))


def count_attendees(db: Session, event_id: int) -> int:
    stmt = select(func.count()).select_from(Attendee).where(Attendee.event_id == event_id)
    return db.scalar(stmt) or 0


def add_attendee(db: Session, event_id: int, user_id: int, comment: str | None = None) -> Attendee:
    attendee = Attendee(event_id=event_id, user_id=user_id, comment=comment)
    db.add(attendee)
    db.commit()
    db.refresh(attendee)
    return attendee


def update_comment(db: Session, attendee: Attendee, comment: str | None) -> Attendee:
    attendee.comment = comment
    db.commit()
    db.refresh(attendee)
    return attendee


def remove_attendee(db: Session, attendee: Attendee) -> None:
    db.delete(attendee)
    db.commit()
