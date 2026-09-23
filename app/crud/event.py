from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.event import Event
from app.schemas.event import EventCreate


def create_event(db: Session, event_in: EventCreate, owner_id: int) -> Event:
    event = Event(**event_in.model_dump(), owner_id=owner_id)
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def get_event(db: Session, event_id: int) -> Event | None:
    return db.get(Event, event_id)


def list_events(db: Session, skip: int = 0, limit: int = 100) -> list[Event]:
    return list(db.scalars(select(Event).offset(skip).limit(limit)))


def delete_event(db: Session, event: Event) -> None:
    db.delete(event)
    db.commit()
