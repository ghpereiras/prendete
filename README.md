# Privento

Backend de gestión de eventos: usuarios, eventos e invitaciones. FastAPI + SQLAlchemy + Alembic + PostgreSQL.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
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

## Endpoints

- `POST /users`, `GET /users`, `GET /users/{id}`
- `POST /events?owner_id=`, `GET /events`, `GET /events/{id}`, `DELETE /events/{id}`
- `POST /events/{event_id}/invitations`, `GET /events/{event_id}/invitations`
- `PATCH /invitations/{id}` — actualizar estado (`accepted` / `declined`)

## Pendiente

- Autenticación (JWT) — hoy `owner_id` se pasa como query param sin validar identidad.
- Migrar `owner_id` / rutas protegidas una vez agregada la auth.

## Migraciones nuevas

```bash
alembic revision --autogenerate -m "descripcion"
alembic upgrade head
```
