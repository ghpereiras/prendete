from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.event_poll import EventPoll, EventPollDateOption, EventPollVote, generate_invite_token
from app.schemas.event_poll import EventPollCreate, EventPollUpdate

_LOAD_OPTIONS = (
    joinedload(EventPoll.owner),
    joinedload(EventPoll.date_options).joinedload(EventPollDateOption.votes).joinedload(EventPollVote.user),
)


def create_poll(db: Session, poll_in: EventPollCreate, owner_id: int) -> EventPoll:
    poll = EventPoll(
        title=poll_in.title,
        description=poll_in.description,
        location=poll_in.location,
        location_details=poll_in.location_details,
        maps_link=poll_in.maps_link,
        duration_minutes=poll_in.duration_minutes,
        owner_id=owner_id,
        date_options=[EventPollDateOption(starts_at=starts_at) for starts_at in poll_in.date_options],
    )
    db.add(poll)
    db.commit()
    return get_poll(db, poll.id)  # type: ignore[return-value]


def update_poll(db: Session, poll: EventPoll, poll_in: EventPollUpdate) -> EventPoll:
    poll.title = poll_in.title
    poll.description = poll_in.description
    poll.location = poll_in.location
    poll.location_details = poll_in.location_details
    poll.maps_link = poll_in.maps_link
    poll.duration_minutes = poll_in.duration_minutes

    # A date that is kept (same instant) keeps its votes; one that is dropped takes its votes with
    # it (delete-orphan cascade); a new one starts empty. Changing a date is therefore a drop + add.
    wanted = set(poll_in.date_options)
    for option in list(poll.date_options):
        if option.starts_at in wanted:
            wanted.discard(option.starts_at)
        else:
            poll.date_options.remove(option)
    for starts_at in wanted:
        poll.date_options.append(EventPollDateOption(starts_at=starts_at))

    db.commit()
    return get_poll(db, poll.id)  # type: ignore[return-value]


def delete_poll(db: Session, poll: EventPoll) -> None:
    db.delete(poll)
    db.commit()


def get_poll(db: Session, poll_id: int) -> EventPoll | None:
    stmt = select(EventPoll).options(*_LOAD_OPTIONS).where(EventPoll.id == poll_id)
    return db.scalar(stmt)


def get_poll_by_token(db: Session, invite_token: str) -> EventPoll | None:
    stmt = select(EventPoll).options(*_LOAD_OPTIONS).where(EventPoll.invite_token == invite_token)
    return db.scalar(stmt)


def list_polls_for_user(db: Session, user_id: int) -> list[EventPoll]:
    voted_poll_ids = (
        select(EventPollDateOption.poll_id)
        .join(EventPollVote, EventPollVote.date_option_id == EventPollDateOption.id)
        .where(EventPollVote.user_id == user_id)
    )
    stmt = (
        select(EventPoll)
        .options(*_LOAD_OPTIONS)
        .where(
            EventPoll.resulting_event_id.is_(None),
            (EventPoll.owner_id == user_id) | (EventPoll.id.in_(voted_poll_ids)),
        )
        .order_by(EventPoll.created_at.desc())
    )
    return list(db.scalars(stmt).unique())


def can_view_poll(db: Session, poll: EventPoll, user_id: int) -> bool:
    if poll.owner_id == user_id:
        return True
    vote = db.scalar(
        select(EventPollVote)
        .join(EventPollDateOption, EventPollVote.date_option_id == EventPollDateOption.id)
        .where(EventPollDateOption.poll_id == poll.id, EventPollVote.user_id == user_id)
    )
    return vote is not None


def regenerate_invite_token(db: Session, poll: EventPoll) -> EventPoll:
    poll.invite_token = generate_invite_token()
    db.commit()
    db.refresh(poll)
    return poll


def set_user_votes(db: Session, poll: EventPoll, user_id: int, option_ids: list[int]) -> EventPoll:
    valid_option_ids = {option.id for option in poll.date_options}
    if not set(option_ids).issubset(valid_option_ids):
        raise ValueError("option_ids must belong to this poll")

    db.query(EventPollVote).where(
        EventPollVote.user_id == user_id,
        EventPollVote.date_option_id.in_(valid_option_ids),
    ).delete(synchronize_session=False)
    for option_id in option_ids:
        db.add(EventPollVote(date_option_id=option_id, user_id=user_id))
    db.commit()
    return get_poll(db, poll.id)  # type: ignore[return-value]


def resolve_poll(db: Session, poll: EventPoll, resulting_event_id: int, date_option_id: int) -> EventPoll:
    poll.resulting_event_id = resulting_event_id
    poll.resolved_date_option_id = date_option_id
    db.commit()
    db.refresh(poll)
    return poll
