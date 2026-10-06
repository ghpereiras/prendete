# Plan: metrics dashboard (admin)

**Goal:** an admin-only screen with total users and events, sign-ups in the last day / week / month, how many users signed up with a password and how many with Google, and other relevant metrics. Status: **implemented** (decisions made at the bottom).

## 1. Where it lives

A `/admin` page inside the app itself, fed by a single `GET /admin/stats` endpoint. It is the simplest option for this number of metrics and it reuses the stack. Alternative discarded for now: an external tool (Metabase/Grafana) connected to Neon, which is more powerful but adds another service to maintain.

**Who is an admin:** the `ADMIN_EMAILS` environment variable (comma-separated list), with no new column and no UI to promote users. A verified email is also required. The backend exposes `is_admin` in `/users/me` so the frontend shows the "Dashboard" link in the account menu only to admins; the real check is in the endpoint (403 if not an admin).

## 2. Sign-up method (decision: no new column)

Accounts with `hashed_password IS NULL` are assumed to be Google ones, and the rest "with password". Accepted limitation: someone who signed up with Google and later set a password (through "forgot my password") counts as "with password". If exactness is needed later, a `signup_method` column is added with a backfill migration.

## 3. Metrics (v1, no schema changes except `signup_method`)

Rolling windows: last 24 hours, 7 days and 30 days.

**Users**
- Total and new per window.
- By sign-up method and with/without a password.
- Verified vs unverified email, and how many unverified ones are past the 7-day grace period (blocked accounts).
- With a profile picture, with push notifications enabled.
- By language (es/en).
- Daily series of sign-ups for the last 30 days (bar chart).

**Events**
- Total and new per window.
- Upcoming vs past.
- Average attendees per event and how many have a limited capacity.

**Polls**
- Total and new per window.
- Open vs resolved (poll → event conversion rate) and average number of voters.

**Participation**
- Total attendances and new ones per window (`attendees.joined_at`).
- Approximate "active users": those who created an event, joined one or voted in the window (computed from existing tables).
- Users with no event and no attendance at all (signed up and did nothing).
- Optional: the last 10 sign-ups (name, method, date). Admins only.

**Limitations to keep in mind:** deleted accounts leave no trace (real deletion), so there is no churn metric unless a counter is added. There is no "last seen" per user; if real active users are wanted, that would be a v2 with a `last_seen_at` column updated with throttling.

## 4. Implementation

**Backend**
- `app/config.py`: `admin_emails`. A `require_admin` dependency in `app/auth.py`.
- `app/routers/admin.py`: `GET /admin/stats`, queries using `COUNT(*) FILTER (WHERE created_at >= now() - interval '7 days')`, one query per table. The daily series groups with `date_trunc('day', created_at AT TIME ZONE 'America/Argentina/Buenos_Aires')`.
- `app/schemas/admin.py`: typed response.
- `UserRead.is_admin` (computed from `ADMIN_EMAILS`).
- Tests (`tests/test_admin.py`): counts and windows, 401 without a session, 403 for non-admins and for admins without a verified email.

**Frontend**
- A `/admin` route under `ProtectedRoute` that redirects if `!user.is_admin`; a "Dashboard" link in `AccountMenu` for admins only.
- `pages/Admin.tsx`: cards with numbers, proportion bars (password/Google, verified/unverified) and a daily sign-ups chart in plain SVG/CSS, with no chart library.
- Texts in `es.json` and `en.json`.

## 5. Considerations

- **Privacy:** aggregates only, with no emails on screen except the optional last-sign-ups list, visible to admins only.
- **Render free tier:** opening the dashboard wakes the backend; the existing "server waking up" notice is shown.
- **Performance:** at the current volume each query is trivial; no cache needed.

## 6. Order and effort (~half a day)

1. `ADMIN_EMAILS`, `require_admin`, `is_admin` in `/users/me` (20 min).
2. `/admin/stats` endpoint + tests (1.5 h).
3. `/admin` page + menu link + i18n (1.5 h).
4. Try it with the data from `seed_data.py` and document `ADMIN_EMAILS` in `DEPLOY.md` and `.env.example` (20 min).

## Decisions made

- Admin through `ADMIN_EMAILS` (no `is_admin` column); the email has to be verified.
- No `last_seen_at`: "active users" is computed from activity (created an event or poll, joined or voted).
- Includes the list of the last 10 sign-ups.
- In production, `ADMIN_EMAILS` has to be set in Render with the email you sign in with.
