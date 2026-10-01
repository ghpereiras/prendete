import hashlib
from datetime import datetime

from sqlalchemy import DateTime, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[str] = mapped_column(String(255), nullable=False)
    # Null for accounts created through Google sign-in that never set a password.
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    language: Mapped[str] = mapped_column(String(5), nullable=False, server_default="es", default="es")
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    avatar: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    events: Mapped[list["Event"]] = relationship(back_populates="owner", cascade="all, delete-orphan")
    attendances: Mapped[list["Attendee"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    push_subscriptions: Mapped[list["PushSubscription"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    @property
    def avatar_url(self) -> str | None:
        if self.avatar is None:
            return None
        # The endpoint is cached 24h (see get_user_avatar) — a content hash in
        # the query string busts that cache automatically whenever the image
        # actually changes, instead of every viewer being stuck with whatever
        # was cached under the same bare /users/{id}/avatar URL.
        version = hashlib.md5(self.avatar).hexdigest()[:8]
        return f"/users/{self.id}/avatar?v={version}"

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def has_password(self) -> bool:
        return self.hashed_password is not None
