from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import admin, attendees, auth, event_polls, events, users

app = FastAPI(title="Prendete API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(users.router)
app.include_router(events.router)
app.include_router(attendees.router)
app.include_router(event_polls.router)


# HEAD too: uptime/keep-alive pingers and Render's wake-up page probe with HEAD, and a 405 there
# reads as a failed check.
@app.api_route("/health", methods=["GET", "HEAD"])
def health():
    return {"status": "ok"}
