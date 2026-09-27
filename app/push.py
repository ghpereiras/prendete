import json
import logging

from pywebpush import WebPushException, webpush
from sqlalchemy.orm import Session

from app.config import settings
from app.crud import push_subscription as push_subscription_crud

logger = logging.getLogger(__name__)


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
            )
        except WebPushException as exc:
            if exc.status_code in (404, 410):
                # The push service invalidated this subscription (browser
                # uninstalled it, site data cleared, etc.) — stop using it.
                push_subscription_crud.delete_by_endpoint(db, subscription.endpoint)
            else:
                logger.warning("Push notification failed for user %s: %s", user_id, exc)
