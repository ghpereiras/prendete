import secrets
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


def generate_invite_token() -> str:
    return secrets.token_urlsafe(12)


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    location_details: Mapped[str | None] = mapped_column(String(255), nullable=True)
    maps_link: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    registration_deadline_minutes_before: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_attendees: Mapped[int] = mapped_column(Integer, nullable=False)
    invite_token: Mapped[str] = mapped_column(
        String(32), unique=True, index=True, nullable=False, default=generate_invite_token
    )
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    owner: Mapped["User"] = relationship(back_populates="events")
    attendees: Mapped[list["Attendee"]] = relationship(back_populates="event", cascade="all, delete-orphan")

    @property
    def owner_name(self) -> str:
        return self.owner.full_name
