# Plan: backup de la base de producción (Neon)

**Objetivo:** perder como máximo 24 hs de datos (RPO) y reconstruir la base en menos de 1 hora (RTO), incluso si se pierde la cuenta de Neon. Estado: plan, nada implementado.

## 1. Dos capas

1. **Neon (rápido, para errores recientes):** historial de restauración a un instante + branches. En el free tier la ventana es corta; **verificar el valor exacto en el dashboard de Neon** antes de confiar en ella. Práctica extra y gratis: crear una *branch* de Neon justo antes de correr una migración riesgosa.
2. **Dump lógico diario fuera de Neon (el backup real):** protege contra borrados viejos, errores de Neon o pérdida de la cuenta.

## 2. Diseño del backup diario

- **Quién lo corre:** GitHub Actions con cron diario (`.github/workflows/db-backup.yml`, ~04:00 ART). No depende de Render (que duerme) ni de un servidor propio. El dump despierta el cómputo de Neon; el costo en horas de cómputo es despreciable.
- **Cliente `pg_dump`:** mismo major que el Postgres de Neon (ver versión en el dashboard); instalarlo desde el repo PGDG en el job, porque el de `ubuntu-latest` puede ser más viejo y falla.
- **Comando:** `pg_dump -Fc --no-owner --no-privileges "$BACKUP_DATABASE_URL"`. La URL va en formato `postgresql://` (no `postgresql+psycopg://` como la app) y con la *direct connection*.
- **Rol de solo lectura:** crear en Neon un rol `backup_ro` con `SELECT` en todo el esquema. El secret `BACKUP_DATABASE_URL` usa ese rol, nunca el dueño.
- **Validación antes de subir:** `pg_restore --list` sobre el dump (falla el job si no se puede leer) y un tamaño mínimo razonable.
- **Cifrado obligatorio:** `age -r "$AGE_PUBLIC_KEY"`. La base tiene emails, hashes de contraseña, endpoints de push y avatares. La clave privada vive solo en el gestor de contraseñas (y una copia offline), jamás en GitHub ni en el repo.
- **Destino:** Cloudflare R2, bucket **privado** (10 GB gratis, sin costo de salida; ya usás Cloudflare). Alternativa: Backblaze B2. Subida con `aws s3 cp --endpoint-url` o `rclone`.
- **Nombres:** `daily/prendete-YYYY-MM-DD.dump.age`.
- **Retención:** regla de lifecycle en R2 que borre `daily/` a los **30 días**. Ver punto 5 sobre copias mensuales.
- **Alertas:** si el job falla, GitHub manda mail. Además un ping a healthchecks.io al terminar bien (avisa si no llega en ~26 hs). Esto cubre el caso silencioso: GitHub desactiva los cron de repos sin actividad por 60 días.

### Secrets de GitHub a crear
`BACKUP_DATABASE_URL`, `AGE_PUBLIC_KEY`, `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET`, `HEALTHCHECK_URL`. El token de R2 con permiso solo de escritura sobre ese bucket.

## 3. Restauración (runbook)

Script `scripts/restore_backup.sh` (a crear): descarga el dump elegido, lo descifra con la clave privada y corre `pg_restore --no-owner --clean --if-exists -d <url_destino>`.

1. Crear un proyecto o branch nuevo en Neon (no pisar el original hasta verificar).
2. Restaurar ahí.
3. `alembic current` debe coincidir con la head del código desplegado.
4. Cambiar `DATABASE_URL` en Render, redeployar y probar login, un evento y una encuesta.

**Probar una restauración real** apenas esté armado (contra el Postgres de `docker-compose.yml`) y repetirlo cada 3 meses. Un backup sin restauración probada no cuenta.

## 4. Secretos que NO están en la base

Guardar en el gestor de contraseñas, aparte del dump: `SECRET_KEY`, el par **VAPID** (si se pierde la privada, todas las suscripciones push dejan de funcionar), `GOOGLE_CLIENT_ID`, `BREVO_API_KEY` y las credenciales de Render, Neon, Cloudflare y Google Cloud.

## 5. Interacción con "Eliminar mi cuenta" y la política de privacidad

Los backups conservan datos de cuentas ya eliminadas hasta que vence su retención. Por eso:
- Evitar retención larga: **30 días diarios** y, si se quiere histórico, mensuales con tope bajo (por ejemplo 3). Sin copias mensuales indefinidas.
- **Actualizar la política de privacidad** con una línea tipo "las copias de seguridad se conservan hasta N días".
- Aviso para el día de una restauración: las cuentas eliminadas desde la fecha del backup reaparecen; habría que volver a borrarlas.

## 6. Qué vigilar

- Los avatares son `bytea` dentro de la base: el dump crece con los usuarios. Mirar el tamaño mensualmente; si se acerca a los 10 GB de R2, considerar sacar los avatares de la base.
- Cuando cambie el major de Postgres en Neon, actualizar el cliente del workflow.

## 7. Orden y esfuerzo (~1,5–2 hs)

1. Verificar la ventana de restauración de Neon y la versión de Postgres (5 min).
2. Crear rol `backup_ro`, bucket R2 con lifecycle y token, par de claves `age` (25 min).
3. Escribir el workflow, cargar los secrets, correrlo a mano con `workflow_dispatch` (30 min).
4. Configurar healthchecks.io (10 min).
5. Escribir `restore_backup.sh`, hacer la primera restauración de prueba y documentar el runbook en `DEPLOY.md` (30 min).
6. Actualizar la política de privacidad con la retención (5 min).

## Decisiones pendientes

- ¿R2 o B2 como destino?
- ¿Frecuencia diaria o cada 12 hs (RPO 12 hs)?
- ¿Se quieren copias mensuales? (si sí, con qué tope)
