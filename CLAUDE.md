# CLAUDE.md

Guide for working in this repo. For end-user features and setup see [README.md](README.md); for the deployment notes, [DEPLOY.md](DEPLOY.md). This file is about how to work on the code, not what the app does.

## Stack

- Backend: FastAPI + SQLAlchemy 2.0 + Alembic + PostgreSQL, at the repo root (`app/`). Venv in `.venv/` (`source .venv/bin/activate`).
- Frontend: React 19 + Vite + TypeScript in `frontend/`, react-router-dom v6, react-i18next (es/en, default es).
- Auth: JWT (PyJWT) + bcrypt.

## Commands

```bash
source .venv/bin/activate && python -m pytest -q       # backend tests (fast, always run after touching app/)
cd frontend && npx tsc -b --noEmit                       # frontend typecheck (always run after touching frontend/src)
cd frontend && npm run dev                               # dev server
alembic upgrade head                                     # apply pending migrations
alembic revision --autogenerate -m "message"             # new migration
```

## Project conventions

- **Language**: the user writes in Spanish, and the UI strings (i18n) are in es/en, but code comments, variable names, commit messages and the repo's documentation are in English.
- **Self-service endpoints**: for actions on the authenticated user's own resource, prefer `PATCH`/`DELETE /events/{event_id}/attendance` (it acts on the current user's row, with no ID) over a generic `/attendance/{id}`. Same pattern for `/users/me/*`.
- **No "soft-delete" rows**: the `Attendee` model has no `status` — leaving an event deletes the row outright. Don't reintroduce pending/declined-style states unless the user explicitly asks for it (it was already simplified once at their request).
- **Confirmation modals**: reuse the CSS classes `.confirm-modal-backdrop` / `.confirm-modal` / `.confirm-modal-actions` (defined in `App.css`) for any new popup. The `ConfirmModal.tsx` component itself is only for destructive confirmations (it forces the button to the red `.danger` style) — for a neutral popup (like `NotificationPrompt.tsx`), copy the class pattern but don't import the component.
- **Form validation**: no native HTML5 validation (`required`, `minLength`, `type="email"` without `noValidate`) — the browser's tooltips are always in English and can't be styled. Every form uses `noValidate` + a `fieldErrors` state + `<span className="field-error">`; see `Login.tsx`/`Register.tsx`/`Profile.tsx`/`CreateEvent.tsx` as a reference. If the backend doesn't validate something (e.g. password length), add the check on the frontend too — don't assume the backend covers it.
- **Migrations**: there IS a production database (Neon), and its start command runs `alembic upgrade head` on every deploy. Never edit or consolidate a migration that has already been applied; add a new one instead, additive when possible (see "Rollbacks" in DEPLOY.md). Watch the manual `create_foreign_key`/`drop_constraint` at the end of `upgrade`/start of `downgrade` for the circular FK `event_polls.resolved_date_option_id` (`use_alter=True`) in the initial migration — `op.create_table()` renders it inline but silently drops it because there is no `metadata.create_all()` in between to add it afterwards; it has to be added back by hand if a migration is ever regenerated with autogenerate.
- **Push notifications**: never assume "the browser has a `PushSubscription`" means "the current user enabled it" — a browser keeps only one subscription per origin, shared by every user who logs in on that device. Always use `getMyPushSubscription()` (it checks against `GET /users/me/push-subscriptions`), never a bare `getPushSubscription()`, to decide what to show in the UI.

## Testing

- pytest with mocks (`unittest.mock.patch`) for anything that hits external services — never real calls to `webpush`/push services or to the email provider in tests. See `tests/test_push.py`.
- `tests/conftest.py` truncates the tables between tests against a real test DB (`prendete_test`); it uses neither sqlite nor DB mocks.

## Known environment limitation

Claude Code's built-in browser pane (Claude Desktop) **blocks Service Worker registration** at the engine level (it fails with a generic "unknown error" even though `/sw.js` is served fine) and `Notification.permission` is always `"denied"` by default. It isn't an app bug. To verify push/PWA changes in this environment: test the backend endpoints directly with `requests`/curl, and for the UI, temporarily hardcode the component's state (with a backup of the original file) to check it visually, then revert. Ask the user to confirm in a real browser when the change depends on real Service Worker/Notification APIs.
