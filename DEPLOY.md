# Deployment notes

How Prendete runs in production at [prendete.ar](https://prendete.ar), and how to set it up from scratch.

## Stack

- **Frontend**: Render Static Site (free, never sleeps — it only serves static files, there is no process running).
- **Backend**: Render Web Service, free tier (it sleeps after ~15 min without requests, and waking up takes anywhere from about 30 seconds to a few minutes; the workspace has 750 free hours/month shared across free services: that is enough for a single service running 24 hours a day (744 hours in a 31-day month), which is why it is kept awake all day — see "Keeping the backend awake").
- **DB**: [Neon](https://neon.tech) (serverless Postgres, permanent free tier).
- **Domain**: `prendete.ar`, bought at nic.ar, with DNS on Cloudflare.

### Backend cold start

Besides keeping it awake all day (next section), the UX softens the problem: the frontend pings `/health` as soon as the app loads (`frontend/src/App.tsx`, fire-and-forget) so the backend starts waking up before the user finishes logging in, and if login still takes more than ~4s a notice is shown ("the server may take a few seconds...") instead of leaving the button hanging with no explanation (`frontend/src/pages/Login.tsx`). Pages that load data retry while the server wakes up instead of showing a false "not found" (`loadWhileServerWakes` in `frontend/src/api/client.ts`). Already implemented.

Neon suspends its compute after ~5 minutes without queries and drops every open connection. The SQLAlchemy engine uses `pool_pre_ping` and a short `pool_recycle` (`app/database.py`) so the first request after a quiet period reconnects instead of failing.

### Keeping the backend awake (24 hours)

Render puts the backend to sleep after ~15 min without external requests (Render's own internal health checks, IP `10.233.x`, don't count: the logs showed the app shutting down exactly 15 min after the last external request). An external cron sends `HEAD https://api.prendete.ar/health` every 10 minutes, around the clock, and with that it never goes to sleep.

**Why 24 hours and not just usage hours**: the cron keeps an already-awake app awake, but it **does not wake it up if it is asleep**. On 2026-10-04 the pings from 08:00 to 12:50 received a 502 from Render (`x-render-routing: no-deploy`) without starting anything (there isn't a single log line in those hours), and the app only started when somebody opened it at 12:57. It could not be determined why Render doesn't wake up for cron-job.org's pings when a manual `curl -I` did. Since waking up isn't reliable, the design is for it to never sleep. If for some reason it goes down or sleeps anyway (a failed deploy, for example), the cron failures raise an alert and the first user to open the app wakes it up.

- **Render hours**: 24 hours × 31 days = 744 hours/month against the workspace's 750 free ones, a margin of 6 hours in 31-day months. The workspace currently has only 2 services (this web service and the static site, which doesn't use hours). **Don't add another free web service to the same workspace.** The month's usage is visible in Workspace Settings → Billing → "Monthly Included Usage" → "Free Instance Hours"; Render charges for usage above what is included.
- **`/health` doesn't touch the database** (`app/main.py`), and it has to stay that way: if it queried Neon, the pings would keep the database compute awake and use up its free hours (Neon suspends by itself after ~5 min without queries). It also answers `HEAD`, because uptime pingers and Render's wake-up page probe with it.
- **Why not GitHub Actions**: a ping every 10 min is ~100 runs a day, each billed for at least 1 min (~3000 min/month against 2000 free in private repos), and GitHub's cron runs late or skips executions, which is exactly what matters here.
- **Chosen service**: [cron-job.org](https://cron-job.org) (free). A single job:
  - Title `prendete-keepalive`, method **HEAD**, URL `https://api.prendete.ar/health`. HEAD avoids cron-job.org receiving the large HTML "Application loading" page that Render returns while the service is asleep: with GET that response exceeds the maximum size and shows up as "Failed (output too large)".
  - Cron `*/10 * * * *` (every day, at every hour). The time zone no longer matters.
  - 30 s timeout (cron-job.org's maximum). With the app awake it answers in milliseconds; if the service is asleep the ping fails (502) and doesn't wake it.
  - Email alerts after 3 consecutive failures: with the 24-hour scheme, a sustained failure means the app went down.

### SPA fallback (frontend routes)

Render's static site serves files by exact path — opening a React Router route directly (e.g. an invite link `/invite/:token` in another browser, not reached by clicking inside the app) returns 404 because there is no physical file at that path. It is fixed with `frontend/public/_redirects` (Vite copies it to `dist/` on build):

```
/*    /index.html   200
```

That way any path returns `index.html` and React Router takes over routing on the client side. Already implemented — if the static site is recreated from scratch nothing else needs configuring in Render's dashboard, it travels with the build.

### Why Neon and not Render's Postgres

Render's free Postgres tier **expires after 30 days** (it deletes the database unless you upgrade to a paid plan) — unlike its web services, which sleep but don't expire. That is why the DB is hosted elsewhere.

Among the free alternatives that were evaluated:
- **Neon**: the compute suspends when idle but **wakes up by itself on the next connection**, with no manual action. Chosen for this reason.
- **Supabase**: also has a free tier, but if the project has no activity for 7 days it is paused and **has to be reactivated by hand** from the dashboard — not suitable for a low-traffic app that should run on its own.

## Notifications (context for the cron)

- Notifications triggered by a user action (someone joins an event, leaves a comment) need no extra infrastructure: the server is already awake handling that request.
- Notifications scheduled by time (reminders like "your event starts in 1 hour") are not implemented. If they are added, note that Render sleeps the free tier, so an internal scheduler (`setInterval`/cron inside the same process) wouldn't fire while the service is asleep; the existing keep-alive cron or a dedicated one would have to call an endpoint of its own (e.g. `/check-and-send-notifications`) every 5-15 min.

## Deploy configuration

1. Connect the GitHub repo to both Render services (web service + static site), auto-deploy on push to `main`.
2. Backend — *start command*:
   ```
   alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
   That way migrations run by themselves on every deploy, no need to remember to apply them by hand.
3. Frontend — *build command*: `npm run build`, *publish directory*: `dist`.
4. Set the backend's *health check path* to `/health` (it already exists in `app/main.py`) — Render uses it to avoid promoting a broken deploy. Check Render's docs on whether zero-downtime behavior differs between the free plan and a paid one.

### Environment variables to set in Render

- Backend:
  - `DATABASE_URL`: Neon's connection string — use the *direct connection*, not the *pooled* one, because the backend already keeps its own connection pool with SQLAlchemy. Mind the `postgresql+psycopg://` prefix instead of `postgresql://`; it is the driver this project uses.
  - `SECRET_KEY`: a new one generated for prod — never the dev one.
  - `VAPID_PUBLIC_KEY`/`VAPID_PRIVATE_KEY`/`VAPID_CONTACT_EMAIL`: a new VAPID pair too, not the dev one.
  - `CORS_ORIGINS`: the production frontend's URL (`https://prendete.ar`), with no trailing slash.
  - `FRONTEND_URL`: `https://prendete.ar`, used to build the links inside emails.
  - `BREVO_API_KEY`, `EMAIL_FROM_ADDRESS`, `EMAIL_FROM_NAME`: transactional email (see "Email").
- Frontend (build-time): `VITE_API_URL` (the backend's URL in prod), `VITE_GOOGLE_MAPS_API_KEY`, **`VITE_VAPID_PUBLIC_KEY`** (it has to be exactly the prod backend's `VAPID_PUBLIC_KEY` — if it doesn't match, `pushManager.subscribe()` fails in the browser).
- In Google Cloud Console, add the real domain to the API key's allowed "HTTP referrers" (it may only have `localhost:5173/*`).
- **Metrics dashboard** (`/admin`): set `ADMIN_EMAILS` in the backend with the email(s) allowed to open it (comma-separated). The account must have a verified email; Google accounts already do.
- **Google Sign-In** ("Continue with Google"): create an OAuth Client ID of type "Web" in Google Cloud Console (APIs & Services → Credentials; external consent screen with basic email/profile scopes, which doesn't require Google verification). Authorized JavaScript origins: `https://prendete.ar` and `http://localhost:5173`. Authorized redirect URIs: `https://prendete.ar/auth/google/callback` and `http://localhost:5173/auth/google/callback`. Set the same Client ID as `GOOGLE_CLIENT_ID` in the backend and `VITE_GOOGLE_CLIENT_ID` in the frontend (build-time); with the variable empty the button isn't shown. Migration `fbfa7bab5f4e` (makes `users.hashed_password` nullable) has to run before deploying the backend. The consent screen also needs the privacy policy and terms pages (`https://prendete.ar/privacy` and `/terms`).

## Database backups

Backups are **not in this repo**: they live in a separate private repo, `ghpereiras/prendete-backups`, with its own GitHub Actions workflow. Every day at 04:00 (Argentina) it takes a dump of the Neon database, encrypts it with [age](https://github.com/FiloSottile/age) and stores it as an artifact that GitHub deletes after 14 days. The setup guide, the restore runbook and the limitations are in that repo's README.

Why it is separate: this repo is public, and the artifacts of a public repo can be downloaded by any GitHub user; GitHub also disables the cron jobs of public repos after 60 days without activity.

What to know from this repo:

- The app has nothing to do with the backup: no environment variables or code are involved. The only requirement is that `alembic current` on the restored database matches the head of this repo's migrations before pointing `DATABASE_URL` at it.
- Besides the dump there are secrets that are not in the database and are worth keeping in the password manager: `SECRET_KEY`, the VAPID pair (if the private key is lost, every push subscription stops working), `GOOGLE_CLIENT_ID`, `BREVO_API_KEY` and the credentials for Render, Neon, Cloudflare and Google Cloud.

## Rollbacks

Render keeps the deploy history with a "Rollback to this deploy" button — one click, without touching git. It applies to both the backend and the static site.

**Careful**: a rollback reverts the code, not the DB schema. If the deploy being reverted included a migration, the old code has to keep working against the new schema, or you have to migrate backwards by hand with `alembic downgrade` against Neon. To minimize this risk, keep writing additive migrations when possible (add nullable columns instead of renaming/dropping in the same deploy).

## Upgrades

On both Render and Neon, moving from free to a paid plan is a matter of changing the plan in the dashboard — no code or configuration changes needed.

## Domain (nic.ar)

**nic.ar has no DNS zone editor of its own** — you can't load A/CNAME/TXT/MX records directly there. It only lets you "delegate" the domain to the nameservers of an external DNS provider, which is where all the real records are loaded. The path taken:

1. Free account on [Cloudflare](https://www.cloudflare.com/) (free DNS, supports every record type needed: Zoho's TXT/MX/SPF/DKIM, Render's CNAMEs).
2. Add `prendete.ar` as a site in Cloudflare — it gives you 2 nameservers of its own.
3. In nic.ar: the **"Delegar"** button (not "Transferir", which is a change of registrar/holder) → "Agregar una nueva delegación" → enter those 2 nameservers → Save. Propagation: hours up to 24-48h.
4. From then on, **all** records (Zoho's verification TXT, MX, SPF, DKIM, DMARC, and Render's CNAME/A records for the static site and `api.prendete.ar`) are loaded in Cloudflare's panel, not in nic.ar.

For the bare root domain, consider redirecting to `www` to avoid DNS problems at the apex (Cloudflare supports CNAME flattening at the apex, so the redirect is probably not needed).

## Email

Two separate things share the domain:

- **Human mailboxes** — [Zoho Mail](https://www.zoho.com/mail/) free plan: up to 5 real mailboxes on your own domain (webmail + IMAP/SMTP), not just a forward. Used for the addresses people write to, plus a dedicated mailbox for the infrastructure accounts (Render, Neon, Brevo), which keeps their notifications (billing, security, outages) separate from the public-facing ones.
- **Transactional email** (account verification, password reset) — [Brevo](https://www.brevo.com/) (300 emails/day free, permanently), sent from `no-reply@prendete.ar` through its HTTP API (`app/email.py`), with the key in `BREVO_API_KEY`. Failures are logged and never break the request that triggered them.

### Email DNS (same zone as everything else)

- MX + domain verification TXT → the ones Zoho Mail asks for when adding `prendete.ar`.
- **SPF**: a single TXT (there can't be two SPF records in the same zone) containing both providers' `include:` — Zoho's and Brevo's.
- DKIM → one TXT per provider, each with its own selector, so they don't collide.
- DMARC (recommended) → TXT at `_dmarc` with policy `p=none` to only monitor at first.

### Suggested order for a from-scratch setup

1. Zoho Mail: sign up with a personal email, verify the domain (TXT in Cloudflare) and create the mailboxes.
2. Use that dedicated mailbox for the Render, Neon and Brevo sign-ups, not a personal email.
3. Neon: create the DB — **don't run `scripts/seed_data.py` against production** (it creates demo users with a known password, `password123`).
4. Backend on Render: deploy, and confirm it answers at its `*.onrender.com` URL before touching DNS.
5. Frontend on Render: deploy, same check at its temporary URL.
6. Load all the DNS records together in Cloudflare (domain, `api`, and Zoho's and Brevo's) to minimize propagation round trips.
7. Verify the custom domains in Render (frontend and backend).
8. Verify Zoho Mail: send and receive a test email on each mailbox, and trigger a verification email from the app.
9. Confirm the referrers of the Maps API key in Google Cloud Console.
10. Create the cron job that keeps the backend awake (see above).
