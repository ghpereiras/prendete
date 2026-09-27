from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.push_subscription import PushSubscription
from app.schemas.push_subscription import PushSubscriptionCreate


def upsert_subscription(db: Session, user_id: int, sub_in: PushSubscriptionCreate) -> PushSubscription:
    existing = db.scalar(select(PushSubscription).where(PushSubscription.endpoint == sub_in.endpoint))
    if existing:
        existing.user_id = user_id
        existing.p256dh = sub_in.keys.p256dh
        existing.auth = sub_in.keys.auth
        db.commit()
        db.refresh(existing)
        return existing

    subscription = PushSubscription(
        user_id=user_id,
        endpoint=sub_in.endpoint,
        p256dh=sub_in.keys.p256dh,
        auth=sub_in.keys.auth,
    )
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    return subscription


def delete_subscription(db: Session, user_id: int, endpoint: str) -> None:
    subscription = db.scalar(
        select(PushSubscription).where(
            PushSubscription.user_id == user_id, PushSubscription.endpoint == endpoint
        )
    )
    if subscription:
        db.delete(subscription)
        db.commit()


def list_for_user(db: Session, user_id: int) -> list[PushSubscription]:
    return list(db.scalars(select(PushSubscription).where(PushSubscription.user_id == user_id)))


def delete_by_endpoint(db: Session, endpoint: str) -> None:
    subscription = db.scalar(select(PushSubscription).where(PushSubscription.endpoint == endpoint))
    if subscription:
        db.delete(subscription)
        db.commit()
