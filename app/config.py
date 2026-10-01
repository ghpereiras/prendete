from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://prendete:prendete@localhost:5432/prendete"
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    vapid_public_key: str
    vapid_private_key: str
    vapid_contact_email: str

    cors_origins: str = "http://localhost:5173"

    brevo_api_key: str
    email_from_address: str = "no-reply@prendete.ar"
    email_from_name: str = "Prendete"
    frontend_url: str = "http://localhost:5173"

    # OAuth Web client ID from Google Cloud Console; empty disables Google sign-in.
    google_client_id: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
