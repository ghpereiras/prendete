# Privento

Gestión de eventos: usuarios, eventos e invitaciones.

- Backend: FastAPI + SQLAlchemy + Alembic + PostgreSQL (raíz del repo)
- Frontend: React + Vite + TypeScript ([frontend/](frontend))

## Backend — Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Editar `.env` y generar un `SECRET_KEY` propio:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

## Base de datos

Levantar Postgres con Docker:

```bash
docker compose up -d
```

Aplicar migraciones:

```bash
alembic upgrade head
```

## Correr la API

```bash
uvicorn app.main:app --reload
```

Docs interactivas en `http://localhost:8000/docs`.

## Autenticación

Todas las rutas salvo `POST /users` (registro) y `POST /auth/login` requieren un JWT.

```bash
# registrarse
curl -X POST localhost:8000/users -H "Content-Type: application/json" \
  -d '{"email":"a@a.com","full_name":"A","password":"secret123"}'

# login (form-urlencoded, username = email)
curl -X POST localhost:8000/auth/login \
  -d "username=a@a.com&password=secret123"

# usar el token
curl localhost:8000/users/me -H "Authorization: Bearer <access_token>"
```

En `/docs`, botón "Authorize" con el mismo email/password.

## Endpoints

- `POST /users` (público), `GET /users`, `GET /users/me`, `GET /users/{id}`
- `POST /auth/login` (público)
- `POST /events` (dueño = usuario autenticado; requiere `starts_at`, `duration_minutes` y `max_attendees`; `location`, `location_details`, `maps_link` y `registration_deadline_minutes_before` son opcionales)
- `GET /events` — eventos propios + eventos donde participás (no lista todos los eventos del sistema)
- `GET /events/{id}` — solo el dueño o un participante aceptado (404 para el resto)
- `DELETE /events/{id}` — solo el dueño

### Invitaciones por link

- `GET /events/{event_id}/invite-link` (solo el dueño) — devuelve el `invite_token` para armar el link a compartir
- `POST /events/{event_id}/invite-link/regenerate` (solo el dueño) — invalida el link anterior y genera uno nuevo
- `GET /events/invite/{invite_token}` (público, sin login) — preview del evento y cupos restantes, para mostrar antes de pedir login/registro
- `POST /events/invite/{invite_token}/join` (autenticado) — se suma al evento; `409` si ya está sumado, si el evento está lleno, o si ya pasó el cierre de inscripciones (`registration_deadline_minutes_before`, o la fecha de inicio del evento si no se definió uno)
- `GET /events/{event_id}/invitations` (solo el dueño) — lista las invitaciones (todas, cualquier estado), con `invitee_id`
- `GET /events/{event_id}/attendees` (dueño o participante aceptado) — lista para mostrar en el frontend: dueño primero (`is_owner: true`) y después cada invitado aceptado, con nombre y email
- `PATCH /invitations/{id}` — cambiar el propio estado (`declined` para salir del evento y liberar cupo, `accepted` para volver a sumarse si hay lugar), solo el invitado

## Tests

```bash
pytest
```

Usan una base separada (`privento_test`, en el mismo Postgres) que se crea sola si no existe, y se truncan las tablas antes de cada test. No tocan la base de desarrollo.

## Migraciones nuevas

```bash
alembic revision --autogenerate -m "descripcion"
alembic upgrade head
```

## Frontend — Setup

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Corre en `http://localhost:5173`. El backend debe estar corriendo en `http://localhost:8000` (CORS ya configurado para ese origen en `app/main.py`).

Páginas:

- `/login`, `/register` — públicas
- `/invite/:token` — pública, preview del evento; si no hay sesión pide login/registro y vuelve acá después
- `/` — protegida, lista tus eventos y accedé a crear uno nuevo
- `/events/new` — protegida, formulario de creación
- `/events/:eventId` — protegida, detalle del evento; si sos el dueño, muestra el link de invitación para compartir

El token JWT se guarda en `localStorage`.

### Duración y cierre de inscripciones

El formulario de creación pide fecha de inicio + **duración en horas** (no una fecha de fin); el horario de fin se calcula y se muestra en el detalle/preview ([api/events.ts](frontend/src/api/events.ts): `endsAt`). El "Cierre de inscripciones" es opcional (en horas antes del evento) — **si no se completa, el default es la fecha de inicio del evento**: nadie puede sumarse una vez que el evento ya empezó, aunque el dueño no haya configurado un cierre explícito (`crud.event.is_registration_open`). Pasado el cierre, `POST .../join` devuelve `409`, y en la preview de invitación el botón "Sumarme" desaparece y se muestra un contador en vivo (`HH:MM:SS`, o `Xd HH:MM:SS` si faltan 24hs o más) hasta el cierre.

### Ubicación con Google Maps

El campo "Link de Google Maps" del formulario de creación es opcional y acepta dos tipos de link, sin necesidad de API key:

- **Link de "Compartir"** (`maps.app.goo.gl/...` o `google.com/maps/place/...`): Google no permite embeberlo en un iframe, así que se muestra un botón "Ver en Google Maps" que abre en pestaña nueva.
- **Link de "Insertar un mapa"** (Compartir → *Insertar un mapa* → copiar el `src` del iframe, `google.com/maps/embed?pb=...`): se muestra el mapa incrustado directamente en la página.

La detección es automática ([utils/maps.ts](frontend/src/utils/maps.ts)) según el formato del link pegado. Si no se completa ningún link, el evento queda solo con el texto libre de "Ubicación".

## Pendiente

- Refresh tokens / logout server-side (los JWT actuales expiran solos, no hay revocación).
- Endpoint para editar eventos (`PUT`/`PATCH /events/{id}`).
- Frontend: pantalla para que el dueño vea/gestione la lista de invitados de un evento.
- Sistema de roles (USER/ADMIN) — quedó en pausa, sin implementar.
