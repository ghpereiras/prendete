import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

TEST_DB_NAME = "prendete_test"
ADMIN_DATABASE_URL = "postgresql+psycopg://prendete:prendete@localhost:5432/prendete"
TEST_DATABASE_URL = f"postgresql+psycopg://prendete:prendete@localhost:5432/{TEST_DB_NAME}"


def _ensure_test_database() -> None:
    admin_engine = create_engine(ADMIN_DATABASE_URL, isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": TEST_DB_NAME}
        ).scalar()
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{TEST_DB_NAME}"'))
    admin_engine.dispose()


@pytest.fixture(scope="session")
def engine():
    _ensure_test_database()
    engine = create_engine(TEST_DATABASE_URL)
    # drop_all first: create_all alone won't pick up column changes on tables
    # that already exist from a previous run against an older model version.
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture()
def db_session(engine):
    with engine.connect() as conn:
        conn.execute(text("TRUNCATE TABLE attendees, events, users RESTART IDENTITY CASCADE"))
        conn.commit()

    session = sessionmaker(bind=engine, autocommit=False, autoflush=False)()
    yield session
    session.close()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def register(
    client: TestClient,
    email: str,
    password: str = "secret123",
    first_name: str = "Test",
    last_name: str = "User",
):
    return client.post(
        "/users",
        json={"email": email, "first_name": first_name, "last_name": last_name, "password": password},
    )


def login(client: TestClient, email: str, password: str = "secret123") -> str:
    response = client.post("/auth/login", data={"username": email, "password": password})
    return response.json()["access_token"]


def register_and_login(
    client: TestClient,
    email: str,
    password: str = "secret123",
    first_name: str = "Test",
    last_name: str = "User",
) -> str:
    register(client, email, password, first_name, last_name)
    return login(client, email, password)


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
