# CLAUDE.md

Guía para trabajar en este repo. Para features/setup del usuario final ver [README.md](README.md); para el plan de deploy, [DEPLOY.md](DEPLOY.md). Esto es sobre cómo trabajar en el código, no qué hace la app.

## Stack

- Backend: FastAPI + SQLAlchemy 2.0 + Alembic + PostgreSQL, en la raíz del repo (`app/`). Venv en `.venv/` (`source .venv/bin/activate`).
- Frontend: React 19 + Vite + TypeScript en `frontend/`, react-router-dom v6, react-i18next (es/en, default es).
- Auth: JWT (PyJWT) + bcrypt.

## Comandos

```bash
source .venv/bin/activate && python -m pytest -q       # backend tests (rápido, correr siempre después de tocar app/)
cd frontend && npx tsc -b --noEmit                       # typecheck frontend (correr siempre después de tocar frontend/src)
cd frontend && npm run dev                               # dev server
alembic upgrade head                                     # aplicar migraciones pendientes
alembic revision --autogenerate -m "mensaje"              # nueva migración
```

## Convenciones del proyecto

- **Idioma**: el usuario escribe en español, las respuestas de la UI (i18n) son en es/en, pero comentarios de código, nombres de variables y mensajes de commit van en inglés.
- **Endpoints self-service**: para acciones sobre el propio recurso del usuario autenticado, preferir `PATCH`/`DELETE /events/{event_id}/attendance` (actúa sobre la fila del usuario actual, sin ID) en vez de `/attendance/{id}` genérico. Mismo patrón para `/users/me/*`.
- **Sin filas "soft-delete"**: el modelo `Attendee` no tiene `status` — salir de un evento borra la fila directamente. No reintroducir estados tipo pending/declined salvo que el usuario lo pida explícitamente (ya se simplificó una vez a pedido suyo).
- **Modales de confirmación**: reusar las clases CSS `.confirm-modal-backdrop` / `.confirm-modal` / `.confirm-modal-actions` (definidas en `App.css`) para cualquier popup nuevo. El componente `ConfirmModal.tsx` en sí solo sirve para confirmaciones destructivas (fuerza el botón a `.danger` rojo) — para un popup neutral (como `NotificationPrompt.tsx`), copiar el patrón de clases pero no importar el componente.
- **Validación de formularios**: nada de validación nativa HTML5 (`required`, `minLength`, `type="email"` sin `noValidate`) — los tooltips del navegador salen en inglés siempre y no se pueden estilar. Todos los forms usan `noValidate` + estado `fieldErrors` + `<span className="field-error">`, ver `Login.tsx`/`Register.tsx`/`Profile.tsx`/`CreateEvent.tsx` como referencia. Si el backend no valida algo (ej. longitud de password), agregar el check en el frontend también — no asumir que el backend cubre el caso.
- **Migraciones**: hay una sola migración consolidada (`c9285c7438c8_initial_schema.py`) más los cambios incrementales desde ahí. No hay base de datos de producción todavía, así que si hace falta consolidar de nuevo es seguro (verificar con autogenerate contra una DB de scratch antes de aplicar).
- **Notificaciones push**: nunca asumir que "el navegador tiene una `PushSubscription`" significa "el usuario actual la activó" — un browser solo mantiene una suscripción por origen, compartida entre todos los usuarios que se loguean en ese dispositivo. Usar siempre `getMyPushSubscription()` (verifica contra `GET /users/me/push-subscriptions`), nunca `getPushSubscription()` a secas, para decidir qué mostrar en la UI.

## Testing

- pytest con mocks (`unittest.mock.patch`) para todo lo que pegue a servicios externos — nunca llamadas reales a `webpush`/push services en tests. Ver `tests/test_push.py`.
- `tests/conftest.py` trunca las tablas entre tests contra una DB real de test (`privento_test`), no usa sqlite ni mocks de DB.

## Limitación de entorno conocida

El browser pane integrado de Claude Code (Claude Desktop) **bloquea el registro de Service Workers** a nivel de motor (falla con "unknown error" genérico aunque `/sw.js` sirva bien) y `Notification.permission` siempre da `"denied"` por default. No es un bug de la app. Para verificar cambios de push/PWA en este entorno: probar los endpoints del backend directo con `requests`/curl, y para UI, hardcodear temporalmente el estado del componente (con backup del archivo original) para verificar visualmente, después revertir. Pedirle al usuario que confirme en un browser real cuando el cambio dependa de Service Worker/Notification APIs reales.
