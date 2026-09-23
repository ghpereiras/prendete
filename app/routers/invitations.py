from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud
from app.auth import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.invitation import InvitationCreate, InvitationRead, InvitationUpdate

router = APIRouter(tags=["invitations"])


@router.post("/events/{event_id}/invitations", response_model=InvitationRead, status_code=201)
def create_invitation(
    event_id: int,
    invitation_in: InvitationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    event = crud.event.get_event(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if event.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the event owner can send invitations")
    if not crud.user.get_user(db, invitation_in.invitee_id):
        raise HTTPException(status_code=404, detail="Invitee not found")
    return crud.invitation.create_invitation(db, event_id, invitation_in)


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
    return crud.invitation.update_invitation_status(db, invitation, invitation_in.status)
