# Privento

Gestión de eventos: usuarios, eventos y asistentes.

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

`scripts/seed_data.py` **borra** todos los usuarios/eventos/asistentes existentes y carga 10 usuarios dummy con 10 eventos pasados y 10 futuros (cada uno con un grupo aleatorio de asistentes). Solo para desarrollo, nunca contra producción:

```bash
python scripts/seed_data.py
```

Todos los usuarios comparten la contraseña `password123`; `demo@example.com` es una buena cuenta para explorar (mezcla de eventos propios y eventos de otros a los que asiste).

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
- `PATCH /events/{id}` — edita el evento (mismos campos y validaciones que `POST /events`); solo el dueño, y solo si el evento todavía no empezó (`403` si ya arrancó). `422` si el `max_attendees` nuevo queda por debajo de la cantidad de invitados ya aceptados
- `DELETE /events/{id}` — solo el dueño, y solo si el evento todavía no empezó (`403` si ya arrancó)

### Invitaciones por link y asistentes

El modelo es simple a propósito: una fila en `attendees` (`app/models/attendee.py`) significa "este usuario va a este evento", sin estados intermedios (no hay `pending`/`declined` — eso existió en una versión anterior y se simplificó). Sumarse crea la fila, abandonar la borra directamente y libera el cupo al instante.

- `GET /events/{event_id}/invite-link` (solo el dueño) — devuelve el `invite_token` para armar el link a compartir
- `POST /events/{event_id}/invite-link/regenerate` (solo el dueño) — invalida el link anterior y genera uno nuevo
- `GET /events/invite/{invite_token}` (público, sin login) — preview del evento y cupos restantes, para mostrar antes de pedir login/registro
- `POST /events/invite/{invite_token}/join` (autenticado) — se suma al evento; body opcional `{"comment": "..."}` (máx. 500 caracteres) que el dueño ve en la lista de asistentes; `409` si ya está sumado, si el evento está lleno, o si ya pasó el cierre de inscripciones (`registration_deadline_minutes_before`, o la fecha de inicio del evento si no se definió uno)
- `PATCH /events/{event_id}/attendance` — actualiza tu propio comentario; `404` si no estás participando en el evento
- `DELETE /events/{event_id}/attendance` — **abandonar el evento**: borra tu fila de asistente y libera el cupo al instante; `403` si sos el dueño (para eso está `DELETE /events/{id}`), `404` si no estabas participando
- `GET /events/{event_id}/attendees` (dueño o participante) — lista para mostrar en el frontend: dueño primero (`is_owner: true`) y después cada asistente, ordenados por `joined_at` (orden en que se sumaron), con nombre y email. El `comment` que cada uno dejó al sumarse solo viaja en la respuesta si quien consulta es el dueño del evento o el propio autor del comentario; para el resto de los participantes viene en `null`

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

`VITE_GOOGLE_MAPS_API_KEY` en `.env` hace falta para poder cargar una ubicación al crear un evento — sin ella, el resto de la app funciona, pero el campo "Ubicación" queda deshabilitado (ver "Ubicación con Google Maps" más abajo, no hay forma manual de cargarla). Para conseguirla:

1. [console.cloud.google.com](https://console.cloud.google.com) → proyecto nuevo → activar facturación (Google pide una tarjeta, incluso para uso que queda dentro de las cuotas gratis).
2. Habilitar, cada una por separado: **Maps JavaScript API** (puede figurar como "Dynamic Maps" en el buscador de APIs), **Places API (New)**, **Maps Embed API**.
3. Credenciales → crear clave de API.
4. Restringirla: por "Referentes HTTP" a tu dominio (`localhost:5173/*` en dev), y por "Restricciones de la API" a las tres de arriba.
5. Pegarla en `frontend/.env` como `VITE_GOOGLE_MAPS_API_KEY=...`.

Páginas:

- `/login`, `/register` — públicas
- `/invite/:token` — pública, preview del evento; si no hay sesión pide login/registro y vuelve acá después
- `/` — protegida, redirige directo a `/events`
- `/events` — protegida, tu pantalla principal: todos tus eventos (propios + a los que asistís) con dos filtros combinables
- `/events/new` — protegida, formulario de creación
- `/events/:eventId` — protegida, detalle del evento; si sos el dueño, muestra el link de invitación para compartir
- `/profile` — protegida, muestra nombre y email del usuario

Todas las páginas comparten un header fijo arriba de todo (`components/Header.tsx`, montado una sola vez en `App.tsx`): a la izquierda un botón circular con ícono de casa que lleva a `/` (que a su vez redirige a `/events`), en el centro el título grande de la página actual (cada página lo setea con `usePageTitle` de `context/PageTitleContext.tsx` — dinámico para páginas como el detalle del evento, que muestra el nombre real del evento en vez de un texto fijo; en `/events` particularmente muestra un saludo, "Hola, {{nombre}}", en vez de un título genérico), y a la derecha el selector de idioma (bandera del idioma activo) y, si hay sesión, un ícono circular con la inicial del usuario que despliega "Mi perfil" / "Cerrar sesión" al pasar el mouse o hacer click (`components/LanguageSwitcher.tsx`, `components/AccountMenu.tsx`, coordinados por `context/TopBarMenuContext.tsx` para que solo uno esté abierto a la vez). No hay sidebar ni navegación lateral — toda la app cuelga de ese header.

`/events` (`pages/Events.tsx`) combina dos filtros independientes, ambos con el mismo componente reutilizable `components/SegmentedFilter.tsx`:
- **Por fecha** (Próximos / Pasados) — se calcula en el cliente comparando `starts_at` contra la hora actual; Próximos ordena ascendente (el más próximo primero), Pasados ordena descendente (el más reciente primero).
- **Por organizador** (Todos / Míos / De otros) — compara `event.owner_id` contra el usuario logueado.

Ambos filtros se combinan sin alterar el orden de la lista.

El token JWT se guarda en `localStorage`.

### Duración y cierre de inscripciones

El formulario de creación pide fecha de inicio + **duración en horas** (no una fecha de fin); el horario de fin se calcula y se muestra en el detalle/preview ([api/events.ts](frontend/src/api/events.ts): `endsAt`). El "Cierre de inscripciones" es opcional (en horas antes del evento) — **si no se completa, el default es la fecha de inicio del evento**: nadie puede sumarse una vez que el evento ya empezó, aunque el dueño no haya configurado un cierre explícito (`crud.event.is_registration_open`). Pasado el cierre, `POST .../join` devuelve `409`, y en la preview de invitación el botón "Sumarme" desaparece y se muestra un contador en vivo (`HH:MM:SS`, o `Xd HH:MM:SS` si faltan 24hs o más) hasta el cierre.

### Ubicación con Google Maps

El campo "Ubicación" del formulario de creación **es** el buscador de Google Maps (`components/LocationSearch.tsx`) — no hay forma de pegar un link a mano, ni un campo de link separado. Requiere `VITE_GOOGLE_MAPS_API_KEY` configurada en `frontend/.env`, con Maps JavaScript API + Places API (New) + Maps Embed API habilitadas en el proyecto de Google Cloud (ver "Frontend — Setup" más arriba); si la key no está o falla la carga, el campo se deshabilita y muestra un error — no hay fallback de texto libre.

Autocompletado en vivo mientras se escribe (Places API New — `AutocompleteSuggestion`, agrupado en sesiones con `AutocompleteSessionToken` para el billing). Al elegir un resultado, se pide el detalle del lugar (`Place.fetchFields`) y con el `place_id` exacto se arma directo `https://www.google.com/maps/embed/v1/place?key=...&q=place_id:<id>` (`utils/googleMaps.ts: buildEmbedUrl`), que se guarda tal cual en `maps_link` — el backend ya no transforma ni valida ese campo, confía en que el frontend siempre manda un link embebible real. El pin queda exacto (viene del `place_id`, no de coordenadas parseadas de una URL) y con el nombre real del lugar.

Si después de elegir un resultado el usuario edita el texto de "Ubicación" a mano, se descarta el link guardado (para no guardar un mapa que ya no corresponde al texto) — el evento queda con esa ubicación como texto libre, sin mapa incrustado.

La detección de si un `maps_link` ya guardado es embebible sigue siendo automática en el frontend ([utils/maps.ts](frontend/src/utils/maps.ts)) para cuando se muestra el evento. Si no se elige ningún lugar, el evento queda sin mapa.

### Foto de perfil

En `/register`, `components/AvatarPicker.tsx` deja elegir una foto (opcional): abre el selector de archivos nativo, y con [react-easy-crop](https://github.com/ValentinH/react-easy-crop) muestra la imagen completa con una máscara circular y zoom para recortarla. Al confirmar, se extrae el recorte a un `<canvas>` de 256x256 y se comprime a JPEG (`utils/image.ts: cropImageToDataUrl`) antes de mandarlo como `avatar_base64` al backend, que igual vuelve a validar/normalizar todo (ver sección de Endpoints). Cuando el usuario tiene foto, reemplaza la inicial en el círculo de cuenta del header (`components/AccountMenu.tsx`), se ve más grande en `/profile`, y aparece antes del nombre en la lista de asistentes de un evento (`components/Avatar.tsx`, usado en `EventDetail.tsx`).

En `/profile`, el botón "Editar perfil" cambia a un formulario (mismo `AvatarPicker`, precargado con la foto actual) para cambiar nombre y/o foto — pega a `PATCH /users/me` y actualiza el usuario en `AuthContext` al instante (sin recargar la página), así el header y el resto de la app reflejan el cambio enseguida.

### Editar y eliminar eventos

En `/events/:id`, el dueño ve los botones "Editar evento" y "Eliminar evento" — solo mientras el evento no haya empezado (`event.starts_at` a futuro); una vez que arrancó, dejan de mostrarse tanto para el dueño como para cualquier participante. "Editar evento" lleva a `/events/:id/edit`, que reusa el mismo formulario y componente de `CreateEvent.tsx` (incluida la búsqueda de ubicación) precargado con los datos actuales y pega a `PATCH /events/{id}` en vez de `POST /events`. "Eliminar evento" abre un popup de confirmación (`components/ConfirmModal.tsx`: Cancelar / Sí, eliminar) antes de pegar a `DELETE /events/{id}` y volver al home. El backend valida ambas operaciones server-side además de ocultarlas en el frontend (dueño y evento no empezado), y `PATCH` además rechaza bajar el `max_attendees` por debajo de la cantidad de invitados ya aceptados.

### Abandonar un evento

En `/events/:id`, quien participa y no es el dueño ve el botón "Salir del evento" (mismo popup de confirmación, `ConfirmModal`, que "Eliminar evento"). Pega a `DELETE /events/{event_id}/attendance`, que borra directamente la fila de `attendees` — no queda ningún registro de que participaste, y el cupo se libera al instante para que otro pueda sumarse. Después te redirige al home. El dueño nunca ve este botón: para borrar su propio evento existe "Eliminar evento".

En esa misma fila, quien participa también puede editar su propio comentario ("Editar comentario" / "Agregar comentario" si no había dejado uno) — abre el mismo tipo de textarea que al sumarse por primera vez y pega a `PATCH /events/{event_id}/attendance`. Nadie más puede editar el comentario ajeno: el endpoint solo actúa sobre la fila de `attendees` del propio usuario autenticado.

## Pendiente

- Refresh tokens / logout server-side (los JWT actuales expiran solos, no hay revocación).
- Frontend: pantalla para que el dueño vea/gestione la lista de invitados de un evento.
- Cambiar el email desde `/profile` (`PATCH /users/me` solo actualiza nombre y foto, no el email).
- Sistema de roles (USER/ADMIN) — quedó en pausa, sin implementar.
