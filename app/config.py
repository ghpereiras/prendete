from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://privento:privento@localhost:5432/privento"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
