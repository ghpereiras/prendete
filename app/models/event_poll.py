from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base
from app.models.event import generate_invite_token


class EventPoll(Base):
    __tablename__ = "event_polls"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    location_details: Mapped[str | None] = mapped_column(String(255), nullable=True)
    maps_link: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    duration_minutes: Mapped[int] = mapped_column(nullable=False)
    invite_token: Mapped[str] = mapped_column(
        String(32), unique=True, index=True, nullable=False, default=generate_invite_token
    )
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    resulting_event_id: Mapped[int | None] = mapped_column(
        ForeignKey("events.id", ondelete="SET NULL"), nullable=True
    )
    resolved_date_option_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "event_poll_date_options.id",
            ondelete="SET NULL",
            use_alter=True,
            name="fk_event_polls_resolved_date_option_id",
        ),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    owner: Mapped["User"] = relationship(foreign_keys=[owner_id])
    resulting_event: Mapped["Event | None"] = relationship(foreign_keys=[resulting_event_id])
    date_options: Mapped[list["EventPollDateOption"]] = relationship(
        back_populates="poll",
        cascade="all, delete-orphan",
        foreign_keys="EventPollDateOption.poll_id",
        order_by="EventPollDateOption.starts_at",
    )

    @property
    def is_resolved(self) -> bool:
        return self.resulting_event_id is not None

    @property
    def owner_name(self) -> str:
        return self.owner.full_name


class EventPollDateOption(Base):
    __tablename__ = "event_poll_date_options"

    id: Mapped[int] = mapped_column(primary_key=True)
    poll_id: Mapped[int] = mapped_column(ForeignKey("event_polls.id", ondelete="CASCADE"), nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    poll: Mapped["EventPoll"] = relationship(back_populates="date_options", foreign_keys=[poll_id])
    votes: Mapped[list["EventPollVote"]] = relationship(back_populates="date_option", cascade="all, delete-orphan")


class EventPollVote(Base):
    __tablename__ = "event_poll_votes"
    __table_args__ = (UniqueConstraint("date_option_id", "user_id", name="uq_date_option_user"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    date_option_id: Mapped[int] = mapped_column(
        ForeignKey("event_poll_date_options.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    date_option: Mapped["EventPollDateOption"] = relationship(back_populates="votes")
    user: Mapped["User"] = relationship()
