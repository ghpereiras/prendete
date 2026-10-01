# Plan: dashboard de métricas (admin)

**Objetivo:** una pantalla solo para administradores con usuarios y eventos totales, altas en el último día / semana / mes, cuántos usuarios se registraron con contraseña y cuántos con Google, y otras métricas relevantes. Estado: **implementado** (decisiones tomadas más abajo).

## 1. Dónde vive

Una página `/admin` dentro de la propia app, alimentada por un único endpoint `GET /admin/stats`. Es lo más simple para la cantidad de métricas y reusa el stack. Alternativa descartada por ahora: una herramienta externa (Metabase/Grafana) conectada a Neon, que es más potente pero suma otro servicio que mantener.

**Quién es admin:** variable de entorno `ADMIN_EMAILS` (lista separada por comas), sin columna nueva ni UI para promover usuarios. Se exige además email verificado. El backend expone `is_admin` en `/users/me` para que el frontend muestre el link "Panel" en el menú de cuenta solo a admins; el control real está en el endpoint (403 si no es admin).

## 2. Método de acceso (decisión: sin columna nueva)

Se asume que las cuentas con `hashed_password IS NULL` son de Google y el resto "con contraseña". Limitación aceptada: quien se registró con Google y después puso una contraseña (por "olvidé mi contraseña") cuenta como "con contraseña". Si más adelante hace falta exactitud, se agrega una columna `signup_method` con migración de relleno.

## 3. Métricas (v1, sin cambios de esquema salvo `signup_method`)

Ventanas móviles: últimas 24 hs, 7 días y 30 días.

**Usuarios**
- Total y nuevos por ventana.
- Por método de registro y con/sin contraseña.
- Email verificado vs sin verificar, y cuántos sin verificar ya pasaron los 7 días de gracia (cuentas bloqueadas).
- Con foto, con notificaciones push activadas.
- Por idioma (es/en).
- Serie diaria de altas de los últimos 30 días (gráfico de barras).

**Eventos**
- Total y nuevos por ventana.
- Próximos vs pasados.
- Promedio de asistentes por evento y cuántos tienen cupo limitado.

**Encuestas**
- Total y nuevas por ventana.
- Abiertas vs resueltas (tasa de conversión encuesta → evento) y promedio de votantes.

**Participación**
- Asistencias totales y nuevas por ventana (`attendees.joined_at`).
- "Usuarios activos" aproximado: los que crearon un evento, se sumaron o votaron en la ventana (se calcula con tablas existentes).
- Usuarios sin ningún evento ni asistencia (se registraron y no hicieron nada).
- Opcional: últimas 10 altas (nombre, método, fecha). Es solo para admins.

**Limitaciones a tener presentes:** las cuentas eliminadas no dejan rastro (borrado real), así que no hay métrica de bajas salvo que se agregue un contador. No hay "último acceso" por usuario; si se lo quiere para saber activos reales, sería una v2 con una columna `last_seen_at` actualizada con throttling.

## 4. Implementación

**Backend**
- `app/config.py`: `admin_emails`. Dependencia `require_admin` en `app/auth.py`.
- `app/routers/admin.py`: `GET /admin/stats`, consultas con `COUNT(*) FILTER (WHERE created_at >= now() - interval '7 days')`, una consulta por tabla. La serie diaria agrupa con `date_trunc('day', created_at AT TIME ZONE 'America/Argentina/Buenos_Aires')`.
- `app/schemas/admin.py`: respuesta tipada.
- `UserRead.is_admin` (calculado desde `ADMIN_EMAILS`).
- Tests (`tests/test_admin.py`): conteos y ventanas, 401 sin sesión, 403 para no admin y para admin sin email verificado.

**Frontend**
- Ruta `/admin` bajo `ProtectedRoute` que redirige si `!user.is_admin`; link "Panel" en `AccountMenu` solo para admins.
- `pages/Admin.tsx`: tarjetas con números, barras de proporción (contraseña/Google, verificados/no) y gráfico de altas diarias en SVG/CSS puro, sin librería de gráficos.
- Textos en `es.json` y `en.json`.

## 5. Consideraciones

- **Privacidad:** solo agregados, sin emails en pantalla salvo la lista opcional de últimas altas, visible solo para admins.
- **Render free tier:** abrir el panel despierta el backend; se ve el aviso de "servidor despertando" que ya existe.
- **Rendimiento:** con el volumen actual cada consulta es trivial; no hace falta caché.

## 6. Orden y esfuerzo (~medio día)

2. `ADMIN_EMAILS`, `require_admin`, `is_admin` en `/users/me` (20 min).
3. Endpoint `/admin/stats` + tests (1,5 hs).
4. Página `/admin` + link en el menú + i18n (1,5 hs).
5. Probar con datos de `seed_data.py` y documentar `ADMIN_EMAILS` en `DEPLOY.md` y `.env.example` (20 min).

## Decisiones tomadas

- Admin por `ADMIN_EMAILS` (sin columna `is_admin`); el email tiene que estar verificado.
- Sin `last_seen_at`: "usuarios activos" se calcula por actividad (creó evento o encuesta, se sumó o votó).
- Incluye la lista de las últimas 10 altas.
- En producción hay que cargar `ADMIN_EMAILS` en Render con el email con el que entrás.
