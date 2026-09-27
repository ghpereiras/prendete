from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://privento:privento@localhost:5432/privento"
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    vapid_public_key: str
    vapid_private_key: str
    vapid_contact_email: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
