from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.invitation import Invitation, InvitationStatus
from app.schemas.invitation import InvitationCreate


def create_invitation(db: Session, event_id: int, invitation_in: InvitationCreate) -> Invitation:
    invitation = Invitation(event_id=event_id, invitee_id=invitation_in.invitee_id)
    db.add(invitation)
    db.commit()
    db.refresh(invitation)
    return invitation


def get_invitation(db: Session, invitation_id: int) -> Invitation | None:
    return db.get(Invitation, invitation_id)


def list_invitations_for_event(db: Session, event_id: int) -> list[Invitation]:
    return list(db.scalars(select(Invitation).where(Invitation.event_id == event_id)))


def update_invitation_status(db: Session, invitation: Invitation, status: InvitationStatus) -> Invitation:
    invitation.status = status
    invitation.responded_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(invitation)
    return invitation
