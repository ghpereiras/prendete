from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud
from app.auth import get_current_user
from app.database import get_db
from app.models.invitation import InvitationStatus
from app.models.user import User
from app.schemas.invitation import InvitationRead, InvitationUpdate

router = APIRouter(tags=["invitations"])


@router.post("/events/invite/{invite_token}/join", response_model=InvitationRead, status_code=201)
def join_event(
    invite_token: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    event = crud.event.get_event_by_token(db, invite_token)
    if not event:
        raise HTTPException(status_code=404, detail="Invalid invite link")

    existing = crud.invitation.get_invitation_for_user(db, event.id, current_user.id)
    if existing and existing.status == InvitationStatus.ACCEPTED:
        raise HTTPException(status_code=409, detail="You already joined this event")

    if crud.invitation.count_accepted(db, event.id) >= event.max_attendees:
        raise HTTPException(status_code=409, detail="This event is full")

    if existing:
        return crud.invitation.update_invitation_status(db, existing, InvitationStatus.ACCEPTED)
    return crud.invitation.create_accepted_invitation(db, event.id, current_user.id)


@router.get("/events/{event_id}/invitations", response_model=list[InvitationRead])
def list_invitations(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    event = crud.event.get_event(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if event.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the event owner can view invitations")
    return crud.invitation.list_invitations_for_event(db, event_id)


@router.patch("/invitations/{invitation_id}", response_model=InvitationRead)
def update_invitation(
    invitation_id: int,
    invitation_in: InvitationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    invitation = crud.invitation.get_invitation(db, invitation_id)
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")
    if invitation.invitee_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the invitee can respond to this invitation")

    if invitation_in.status == InvitationStatus.ACCEPTED and invitation.status != InvitationStatus.ACCEPTED:
        event = crud.event.get_event(db, invitation.event_id)
        if crud.invitation.count_accepted(db, invitation.event_id) >= event.max_attendees:
            raise HTTPException(status_code=409, detail="This event is full")

    return crud.invitation.update_invitation_status(db, invitation, invitation_in.status)
