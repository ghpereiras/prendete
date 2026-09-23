from fastapi import FastAPI

from app.routers import events, invitations, users

app = FastAPI(title="Privento API")

app.include_router(users.router)
app.include_router(events.router)
app.include_router(invitations.router)


@app.get("/health")
def health():
    return {"status": "ok"}
