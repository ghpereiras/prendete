# Privento

Backend de gestión de eventos: usuarios, eventos e invitaciones. FastAPI + SQLAlchemy + Alembic + PostgreSQL.

## Setup

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
- `POST /events` (dueño = usuario autenticado), `GET /events`, `GET /events/{id}`, `DELETE /events/{id}` (solo el dueño)
- `POST /events/{event_id}/invitations` (solo el dueño del evento), `GET /events/{event_id}/invitations` (solo el dueño)
- `PATCH /invitations/{id}` — actualizar estado (`accepted` / `declined`), solo el invitado

## Pendiente

- Refresh tokens / logout (los JWT actuales expiran solos, no hay revocación).
- Endpoint para editar eventos (`PUT`/`PATCH /events/{id}`).

## Migraciones nuevas

```bash
alembic revision --autogenerate -m "descripcion"
alembic upgrade head
```
