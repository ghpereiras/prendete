"""Populates the database with dummy users, events (past and future) and attendees.

Usage (from the project root, with the backend venv active):
    python scripts/seed_data.py

Safe to re-run: it wipes every user/event/attendee before seeding again
(only makes sense against a dev database — never point this at production).
"""

import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal  # noqa: E402
from app.models.attendee import Attendee  # noqa: E402
from app.models.event import Event  # noqa: E402
from app.models.event_poll import EventPoll, EventPollDateOption, EventPollVote  # noqa: E402
from app.models.user import User  # noqa: E402
from app.security import hash_password  # noqa: E402

PASSWORD = "password123"

USERS = [
    ("demo@example.com", "Demo", "User"),
    ("ana.garcia@example.com", "Ana", "García"),
    ("carlos.ruiz@example.com", "Carlos", "Ruiz"),
    ("lucia.fernandez@example.com", "Lucía", "Fernández"),
    ("martin.lopez@example.com", "Martín", "López"),
    ("sofia.martinez@example.com", "Sofía", "Martínez"),
    ("diego.sanchez@example.com", "Diego", "Sánchez"),
    ("valentina.romero@example.com", "Valentina", "Romero"),
    ("tomas.diaz@example.com", "Tomás", "Díaz"),
    ("camila.torres@example.com", "Camila", "Torres"),
]

# (owner_email, title, days_offset, duration_minutes, max_attendees, location, registration_deadline_minutes_before)
# Locations are real places that resolve on Google Maps (not made-up names), so
# the seeded events show accurate map cards in the app.
PAST_EVENTS = [
    ("demo@example.com", "Asado de fin de año", -15, 240, 12, "Bosques de Palermo, Buenos Aires", None),
    ("ana.garcia@example.com", "Cumpleaños de Ana", -30, 300, 20, "Centro Cultural Recoleta, Buenos Aires", None),
    ("carlos.ruiz@example.com", "Torneo de fútbol 5", -10, 120, 10, "Club Ferro Carril Oeste, Caballito, Buenos Aires", None),
    ("lucia.fernandez@example.com", "Noche de juegos de mesa", -20, 180, 8, "Plaza Dorrego, San Telmo, Buenos Aires", None),
    ("martin.lopez@example.com", "Clase de cocina italiana", -45, 150, 6, "Plaza Francia, Recoleta, Buenos Aires", None),
    ("demo@example.com", "Cena de egresados", -60, 210, 15, "La Cabrera, Palermo, Buenos Aires", None),
    ("sofia.martinez@example.com", "Picnic en el parque", -5, 180, 12, "Parque Centenario, Buenos Aires", None),
    ("diego.sanchez@example.com", "Reunión de ex compañeros", -25, 150, 10, "Café Tortoni, Buenos Aires", None),
    ("ana.garcia@example.com", "Maratón 10k", -40, 90, 25, "Costanera Norte, Buenos Aires", None),
    ("carlos.ruiz@example.com", "After office viernes", -3, 150, 14, "Florería Atlántico, Retiro, Buenos Aires", None),
]

FUTURE_EVENTS = [
    ("martin.lopez@example.com", "Cumpleaños de Martín", 5, 240, 18, "Parque Sarmiento, Villa Urquiza, Buenos Aires", None),
    ("demo@example.com", "Conferencia de tecnología 2026", 20, 480, 100, "La Rural, Predio Ferial de Buenos Aires", 1440),
    ("ana.garcia@example.com", "Asado de bienvenida", 2, 240, 12, "Delta del Tigre, Buenos Aires", None),
    ("carlos.ruiz@example.com", "Torneo de truco", 10, 180, 16, "Chacarita Juniors, Buenos Aires", None),
    ("lucia.fernandez@example.com", "Clase de yoga al aire libre", 15, 90, 20, "Parque Las Heras, Buenos Aires", 120),
    ("demo@example.com", "Cena de fin de proyecto", 30, 180, 10, "Puerto Madero, Buenos Aires", None),
    ("sofia.martinez@example.com", "Noche de trivia", 7, 150, 12, "Los Galgos, Congreso, Buenos Aires", None),
    ("diego.sanchez@example.com", "Salida a la montaña", 45, 2880, 8, "Sierra de la Ventana, Buenos Aires", 4320),
    ("valentina.romero@example.com", "Cumpleaños de Valentina", 12, 240, 20, "Usina del Arte, La Boca, Buenos Aires", None),
    ("martin.lopez@example.com", "Meetup de React Buenos Aires", 60, 150, 60, "Centro Cultural Kirchner, Buenos Aires", 2880),
]

COMMENTS = [
    "¡Ahí voy a estar!",
    "Llevo algo para compartir.",
    "Nos vemos, tengo ganas.",
    "Voy a llegar un poco más tarde.",
    None,
    None,
]

# (owner_email, title, location, duration_minutes, [days_offset for each proposed date])
POLLS = [
    (
        "demo@example.com",
        "Buscando fecha para el asado de otoño",
        "Bosques de Palermo, Buenos Aires",
        240,
        [10, 17, 24],
    ),
    (
        "carlos.ruiz@example.com",
        "¿Cuándo hacemos el torneo de ping pong?",
        "Club Ferro Carril Oeste, Caballito, Buenos Aires",
        120,
        [8, 15],
    ),
    (
        "lucia.fernandez@example.com",
        "Noche de karaoke, ¿qué día les viene mejor?",
        "Bar Sur, San Telmo, Buenos Aires",
        180,
        [12, 19, 26, 33],
    ),
    (
        "valentina.romero@example.com",
        "Weekend de camping",
        "Tigre, Buenos Aires",
        2880,
        [40, 55],
    ),
]


def wipe(db) -> None:
    db.query(EventPollVote).delete()
    db.query(EventPollDateOption).delete()
    db.query(EventPoll).delete()
    db.query(Attendee).delete()
    db.query(Event).delete()
    db.query(User).delete()
    db.commit()


def seed_users(db) -> dict[str, User]:
    users = {}
    for email, first_name, last_name in USERS:
        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            hashed_password=hash_password(PASSWORD),
            email_verified_at=datetime.now(timezone.utc),
        )
        db.add(user)
        users[email] = user
    db.commit()
    for user in users.values():
        db.refresh(user)
    return users


def seed_events(db, users: dict[str, User], specs: list[tuple]) -> None:
    now = datetime.now(timezone.utc)
    for owner_email, title, days_offset, duration, max_attendees, location, deadline_minutes in specs:
        owner = users[owner_email]
        event = Event(
            title=title,
            description=f"{title} — organizado por {owner.full_name}.",
            location=location,
            starts_at=now + timedelta(days=days_offset, hours=random.randint(0, 5)),
            duration_minutes=duration,
            registration_deadline_minutes_before=deadline_minutes,
            max_attendees=max_attendees,
            owner_id=owner.id,
        )
        db.add(event)
        db.flush()

        candidates = [u for email, u in users.items() if email != owner_email]
        attendees = random.sample(candidates, k=random.randint(3, min(6, len(candidates))))
        for attendee in attendees:
            db.add(
                Attendee(
                    event_id=event.id,
                    user_id=attendee.id,
                    comment=random.choice(COMMENTS),
                )
            )
    db.commit()


def seed_polls(db, users: dict[str, User]) -> None:
    now = datetime.now(timezone.utc)
    for owner_email, title, location, duration, day_offsets in POLLS:
        owner = users[owner_email]
        poll = EventPoll(
            title=title,
            description=f"{title} — organiza {owner.full_name}.",
            location=location,
            duration_minutes=duration,
            owner_id=owner.id,
        )
        db.add(poll)
        db.flush()

        date_options = []
        for offset in day_offsets:
            option = EventPollDateOption(
                poll_id=poll.id,
                starts_at=now + timedelta(days=offset, hours=random.randint(0, 5)),
            )
            db.add(option)
            date_options.append(option)
        db.flush()

        # Each voter marks one or more of the proposed dates as one they can
        # make it to — not everyone invited necessarily votes for all of them.
        candidates = [u for email, u in users.items() if email != owner_email]
        voters = random.sample(candidates, k=random.randint(3, min(6, len(candidates))))
        for voter in voters:
            chosen_options = random.sample(date_options, k=random.randint(1, len(date_options)))
            for option in chosen_options:
                db.add(EventPollVote(date_option_id=option.id, user_id=voter.id))
    db.commit()


def main() -> None:
    random.seed(42)
    db = SessionLocal()
    try:
        wipe(db)
        users = seed_users(db)
        seed_events(db, users, PAST_EVENTS)
        seed_events(db, users, FUTURE_EVENTS)
        seed_polls(db, users)
    finally:
        db.close()

    print(f"Seeded {len(USERS)} users, {len(PAST_EVENTS)} past events, {len(FUTURE_EVENTS)} future events.")
    print(f"Seeded {len(POLLS)} date polls, each with voters already picked on some of the dates.")
    print(f"All users share the password: {PASSWORD}")
    print("Log in as demo@example.com to see a mix of owned and joined events, plus a pending poll.")


if __name__ == "__main__":
    main()
