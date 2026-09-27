# Plan de deploy

Todavía no productivizado — esto es el plan acordado, no algo ya implementado. Referencia para cuando se ejecute.

## Stack elegido

- **Frontend**: Render Static Site (gratis, sin sleep — solo sirve archivos estáticos, no corre un proceso).
- **Backend**: Render Web Service, free tier (duerme tras ~15 min sin requests, cold start de ~30-50s al despertar).
- **DB**: [Neon](https://neon.tech) (Postgres serverless, free tier permanente).
- **Dominio**: comprado en nic.ar.

### Por qué Neon y no la Postgres de Render

El free tier de Postgres de Render **expira a los 30 días** (borra la base si no se upgradea a pago) — a diferencia de sus web services, que duermen pero no expiran. Por eso la DB va aparte.

Entre las alternativas gratis evaluadas:
- **Neon**: se suspende el cómputo por inactividad pero **se despierta solo con la próxima conexión**, sin acción manual. Elegido por esto.
- **Supabase**: también tiene free tier, pero si el proyecto no tiene actividad en 7 días se pausa y **hay que reactivarlo a mano** desde el dashboard — no sirve para una app de bajo tráfico que se mantenga sola.

## Notificaciones (contexto para el cron)

- Notificaciones disparadas por una acción del usuario (alguien se suma a un evento, deja un comentario) no necesitan infraestructura extra: el servidor ya está despierto atendiendo esa request.
- Notificaciones programadas por horario (recordatorios tipo "tu evento empieza en 1 hora") si necesitan algo: como Render duerme el free tier, hace falta un **cron externo gratuito** (cron-job.org, GitHub Actions con horario programado, etc.) que le pegue a un endpoint propio (ej. `/check-and-send-notifications`) cada 5-15 min. Eso despierta el servicio si estaba dormido y dispara el envío de lo que esté vencido. Sin esto, un scheduler interno (`setInterval`/cron en el mismo proceso) no se dispararía mientras el servicio está dormido.

## Configuración de deploy

1. Conectar el repo de GitHub a ambos servicios de Render (web service + static site), auto-deploy en push a `main`.
2. Backend — *start command*:
   ```
   alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
   Así las migraciones corren solas en cada deploy, no hace falta acordarse de aplicarlas a mano.
3. Frontend — *build command*: `npm run build`, *publish directory*: `dist`.
4. Configurar el *health check path* del backend en `/health` (ya existe en `app/main.py`) — Render lo usa para no promocionar un deploy roto. Confirmar en la doc de Render si el comportamiento de zero-downtime difiere entre el plan free y uno pago.

### Variables de entorno a cargar en Render

- Backend: `DATABASE_URL` (connection string de Neon), `SECRET_KEY` (nueva, generada para prod — nunca la de dev).
- Frontend (build-time): `VITE_API_URL` (URL del backend en prod), `VITE_GOOGLE_MAPS_API_KEY`.
- En Google Cloud Console, agregar el dominio real a las "Referentes HTTP" permitidos de la API key (hoy solo tiene `localhost:5173/*`).

## Rollbacks

Render guarda el historial de deploys con un botón "Rollback to this deploy" — un click, sin tocar git. Aplica tanto al backend como al static site.

**Cuidado**: un rollback revierte el código, no el esquema de la DB. Si el deploy que se revierte incluía una migración, el código viejo tiene que seguir funcionando contra el esquema nuevo, o hay que migrar para atrás a mano con `alembic downgrade` contra Neon. Para minimizar este riesgo, seguir escribiendo migraciones aditivas cuando se pueda (agregar columnas nullable en vez de renombrar/borrar en el mismo deploy).

## Upgrades

Tanto en Render como en Neon, pasar de free a un plan pago es cambiar el plan desde el dashboard — no requiere tocar código ni configuración.

## Dominio (nic.ar)

Agregar el dominio custom en cada servicio de Render (el static site para `tudominio.ar`, el web service para `api.tudominio.ar` u otro subdominio elegido). Render da los registros DNS exactos (normalmente CNAME para subdominios) para cargar en el panel de "Zona DNS" de nic.ar. Para el dominio raíz sin subdominio, evaluar redirigir a `www` para evitar problemas de DNS con el apex.
