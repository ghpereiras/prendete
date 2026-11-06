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

    # Comma-separated emails allowed to open the admin dashboard.
    admin_emails: str = ""

    # "Create with AI" (AWS Bedrock). An empty model id turns the feature off: the endpoint answers 503
    # and nothing else in the app changes. Credentials left empty fall back to boto3's default chain
    # (env vars, ~/.aws, an instance role); they are explicit here so a local .env works too.
    aws_region: str = "us-east-1"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    bedrock_model_id: str = ""
    ai_timeout_seconds: int = 20
    # Caps on how many model calls are made, per user and across the whole app, in any 24 hours.
    # They are the spending ceiling: an AWS budget alert only emails, it never stops anything.
    ai_daily_limit_per_user: int = 10
    ai_daily_limit_global: int = 300

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


    @property
    def admin_email_list(self) -> set[str]:
        return {e.strip().lower() for e in self.admin_emails.split(",") if e.strip()}


settings = Settings()
