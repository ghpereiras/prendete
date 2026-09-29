from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud
from app.auth import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.attendee import AttendanceUpdate, AttendeeRead, JoinInput
from app.schemas.event import EventAttendee

router = APIRouter(tags=["attendees"])


@router.post("/events/invite/{invite_token}/join", response_model=AttendeeRead, status_code=201)
def join_event(
    invite_token: str,
    join_in: JoinInput | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    event = crud.event.get_event_by_token(db, invite_token)
    if not event:
        raise HTTPException(status_code=404, detail="Invalid invite link")

    if event.owner_id == current_user.id:
        raise HTTPException(status_code=409, detail="You're the owner of this event")

    if crud.attendee.get_attendee(db, event.id, current_user.id):
        raise HTTPException(status_code=409, detail="You already joined this event")

    if not crud.event.is_registration_open(event):
        raise HTTPException(status_code=409, detail="Registration for this event is closed")

    if event.max_attendees is not None and crud.attendee.count_attendees(db, event.id) >= event.max_attendees:
        raise HTTPException(status_code=409, detail="This event is full")

    comment = join_in.comment if join_in else None
    return crud.attendee.add_attendee(db, event.id, current_user.id, comment=comment)


@router.patch("/events/{event_id}/attendance", response_model=AttendeeRead)
def update_attendance(
    event_id: int,
    update_in: AttendanceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attendee = crud.attendee.get_attendee(db, event_id, current_user.id)
    if not attendee:
        raise HTTPException(status_code=404, detail="You're not attending this event")
    return crud.attendee.update_comment(db, attendee, update_in.comment)


@router.delete("/events/{event_id}/attendance", status_code=204)
def leave_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    event = crud.event.get_event(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if event.owner_id == current_user.id:
        raise HTTPException(status_code=403, detail="Event owners can't leave their own event")

    attendee = crud.attendee.get_attendee(db, event_id, current_user.id)
    if not attendee:
        raise HTTPException(status_code=404, detail="You're not attending this event")
    crud.attendee.remove_attendee(db, attendee)


@router.get("/events/{event_id}/attendees", response_model=list[EventAttendee])
def list_attendees(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    event = crud.event.get_event(db, event_id)
    if not event or not crud.event.can_view_event(db, event, current_user.id):
        raise HTTPException(status_code=404, detail="Event not found")

    is_owner_viewing = current_user.id == event.owner_id

    attendees = [
        EventAttendee(
            user_id=event.owner.id,
            full_name=event.owner.full_name,
            email=event.owner.email,
            avatar_url=event.owner.avatar_url,
            is_owner=True,
        )
    ]
    attendees += [
        EventAttendee(
            user_id=attendee.user.id,
            full_name=attendee.user.full_name,
            email=attendee.user.email,
            avatar_url=attendee.user.avatar_url,
            is_owner=False,
            # Comments are only visible to the event owner and to their own author.
            comment=attendee.comment if (is_owner_viewing or attendee.user_id == current_user.id) else None,
        )
        for attendee in crud.attendee.list_attendees_for_event(db, event_id)
    ]
    return attendees
