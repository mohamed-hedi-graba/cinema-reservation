from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    test_database_url: str
    app_env: str = "development"
    log_level: str = "INFO"
    stripe_secret_key: str = "sk_test_mock"
    stripe_webhook_secret: str = "whsec_mock"
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_user: str = ""
    smtp_password: str = ""


settings = Settings()
