from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.invitation import Invitation, InvitationStatus


def get_invitation(db: Session, invitation_id: int) -> Invitation | None:
    return db.get(Invitation, invitation_id)


def get_invitation_for_user(db: Session, event_id: int, invitee_id: int) -> Invitation | None:
    return db.scalar(
        select(Invitation).where(Invitation.event_id == event_id, Invitation.invitee_id == invitee_id)
    )


def list_invitations_for_event(db: Session, event_id: int) -> list[Invitation]:
    return list(db.scalars(select(Invitation).where(Invitation.event_id == event_id)))


def list_accepted_invitees(db: Session, event_id: int) -> list[Invitation]:
    stmt = (
        select(Invitation)
        .options(joinedload(Invitation.invitee))
        .where(Invitation.event_id == event_id, Invitation.status == InvitationStatus.ACCEPTED)
        .order_by(Invitation.responded_at)
    )
    return list(db.scalars(stmt))


def count_accepted(db: Session, event_id: int, exclude_user_id: int | None = None) -> int:
    stmt = (
        select(func.count())
        .select_from(Invitation)
        .where(Invitation.event_id == event_id, Invitation.status == InvitationStatus.ACCEPTED)
    )
    if exclude_user_id is not None:
        stmt = stmt.where(Invitation.invitee_id != exclude_user_id)
    return db.scalar(stmt) or 0


def create_accepted_invitation(db: Session, event_id: int, invitee_id: int) -> Invitation:
    invitation = Invitation(
        event_id=event_id,
        invitee_id=invitee_id,
        status=InvitationStatus.ACCEPTED,
        responded_at=datetime.now(timezone.utc),
    )
    db.add(invitation)
    db.commit()
    db.refresh(invitation)
    return invitation


def update_invitation_status(db: Session, invitation: Invitation, status: InvitationStatus) -> Invitation:
    invitation.status = status
    invitation.responded_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(invitation)
    return invitation
