# Plan de deploy

Todavía no productivizado — esto es el plan acordado, no algo ya implementado. Referencia para cuando se ejecute.

## Stack elegido

- **Frontend**: Render Static Site (gratis, sin sleep — solo sirve archivos estáticos, no corre un proceso).
- **Backend**: Render Web Service, free tier (duerme tras ~15 min sin requests, cold start de ~30-60s al despertar; el workspace tiene 750 hs/mes gratis compartidas entre servicios free, lo justo para un solo servicio corriendo todo el mes con poco margen — no alcanza para mantenerlo siempre despierto con un ping externo sin arriesgarse a agotarlas).
- **DB**: [Neon](https://neon.tech) (Postgres serverless, free tier permanente).
- **Dominio**: `prendete.ar`, comprado en nic.ar.

### Cold-start del backend

En vez de pagar un upgrade o mantenerlo siempre despierto con un cron externo (ver nota de las 750 hs arriba), se mitiga con UX: el frontend pinguea `/health` apenas carga la app (`frontend/src/App.tsx`, fire-and-forget) para que el backend empiece a despertar antes de que el usuario termine de loguearse, y si el login igual tarda más de ~4s se muestra un aviso ("el servidor puede tardar unos segundos...") en vez de dejar el botón colgado sin explicación (`frontend/src/pages/Login.tsx`). Ya implementado.

### SPA fallback (rutas del frontend)

El static site de Render sirve archivos por path exacto — abrir directamente una ruta de React Router (ej. un link de invitación `/invite/:token` en otro navegador, no navegado por click dentro de la app) devuelve 404 porque no existe un archivo físico en ese path. Se soluciona con `frontend/public/_redirects` (Vite lo copia a `dist/` en el build):

```
/*    /index.html   200
```

Así cualquier path devuelve `index.html` y React Router se hace cargo del ruteo del lado del cliente. Ya implementado — si se recrea el static site desde cero no hace falta configurar nada aparte en el dashboard de Render, viaja con el build.

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
- **Panel de métricas** (`/admin`): cargar `ADMIN_EMAILS` en el backend con el/los emails que pueden abrirlo (separados por coma). La cuenta tiene que tener el email verificado; las cuentas de Google ya lo están.
- **Google Sign-In** ("Continuar con Google"): crear un OAuth Client ID tipo "Web" en Google Cloud Console (APIs y servicios → Credenciales; pantalla de consentimiento externa con scopes básicos email/profile, no requiere verificación de Google). Orígenes JS autorizados: `https://prendete.ar` y `http://localhost:5173`. URIs de redirección autorizadas: `https://prendete.ar/auth/google/callback` y `http://localhost:5173/auth/google/callback`. Cargar el mismo Client ID como `GOOGLE_CLIENT_ID` en el backend y `VITE_GOOGLE_CLIENT_ID` en el frontend (build-time); con la variable vacía el botón no se muestra. La migración `fbfa7bab5f4e` (hace nullable `users.hashed_password`) tiene que correrse antes de deployar el backend.

## Backups de la base

Un workflow de GitHub Actions (`.github/workflows/db-backup.yml`) hace todos los días a las 04:00 (Argentina) un dump de la base de Neon, lo cifra con [age](https://github.com/FiloSottile/age) y lo guarda como **artefacto del workflow**, que GitHub borra solo a los **14 días**. Es una precaución: la app es simple y no se espera restaurar, pero con esto una pérdida de datos o de la cuenta de Neon no es definitiva. El dump se hace con una conexión de solo lectura y los archivos están cifrados, así que que vivan en GitHub no expone los datos.

Limitaciones a tener presentes: los backups están en el mismo proveedor que el código (si se perdiera la cuenta de GitHub, se perderían con ella), y los artefactos cuentan contra la cuota de almacenamiento de la cuenta (en el plan gratis de repos privados son unos 500 MB en total; mirar Settings > Billing si la base crece). Si algún día hace falta separar los backups de GitHub, el siguiente paso es subirlos a un bucket externo (Cloudflare R2 o Backblaze B2).

### Configuración (una sola vez)

1. **Neon**: anotar la versión de Postgres del proyecto y ponerla en `PG_MAJOR` del workflow (el cliente tiene que ser igual o más nuevo). Crear un rol de solo lectura desde el SQL Editor, conectado como el dueño de la base:

   ```sql
   CREATE ROLE backup_ro LOGIN PASSWORD '<una-contraseña-larga>';
   GRANT CONNECT ON DATABASE neondb TO backup_ro;  -- cambiar neondb por el nombre real
   GRANT USAGE ON SCHEMA public TO backup_ro;
   GRANT SELECT ON ALL TABLES IN SCHEMA public TO backup_ro;
   GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO backup_ro;
   ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO backup_ro;
   ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON SEQUENCES TO backup_ro;
   ```

   La URL para el secret es la *direct connection* (host sin `-pooler`) con ese rol, en formato `postgresql://backup_ro:<pass>@<host>/<db>?sslmode=require` (sin `+psycopg`).
2. **Clave de cifrado**: `age-keygen -o prendete-backup.key` (en Ubuntu: `sudo apt install age`). Imprime la clave pública (`age1...`) que va al secret `AGE_PUBLIC_KEY`. El archivo `prendete-backup.key` es la clave **privada**: guardarlo en el gestor de contraseñas (con una segunda copia en otro lugar) y borrarlo del disco. Sin esa clave los backups no se pueden abrir, y nunca va al repo ni a GitHub.
3. **healthchecks.io** (recomendado): crear un check con período de 1 día y gracia de 2 horas; su URL de ping va al secret `HEALTHCHECK_URL`. Avisa por mail si el backup deja de correr, incluso si GitHub desactiva el cron por inactividad del repo.
4. **GitHub** → Settings → Secrets and variables → Actions → crear: `BACKUP_DATABASE_URL`, `AGE_PUBLIC_KEY` y `HEALTHCHECK_URL`.
5. Correrlo a mano: Actions → "Database backup" → *Run workflow*. Confirmar que la corrida termina bien y que aparece el artefacto `prendete-YYYY-MM-DD` al final de la página de la corrida.
6. **Probar una restauración** (ver abajo) apenas el primer backup esté listo, y repetirlo de vez en cuando. Un backup que nunca se restauró no está probado.

### Restaurar

Hace falta `pg_restore` (paquete `postgresql-client`, mismo major o más nuevo que el del workflow), `age` y la clave privada.

```bash
# 1. Bajar el backup que se quiere: desde la página de la corrida en GitHub
#    (Actions > Database backup > la corrida > Artifacts), o con la CLI `gh`:
gh run download <run-id> -n prendete-YYYY-MM-DD   # deja el archivo en ./prendete-YYYY-MM-DD/

# 2. Restaurar en una base NUEVA y vacía
AGE_IDENTITY_FILE=prendete-backup.key scripts/restore_backup.sh \
  prendete-YYYY-MM-DD/prendete-YYYY-MM-DD.dump.age "postgresql://usuario:pass@host/basenueva"
```

- **Prueba local**: el Postgres del `docker-compose.yml` es la versión 16, más vieja que la de Neon (18), así que para probar levantar uno de la misma versión (`docker run --rm -d --name pgtest -e POSTGRES_PASSWORD=test -p 5433:5432 postgres:18`) y restaurar en `postgresql://postgres:test@localhost:5433/postgres`. El `pg_restore` de tu máquina tiene que ser 18 o más nuevo (en Ubuntu: agregar el repo PGDG con `sudo /usr/share/postgresql-common/pgdg/apt.postgresql.org.sh` e instalar `postgresql-client-18`).
- **Si hay que recuperar producción**: crear un proyecto o branch nuevo en Neon, restaurar ahí, comprobar `alembic current` contra la head del código, cambiar `DATABASE_URL` en Render y redeployar, y probar login y un evento. No pisar la base original hasta verificar.
- Las cuentas que se eliminaron después de la fecha del backup reaparecen al restaurarlo; habría que volver a borrarlas.
- Además del dump hay secretos que no están en la base y conviene tener en el gestor de contraseñas: `SECRET_KEY`, el par VAPID (si se pierde la clave privada, todas las suscripciones push dejan de funcionar), `GOOGLE_CLIENT_ID`, `BREVO_API_KEY` y las credenciales de Render, Neon, Cloudflare y Google Cloud.

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
