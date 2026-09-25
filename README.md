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

## Datos de prueba

`scripts/seed_data.py` **borra** todos los usuarios/eventos/invitaciones existentes y carga 10 usuarios dummy con 10 eventos pasados y 10 futuros (con invitaciones en distintos estados). Solo para desarrollo, nunca contra producción:

```bash
python scripts/seed_data.py
```

Todos los usuarios comparten la contraseña `password123`; `demo@example.com` es una buena cuenta para explorar (mezcla de eventos propios e invitaciones a eventos de otros).

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

- `POST /users` (público) — registro; acepta `avatar_base64` opcional (bare base64 o data URL). Se decodifica, valida como imagen real, recorta al centro a cuadrado, se redimensiona a 256x256 y se re-comprimir como JPEG antes de guardar (`app/utils/avatar.py: process_avatar`) — nunca se confía en el recorte/tamaño que mandó el cliente. `422` si no es una imagen válida o pesa más de 8MB decodificada.
- `GET /users`, `GET /users/me`, `GET /users/{id}` — incluyen `avatar_url` (`/users/{id}/avatar`) o `null` si no tiene foto
- `PATCH /users/me` — edita el propio nombre y/o foto; todos los campos son opcionales e independientes: `full_name` (si se manda, reemplaza el nombre), `avatar_base64` (si se manda, reemplaza la foto, mismo procesamiento/validación que en el registro), `remove_avatar: true` (saca la foto actual). Mandar `avatar_base64` y `remove_avatar: true` juntos no tiene sentido — gana `remove_avatar`
- `GET /users/{id}/avatar` (público, sin login) — devuelve el JPEG crudo; no requiere auth a propósito porque se consume desde `<img src="...">` (header, perfil, lista de asistentes), que nunca manda el JWT
- `POST /auth/login` (público)
- `POST /events` (dueño = usuario autenticado; requiere `starts_at`, `duration_minutes` y `max_attendees`; `location`, `location_details`, `maps_link` y `registration_deadline_minutes_before` son opcionales). `422` si `starts_at` ya pasó, o si con el `registration_deadline_minutes_before` elegido las inscripciones ya estarían cerradas en el momento de crear el evento (validado en `EventCreate.validate_start_and_registration_window`, `app/schemas/event.py`)
- `GET /events` — eventos propios + eventos donde participás (no lista todos los eventos del sistema), ordenados por `starts_at` ascendente (el que empieza más pronto primero); cada evento incluye `owner_name`
- `GET /events/{id}` — solo el dueño o un participante aceptado (404 para el resto)
- `DELETE /events/{id}` — solo el dueño

### Invitaciones por link

- `GET /events/{event_id}/invite-link` (solo el dueño) — devuelve el `invite_token` para armar el link a compartir
- `POST /events/{event_id}/invite-link/regenerate` (solo el dueño) — invalida el link anterior y genera uno nuevo
- `GET /events/invite/{invite_token}` (público, sin login) — preview del evento y cupos restantes, para mostrar antes de pedir login/registro
- `POST /events/invite/{invite_token}/join` (autenticado) — se suma al evento; body opcional `{"comment": "..."}` (máx. 500 caracteres) que el dueño ve en la lista de asistentes; `409` si ya está sumado, si el evento está lleno, o si ya pasó el cierre de inscripciones (`registration_deadline_minutes_before`, o la fecha de inicio del evento si no se definió uno)
- `GET /events/{event_id}/invitations` (solo el dueño) — lista las invitaciones (todas, cualquier estado), con `invitee_id`
- `GET /events/{event_id}/attendees` (dueño o participante aceptado) — lista para mostrar en el frontend: dueño primero (`is_owner: true`) y después cada invitado aceptado, con nombre y email. El `comment` que cada uno dejó al sumarse solo viaja en la respuesta si quien consulta es el dueño del evento o el propio autor del comentario; para el resto de los participantes viene en `null`
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
- `/` — protegida, lista todos tus eventos y accedé a crear uno nuevo
- `/events/upcoming` — protegida, solo eventos con `starts_at` futuro (orden ascendente, el más próximo primero)
- `/events/past` — protegida, solo eventos con `starts_at` pasado (orden descendente, el más reciente primero)
- `/events/new` — protegida, formulario de creación
- `/events/:eventId` — protegida, detalle del evento; si sos el dueño, muestra el link de invitación para compartir
- `/profile` — protegida, muestra nombre y email del usuario

Todas las páginas comparten un header fijo arriba de todo (`components/Header.tsx`, montado una sola vez en `App.tsx`): a la izquierda un botón circular con ícono de casa que lleva a `/`, en el centro el título grande de la página actual (cada página lo setea con `usePageTitle` de `context/PageTitleContext.tsx` — dinámico para páginas como el detalle del evento, que muestra el nombre real del evento en vez de un texto fijo), y a la derecha el selector de idioma (bandera del idioma activo) y, si hay sesión, un ícono circular con la inicial del usuario que despliega "Mi perfil" / "Cerrar sesión" al pasar el mouse o hacer click (`components/LanguageSwitcher.tsx`, `components/AccountMenu.tsx`, coordinados por `context/TopBarMenuContext.tsx` para que solo uno esté abierto a la vez). Además, las páginas protegidas muestran debajo del header una barra lateral fija (`components/Sidebar.tsx`, vía `components/Layout.tsx` en `context/ProtectedRoute.tsx`) con links a Inicio / Próximos eventos / Eventos pasados; en mobile se convierte en una fila horizontal. Los filtros de próximos/pasados se calculan en el cliente comparando `starts_at` contra la hora actual.

El token JWT se guarda en `localStorage`.

### Duración y cierre de inscripciones

El formulario de creación pide fecha de inicio + **duración en horas** (no una fecha de fin); el horario de fin se calcula y se muestra en el detalle/preview ([api/events.ts](frontend/src/api/events.ts): `endsAt`). El "Cierre de inscripciones" es opcional (en horas antes del evento) — **si no se completa, el default es la fecha de inicio del evento**: nadie puede sumarse una vez que el evento ya empezó, aunque el dueño no haya configurado un cierre explícito (`crud.event.is_registration_open`). Pasado el cierre, `POST .../join` devuelve `409`, y en la preview de invitación el botón "Sumarme" desaparece y se muestra un contador en vivo (`HH:MM:SS`, o `Xd HH:MM:SS` si faltan 24hs o más) hasta el cierre.

### Ubicación con Google Maps

El campo "Link de Google Maps" del formulario de creación es opcional y acepta dos tipos de link, sin necesidad de API key:

- **Link de "Compartir"** (`maps.app.goo.gl/...` o `google.com/maps/place/...`): Google no permite embeberlo en un iframe, así que se muestra un botón "Ver en Google Maps" que abre en pestaña nueva.
- **Link de "Insertar un mapa"** (Compartir → *Insertar un mapa*): se muestra el mapa incrustado directamente en la página. El campo acepta tanto pegar solo el link (`google.com/maps/embed?pb=...`) como pegar el `<iframe>` completo que copia Google — el backend extrae la URL del `src` antes de guardar (`app/utils/maps.py: extract_maps_url`, aplicado en `EventCreate.maps_link`), así que no hace falta que el usuario edite el HTML a mano.

La detección de si es embebible es automática en el frontend ([utils/maps.ts](frontend/src/utils/maps.ts)) según el formato de la URL ya normalizada. Si no se completa ningún link, el evento queda solo con el texto libre de "Ubicación".

### Foto de perfil

En `/register`, `components/AvatarPicker.tsx` deja elegir una foto (opcional): abre el selector de archivos nativo, y con [react-easy-crop](https://github.com/ValentinH/react-easy-crop) muestra la imagen completa con una máscara circular y zoom para recortarla. Al confirmar, se extrae el recorte a un `<canvas>` de 256x256 y se comprime a JPEG (`utils/image.ts: cropImageToDataUrl`) antes de mandarlo como `avatar_base64` al backend, que igual vuelve a validar/normalizar todo (ver sección de Endpoints). Cuando el usuario tiene foto, reemplaza la inicial en el círculo de cuenta del header (`components/AccountMenu.tsx`), se ve más grande en `/profile`, y aparece antes del nombre en la lista de asistentes de un evento (`components/Avatar.tsx`, usado en `EventDetail.tsx`).

En `/profile`, el botón "Editar perfil" cambia a un formulario (mismo `AvatarPicker`, precargado con la foto actual) para cambiar nombre y/o foto — pega a `PATCH /users/me` y actualiza el usuario en `AuthContext` al instante (sin recargar la página), así el header y el resto de la app reflejan el cambio enseguida.

## Pendiente

- Refresh tokens / logout server-side (los JWT actuales expiran solos, no hay revocación).
- Endpoint para editar eventos (`PUT`/`PATCH /events/{id}`).
- Frontend: pantalla para que el dueño vea/gestione la lista de invitados de un evento.
- Cambiar el email desde `/profile` (`PATCH /users/me` solo actualiza nombre y foto, no el email).
- Sistema de roles (USER/ADMIN) — quedó en pausa, sin implementar.
