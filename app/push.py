import json
import logging
from typing import Iterable

from pywebpush import WebPushException, webpush
from sqlalchemy.orm import Session

from app.config import settings
from app.crud import push_subscription as push_subscription_crud

logger = logging.getLogger(__name__)

# How long the push service should hold a notification for a device that's
# offline right now, in seconds. pywebpush defaults to 0 ("deliver only if
# connected right now, otherwise drop it") — 3 days gives an offline
# recipient a real chance to still get it instead of losing it silently.
PUSH_TTL_SECONDS = 60 * 60 * 24 * 3


def send_push_to_user(db: Session, user_id: int, payload: dict) -> None:
    for subscription in push_subscription_crud.list_for_user(db, user_id):
        try:
            webpush(
                subscription_info={
                    "endpoint": subscription.endpoint,
                    "keys": {"p256dh": subscription.p256dh, "auth": subscription.auth},
                },
                data=json.dumps(payload),
                vapid_private_key=settings.vapid_private_key,
                vapid_claims={"sub": f"mailto:{settings.vapid_contact_email}"},
                ttl=PUSH_TTL_SECONDS,
            )
        except WebPushException as exc:
            if exc.status_code in (404, 410):
                # The push service invalidated this subscription (browser
                # uninstalled it, site data cleared, etc.) — stop using it.
                push_subscription_crud.delete_by_endpoint(db, subscription.endpoint)
            else:
                logger.warning("Push notification failed for user %s: %s", user_id, exc)


def send_push_to_users(db: Session, user_ids: Iterable[int], payload: dict) -> None:
    for user_id in user_ids:
        try:
            send_push_to_user(db, user_id, payload)
        except Exception:
            # webpush() talks to a third-party service over the network and
            # can raise things other than WebPushException (timeouts,
            # connection errors, ...) that send_push_to_user doesn't catch.
            # One bad delivery must not stop the rest of the attendees from
            # being notified, nor bubble up into the caller's HTTP response —
            # by the time this runs, the actual event change is already
            # committed, so a push failure here is not the caller's error.
            logger.exception("Push notification failed for user %s", user_id)
