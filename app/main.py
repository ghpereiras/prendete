from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import attendees, auth, events, users

app = FastAPI(title="Privento API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(events.router)
app.include_router(attendees.router)


@app.get("/health")
def health():
    return {"status": "ok"}
