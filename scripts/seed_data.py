"""Populates the database with dummy users, events (past and future) and invitations.

Usage (from the project root, with the backend venv active):
    python scripts/seed_data.py

Safe to re-run: it wipes every user/event/invitation before seeding again
(only makes sense against a dev database — never point this at production).
"""

import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal  # noqa: E402
from app.models.event import Event  # noqa: E402
from app.models.invitation import Invitation, InvitationStatus  # noqa: E402
from app.models.user import User  # noqa: E402
from app.security import hash_password  # noqa: E402

PASSWORD = "password123"

USERS = [
    ("demo@example.com", "Demo User"),
    ("ana.garcia@example.com", "Ana García"),
    ("carlos.ruiz@example.com", "Carlos Ruiz"),
    ("lucia.fernandez@example.com", "Lucía Fernández"),
    ("martin.lopez@example.com", "Martín López"),
    ("sofia.martinez@example.com", "Sofía Martínez"),
    ("diego.sanchez@example.com", "Diego Sánchez"),
    ("valentina.romero@example.com", "Valentina Romero"),
    ("tomas.diaz@example.com", "Tomás Díaz"),
    ("camila.torres@example.com", "Camila Torres"),
]

# (owner_email, title, days_offset, duration_minutes, max_attendees, location, registration_deadline_minutes_before)
PAST_EVENTS = [
    ("demo@example.com", "Asado de fin de año", -15, 240, 12, "Casa de Demo, Palermo", None),
    ("ana.garcia@example.com", "Cumpleaños de Ana", -30, 300, 20, "Salón Fiesta, Belgrano", None),
    ("carlos.ruiz@example.com", "Torneo de fútbol 5", -10, 120, 10, "Cancha El Potrero", None),
    ("lucia.fernandez@example.com", "Noche de juegos de mesa", -20, 180, 8, "Bar La Mesa, San Telmo", None),
    ("martin.lopez@example.com", "Clase de cocina italiana", -45, 150, 6, "Cocina Trattoria, Recoleta", None),
    ("demo@example.com", "Cena de egresados", -60, 210, 15, "Restaurante Central", None),
    ("sofia.martinez@example.com", "Picnic en el parque", -5, 180, 12, "Parque Centenario", None),
    ("diego.sanchez@example.com", "Reunión de ex compañeros", -25, 150, 10, "Café del Barrio", None),
    ("ana.garcia@example.com", "Maratón 10k", -40, 90, 25, "Costanera Norte", None),
    ("carlos.ruiz@example.com", "After office viernes", -3, 150, 14, "Bar Terraza, Microcentro", None),
]

FUTURE_EVENTS = [
    ("martin.lopez@example.com", "Cumpleaños de Martín", 5, 240, 18, "Casa de Martín, Villa Urquiza", None),
    ("demo@example.com", "Conferencia de tecnología 2026", 20, 480, 100, "Centro de Convenciones", 1440),
    ("ana.garcia@example.com", "Asado de bienvenida", 2, 240, 12, "Quinta El Rincón", None),
    ("carlos.ruiz@example.com", "Torneo de truco", 10, 180, 16, "Club Social", None),
    ("lucia.fernandez@example.com", "Clase de yoga al aire libre", 15, 90, 20, "Parque Las Heras", 120),
    ("demo@example.com", "Cena de fin de proyecto", 30, 180, 10, "Restaurante Puerto", None),
    ("sofia.martinez@example.com", "Noche de trivia", 7, 150, 12, "Bar Pregunta", None),
    ("diego.sanchez@example.com", "Salida a la montaña", 45, 2880, 8, "Sierra de la Ventana", 4320),
    ("valentina.romero@example.com", "Cumpleaños de Valentina", 12, 240, 20, "Salón Luna", None),
    ("martin.lopez@example.com", "Meetup de React Buenos Aires", 60, 150, 60, "Coworking Nave", 2880),
]

COMMENTS = [
    "¡Ahí voy a estar!",
    "Llevo algo para compartir.",
    "Nos vemos, tengo ganas.",
    "Voy a llegar un poco más tarde.",
    None,
    None,
]


def wipe(db) -> None:
    db.query(Invitation).delete()
    db.query(Event).delete()
    db.query(User).delete()
    db.commit()


def seed_users(db) -> dict[str, User]:
    users = {}
    for email, full_name in USERS:
        user = User(email=email, full_name=full_name, hashed_password=hash_password(PASSWORD))
        db.add(user)
        users[email] = user
    db.commit()
    for user in users.values():
        db.refresh(user)
    return users


def seed_events(db, users: dict[str, User], specs: list[tuple], *, mostly_accepted: bool) -> None:
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
        invitees = random.sample(candidates, k=random.randint(3, min(6, len(candidates))))
        for invitee in invitees:
            if mostly_accepted:
                status = random.choices(
                    [InvitationStatus.ACCEPTED, InvitationStatus.DECLINED],
                    weights=[85, 15],
                )[0]
            else:
                status = random.choices(
                    [InvitationStatus.ACCEPTED, InvitationStatus.PENDING, InvitationStatus.DECLINED],
                    weights=[50, 40, 10],
                )[0]
            responded_at = now if status != InvitationStatus.PENDING else None
            db.add(
                Invitation(
                    event_id=event.id,
                    invitee_id=invitee.id,
                    status=status,
                    responded_at=responded_at,
                    comment=random.choice(COMMENTS) if status == InvitationStatus.ACCEPTED else None,
                )
            )
    db.commit()


def main() -> None:
    random.seed(42)
    db = SessionLocal()
    try:
        wipe(db)
        users = seed_users(db)
        seed_events(db, users, PAST_EVENTS, mostly_accepted=True)
        seed_events(db, users, FUTURE_EVENTS, mostly_accepted=False)
    finally:
        db.close()

    print(f"Seeded {len(USERS)} users, {len(PAST_EVENTS)} past events, {len(FUTURE_EVENTS)} future events.")
    print(f"All users share the password: {PASSWORD}")
    print("Log in as demo@example.com to see a mix of owned and joined events.")


if __name__ == "__main__":
    main()
