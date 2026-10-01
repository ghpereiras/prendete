import base64
import logging
import re
from urllib.parse import urlparse

import requests
from google.auth.exceptions import TransportError
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from app.config import settings
from app.utils.avatar import InvalidAvatarError, process_avatar

logger = logging.getLogger(__name__)


class InvalidGoogleToken(Exception):
    pass


class GoogleUnavailable(Exception):
    pass


def verify_google_id_token(credential: str, nonce: str) -> dict:
    if not settings.google_client_id:
        raise GoogleUnavailable("Google sign-in is not configured")
    try:
        info = id_token.verify_oauth2_token(
            credential, google_requests.Request(), settings.google_client_id
        )
    except TransportError as exc:
        raise GoogleUnavailable(str(exc)) from exc
    except ValueError as exc:
        raise InvalidGoogleToken(str(exc)) from exc

    if info.get("nonce") != nonce:
        raise InvalidGoogleToken("Nonce mismatch")
    if not info.get("email") or not info.get("email_verified"):
        raise InvalidGoogleToken("Google account email is not verified")
    return info


def fetch_profile_picture(url: str) -> bytes | None:
    """Download and normalize the Google profile photo; None if unavailable.

    Best effort: signing in must never fail because the photo couldn't be fetched.
    """
    parsed = urlparse(url)
    if parsed.scheme != "https" or not (parsed.hostname or "").endswith(".googleusercontent.com"):
        return None
    # Google serves a 96px thumbnail by default; ask for a size close to what we store.
    sized_url = re.sub(r"=s\d+(-c)?$", "=s256-c", url)
    try:
        response = requests.get(sized_url, timeout=5)
        response.raise_for_status()
        return process_avatar(base64.b64encode(response.content).decode())
    except (requests.RequestException, InvalidAvatarError):
        logger.warning("Could not fetch Google profile picture", exc_info=True)
        return None
