import base64
import binascii
import io

from PIL import Image, UnidentifiedImageError

AVATAR_SIZE = 256
JPEG_QUALITY = 85
# Matches the client-side cap on the raw file the user picks, before cropping.
MAX_DECODED_BYTES = 8 * 1024 * 1024


class InvalidAvatarError(ValueError):
    pass


def process_avatar(data: str) -> bytes:
    """Decode, validate and normalize an avatar image to a square JPEG.

    Accepts a bare base64 string or a data URL (data:image/...;base64,...).
    Never trusts the client's crop or size: always re-crops to a centered
    square, resizes to AVATAR_SIZE and re-encodes as JPEG, so every stored
    avatar has the same predictable format and a small, bounded size.
    """
    encoded = data.split(",", 1)[1] if data.startswith("data:") else data

    try:
        raw = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise InvalidAvatarError("Invalid base64 image data") from exc

    if len(raw) > MAX_DECODED_BYTES:
        raise InvalidAvatarError("Image is too large")

    try:
        Image.open(io.BytesIO(raw)).verify()
        image = Image.open(io.BytesIO(raw))  # verify() consumes the file; reopen to use it
    except (UnidentifiedImageError, OSError) as exc:
        raise InvalidAvatarError("File is not a valid image") from exc

    image = image.convert("RGB")

    width, height = image.size
    side = min(width, height)
    left = (width - side) // 2
    top = (height - side) // 2
    image = image.crop((left, top, left + side, top + side))
    image = image.resize((AVATAR_SIZE, AVATAR_SIZE), Image.LANCZOS)

    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=JPEG_QUALITY)
    return buffer.getvalue()
