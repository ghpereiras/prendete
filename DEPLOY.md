# Plan de deploy

Todavía no productivizado — esto es el plan acordado, no algo ya implementado. Referencia para cuando se ejecute.

## Stack elegido

- **Frontend**: Render Static Site (gratis, sin sleep — solo sirve archivos estáticos, no corre un proceso).
- **Backend**: Render Web Service, free tier (duerme tras ~15 min sin requests, cold start de ~30-60s al despertar; el workspace tiene 750 hs/mes gratis compartidas entre servicios free, lo justo para un solo servicio corriendo todo el mes con poco margen — no alcanza para mantenerlo siempre despierto con un ping externo sin arriesgarse a agotarlas).
- **DB**: [Neon](https://neon.tech) (Postgres serverless, free tier permanente).
- **Dominio**: `prendete.ar`, comprado en nic.ar.

### Cold-start del backend

En vez de pagar un upgrade o mantenerlo siempre despierto con un cron externo (ver nota de las 750 hs arriba), se mitiga con UX: el frontend pinguea `/health` apenas carga la app (`frontend/src/App.tsx`, fire-and-forget) para que el backend empiece a despertar antes de que el usuario termine de loguearse, y si el login igual tarda más de ~4s se muestra un aviso ("el servidor puede tardar unos segundos...") en vez de dejar el botón colgado sin explicación (`frontend/src/pages/Login.tsx`). Ya implementado.

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

- Backend: `DATABASE_URL` (connection string de Neon — usar la *direct connection*, no la *pooled*, porque el backend ya mantiene su propio pool de conexiones con SQLAlchemy; ojo con anteponer `postgresql+psycopg://` en vez de `postgresql://`, es el driver que usa el proyecto), `SECRET_KEY` (nueva, generada para prod — nunca la de dev), `VAPID_PUBLIC_KEY`/`VAPID_PRIVATE_KEY`/`VAPID_CONTACT_EMAIL` (par VAPID nuevo también, no el de dev).
- Frontend (build-time): `VITE_API_URL` (URL del backend en prod), `VITE_GOOGLE_MAPS_API_KEY`, **`VITE_VAPID_PUBLIC_KEY`** (tiene que ser exactamente la misma `VAPID_PUBLIC_KEY` del backend de prod — si no coincide, `pushManager.subscribe()` falla en el browser).
- En Google Cloud Console, agregar el dominio real a las "Referentes HTTP" permitidos de la API key (hoy solo tiene `localhost:5173/*`).

## Rollbacks

Render guarda el historial de deploys con un botón "Rollback to this deploy" — un click, sin tocar git. Aplica tanto al backend como al static site.

**Cuidado**: un rollback revierte el código, no el esquema de la DB. Si el deploy que se revierte incluía una migración, el código viejo tiene que seguir funcionando contra el esquema nuevo, o hay que migrar para atrás a mano con `alembic downgrade` contra Neon. Para minimizar este riesgo, seguir escribiendo migraciones aditivas cuando se pueda (agregar columnas nullable en vez de renombrar/borrar en el mismo deploy).

## Upgrades

Tanto en Render como en Neon, pasar de free a un plan pago es cambiar el plan desde el dashboard — no requiere tocar código ni configuración.

## Dominio (nic.ar)

**nic.ar no tiene editor de zona DNS propio** — no se pueden cargar registros A/CNAME/TXT/MX directamente ahí. Solo permite "delegar" el dominio a los nameservers de un proveedor DNS externo, que es donde se cargan todos los registros de verdad. Camino elegido:

1. Cuenta gratis en [Cloudflare](https://www.cloudflare.com/) (DNS gratis, soporta todos los tipos de registro que hacen falta: TXT/MX/SPF/DKIM de Zoho, CNAME de Render).
2. Agregar `prendete.ar` como sitio en Cloudflare — da 2 nameservers propios.
3. En nic.ar: botón **"Delegar"** (no "Transferir", que es cambio de registrador/titular) → "Agregar una nueva delegación" → cargar esos 2 nameservers → Guardar. Propagación: horas hasta 24-48hs.
4. De ahí en adelante, **todos** los registros (el TXT de verificación de Zoho, MX, SPF, DKIM, DMARC, y los CNAME/A de Render para el static site y `api.prendete.ar`) se cargan en el panel de Cloudflare, no en nic.ar.

Para el dominio raíz sin subdominio, evaluar redirigir a `www` para evitar problemas de DNS con el apex (Cloudflare soporta CNAME flattening en el apex, así que probablemente no haga falta el redirect).

## Email

No se envía ningún email desde la app todavía (solo push notifications) — esto es exclusivamente para casillas humanas y para dejar reservado el remitente que se usará el día que se implemente envío transaccional (reset de contraseña, etc.), que **no está en el alcance actual**.

- **`redes@prendete.ar` / `info@prendete.ar`**: [Zoho Mail](https://www.zoho.com/mail/) plan gratuito — hasta 5 casillas reales con dominio propio (webmail + IMAP/SMTP), no es solo un forward.
- **`no-reply@prendete.ar`**: se crea también como casilla de Zoho por ahora (entra en el límite de 5 gratis), solo para que exista y no rebote si alguien le escribe. No se usa como remitente hasta implementar el envío transaccional — en ese momento se evalúa si conviene migrarla a un proveedor tipo Resend (DKIM propio, no choca con el de Zoho porque usan selectores distintos).
- **`admin@prendete.ar`**: cuarta casilla de Zoho, dedicada a las altas de las cuentas de infraestructura (Render, Neon) — ver orden de altas más abajo. Mantiene esas notificaciones (billing, seguridad, outages) separadas de `redes@`, que es la que va a recibir mensajes públicos de gente escribiendo por redes sociales.

### DNS de email (misma zona que el resto)

- MX + TXT de verificación de dominio → los que pida Zoho Mail al agregar `prendete.ar`.
- **SPF**: un único TXT (no puede haber dos registros SPF en la misma zona) con el `include:` de Zoho — dejar la sintaxis lista para agregar otro `include:` el día que se sume un proveedor transaccional.
- DKIM → TXT con el selector que dé Zoho.
- DMARC (recomendado, opcional en esta etapa) → TXT en `_dmarc` con política `p=none` para solo monitorear al principio.

### Orden de altas de cuentas

1. Zoho Mail: alta con el email personal actual (todavía no existe ninguna dirección `@prendete.ar`).
2. Verificar el dominio en Zoho (TXT en nic.ar) y crear las 4 casillas: `redes@`, `info@`, `no-reply@`, `admin@`.
3. Usar `admin@prendete.ar` para las altas en Render y Neon, no el email personal ni `redes@`.
4. `nic.ar` (registro del dominio) queda con el email que ya tiene de antes — cambiar el contacto/WHOIS es una operación aparte y más sensible, fuera de alcance salvo que se pida explícitamente.

### Orden sugerido de ejecución completo

1. Zoho Mail: alta + verificación de dominio + crear las 4 casillas.
2. Neon: crear la DB con `admin@prendete.ar` — **no correr `scripts/seed_data.py` contra producción** (crea usuarios demo con contraseña conocida, `password123`).
3. Backend en Render: alta con `admin@prendete.ar`, deploy, confirmar que responde en su URL `*.onrender.com` antes de tocar DNS.
4. Frontend en Render: deploy, mismo chequeo en su URL temporal.
5. Cargar todos los registros DNS juntos en nic.ar (dominio, `api`, y los de Zoho) para minimizar idas y vueltas de propagación.
6. Verificar los dominios custom en Render (frontend y backend).
7. Verificar Zoho Mail: mandar y recibir un email de prueba en cada casilla.
8. Confirmar los referrers de la Maps API key en Google Cloud Console.
