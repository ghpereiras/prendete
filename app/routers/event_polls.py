from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, push
from app.auth import get_current_user, get_optional_user
from app.database import get_db
from app.models.event_poll import EventPoll
from app.models.user import User
from app.schemas.event_poll import (
    EventPollCreate,
    EventPollDateOptionPreview,
    EventPollDateOptionRead,
    EventPollInviteLink,
    EventPollInvitePreview,
    EventPollRead,
    EventPollResolve,
    EventPollVoterRead,
    PollDateVotesInput,
)

router = APIRouter(prefix="/event-polls", tags=["event-polls"])


def _build_voters(option) -> list[EventPollVoterRead]:
    return [
        EventPollVoterRead(
            user_id=vote.user.id,
            full_name=vote.user.full_name,
            avatar_url=vote.user.avatar_url,
        )
        for vote in option.votes
    ]


def _build_poll_read(poll: EventPoll, viewer_id: int) -> EventPollRead:
    return EventPollRead(
        id=poll.id,
        title=poll.title,
        description=poll.description,
        location=poll.location,
        location_details=poll.location_details,
        maps_link=poll.maps_link,
        duration_minutes=poll.duration_minutes,
        owner_id=poll.owner_id,
        owner_name=poll.owner_name,
        resulting_event_id=poll.resulting_event_id,
        created_at=poll.created_at,
        date_options=[
            EventPollDateOptionRead(
                id=option.id,
                starts_at=option.starts_at,
                voters=_build_voters(option),
                voted_by_me=any(vote.user_id == viewer_id for vote in option.votes),
            )
            for option in poll.date_options
        ],
    )


@router.post("", response_model=EventPollRead, status_code=201)
def create_poll(
    poll_in: EventPollCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    poll = crud.event_poll.create_poll(db, poll_in, owner_id=current_user.id)
    return _build_poll_read(poll, current_user.id)


@router.get("", response_model=list[EventPollRead])
def list_polls(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    polls = crud.event_poll.list_polls_for_user(db, current_user.id)
    return [_build_poll_read(poll, current_user.id) for poll in polls]


@router.get("/invite/{invite_token}", response_model=EventPollInvitePreview)
def preview_invite(
    invite_token: str,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    poll = crud.event_poll.get_poll_by_token(db, invite_token)
    if not poll or poll.is_resolved:
        raise HTTPException(status_code=404, detail="Invalid invite link")
    return EventPollInvitePreview(
        id=poll.id,
        title=poll.title,
        description=poll.description,
        location=poll.location,
        location_details=poll.location_details,
        maps_link=poll.maps_link,
        duration_minutes=poll.duration_minutes,
        owner_id=poll.owner_id,
        date_options=[
            EventPollDateOptionPreview(
                id=option.id,
                starts_at=option.starts_at,
                vote_count=len(option.votes),
                voters=_build_voters(option) if current_user else [],
            )
            for option in poll.date_options
        ],
    )


@router.post("/invite/{invite_token}/vote", response_model=EventPollRead)
def vote_by_invite(
    invite_token: str,
    votes_in: PollDateVotesInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    poll = crud.event_poll.get_poll_by_token(db, invite_token)
    if not poll or poll.is_resolved:
        raise HTTPException(status_code=404, detail="Invalid invite link")
    try:
        poll = crud.event_poll.set_user_votes(db, poll, current_user.id, votes_in.option_ids)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return _build_poll_read(poll, current_user.id)


@router.get("/{poll_id}", response_model=EventPollRead)
def get_poll(
    poll_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    poll = crud.event_poll.get_poll(db, poll_id)
    if not poll or not crud.event_poll.can_view_poll(db, poll, current_user.id):
        raise HTTPException(status_code=404, detail="Poll not found")
    return _build_poll_read(poll, current_user.id)


@router.get("/{poll_id}/invite-link", response_model=EventPollInviteLink)
def get_invite_link(
    poll_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    poll = crud.event_poll.get_poll(db, poll_id)
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")
    if poll.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the poll owner can view the invite link")
    return EventPollInviteLink(invite_token=poll.invite_token)


@router.post("/{poll_id}/invite-link/regenerate", response_model=EventPollInviteLink)
def regenerate_invite_link(
    poll_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    poll = crud.event_poll.get_poll(db, poll_id)
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")
    if poll.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the poll owner can regenerate the invite link")
    poll = crud.event_poll.regenerate_invite_token(db, poll)
    return EventPollInviteLink(invite_token=poll.invite_token)


@router.put("/{poll_id}/date-options/votes", response_model=EventPollRead)
def update_votes(
    poll_id: int,
    votes_in: PollDateVotesInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    poll = crud.event_poll.get_poll(db, poll_id)
    if not poll or not crud.event_poll.can_view_poll(db, poll, current_user.id):
        raise HTTPException(status_code=404, detail="Poll not found")
    if poll.is_resolved:
        raise HTTPException(status_code=409, detail="This poll was already resolved")
    try:
        poll = crud.event_poll.set_user_votes(db, poll, current_user.id, votes_in.option_ids)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return _build_poll_read(poll, current_user.id)


@router.post("/{poll_id}/resolve", response_model=EventPollRead)
def resolve_poll(
    poll_id: int,
    resolve_in: EventPollResolve,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    poll = crud.event_poll.get_poll(db, poll_id)
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")
    if poll.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the poll owner can resolve this poll")
    if poll.is_resolved:
        raise HTTPException(status_code=409, detail="This poll was already resolved")

    resulting_event = crud.event.get_event(db, resolve_in.resulting_event_id)
    if not resulting_event or resulting_event.owner_id != current_user.id:
        raise HTTPException(status_code=422, detail="resulting_event_id must be an event you own")
    chosen_option = next(
        (option for option in poll.date_options if option.id == resolve_in.date_option_id), None
    )
    if not chosen_option:
        raise HTTPException(status_code=422, detail="date_option_id must belong to this poll")

    for vote in chosen_option.votes:
        if vote.user_id == resulting_event.owner_id:
            continue
        crud.attendee.add_attendee(db, resulting_event.id, vote.user_id)

    poll = crud.event_poll.resolve_poll(db, poll, resolve_in.resulting_event_id, resolve_in.date_option_id)

    voter_ids = {
        vote.user_id
        for option in poll.date_options
        for vote in option.votes
        if vote.user_id != resulting_event.owner_id
    }
    push.send_localized_push_to_users(
        db,
        voter_ids,
        "poll_resolved",
        f"/events/{resulting_event.id}",
        title=resulting_event.title,
        date=chosen_option.starts_at,
    )
    return _build_poll_read(poll, current_user.id)
