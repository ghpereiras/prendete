from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, push
from app.auth import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.event import EventCreate, EventInviteLink, EventInvitePreview, EventRead, EventUpdate

router = APIRouter(prefix="/events", tags=["events"])


@router.post("", response_model=EventRead, status_code=201)
def create_event(
    event_in: EventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud.event.create_event(db, event_in, owner_id=current_user.id)


@router.get("", response_model=list[EventRead])
def list_events(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud.event.list_events_for_user(db, current_user.id, skip, limit)


@router.get("/invite/{invite_token}", response_model=EventInvitePreview)
def preview_invite(invite_token: str, db: Session = Depends(get_db)):
    event = crud.event.get_event_by_token(db, invite_token)
    if not event:
        raise HTTPException(status_code=404, detail="Invalid invite link")
    accepted = crud.attendee.count_attendees(db, event.id)
    return EventInvitePreview(
        id=event.id,
        title=event.title,
        description=event.description,
        location=event.location,
        location_details=event.location_details,
        maps_link=event.maps_link,
        starts_at=event.starts_at,
        duration_minutes=event.duration_minutes,
        registration_deadline_minutes_before=event.registration_deadline_minutes_before,
        max_attendees=event.max_attendees,
        spots_left=None if event.max_attendees is None else max(event.max_attendees - accepted, 0),
        registration_open=crud.event.is_registration_open(event),
        owner_id=event.owner_id,
    )


@router.get("/{event_id}", response_model=EventRead)
def get_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    event = crud.event.get_event(db, event_id)
    if not event or not crud.event.can_view_event(db, event, current_user.id):
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.get("/{event_id}/invite-link", response_model=EventInviteLink)
def get_invite_link(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    event = crud.event.get_event(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if event.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the event owner can view the invite link")
    return EventInviteLink(invite_token=event.invite_token)


@router.post("/{event_id}/invite-link/regenerate", response_model=EventInviteLink)
def regenerate_invite_link(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    event = crud.event.get_event(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if event.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the event owner can regenerate the invite link")
    event = crud.event.regenerate_invite_token(db, event)
    return EventInviteLink(invite_token=event.invite_token)


@router.patch("/{event_id}", response_model=EventRead)
def update_event(
    event_id: int,
    event_in: EventUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    event = crud.event.get_event(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if event.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the event owner can edit this event")
    if event.starts_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=403, detail="Cannot edit an event that already happened")

    accepted = crud.attendee.count_attendees(db, event.id)
    if event_in.max_attendees is not None and event_in.max_attendees < accepted:
        raise HTTPException(
            status_code=422,
            detail="max_attendees cannot be lower than the number of already accepted attendees",
        )

    attendee_user_ids = [a.user_id for a in crud.attendee.list_attendees_for_event(db, event.id)]
    updated_event = crud.event.update_event(db, event, event_in)
    if event_in.notify_attendees:
        push.send_localized_push_to_users(
            db,
            attendee_user_ids,
            "event_updated",
            f"/events/{updated_event.id}",
            title=updated_event.title,
        )
    return updated_event


@router.delete("/{event_id}", status_code=204)
def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    event = crud.event.get_event(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if event.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the event owner can delete this event")
    if event.starts_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=403, detail="Cannot delete an event that already happened")

    attendee_user_ids = [a.user_id for a in crud.attendee.list_attendees_for_event(db, event.id)]
    event_title = event.title
    crud.event.delete_event(db, event)
    push.send_localized_push_to_users(
        db, attendee_user_ids, "event_cancelled", "/events", title=event_title
    )
