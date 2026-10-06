from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

# Neon suspends its compute after ~5 min idle and drops every open connection ("terminating
# connection due to administrator command"). pre_ping tests a pooled connection before using it and
# reconnects (waking Neon) if it is dead, so the first request after a quiet spell doesn't fail;
# recycle keeps connections younger than the idle window.
engine = create_engine(settings.database_url, pool_pre_ping=True, pool_recycle=240)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
