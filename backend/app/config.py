from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_env: str = "dev"
    database_url: str = "sqlite:///./pharmacy.db"
    jwt_secret: str = "dev-only-secret"
    otp_secret: str = "dev-only-otp"
    fernet_key: str = ""
    gemini_api_key: str = ""
    upload_dir: str = "./uploads"
    max_upload_bytes: int = 5 * 1024 * 1024
    otp_ttl_seconds: int = 300
    otp_max_attempts: int = 5


settings = Settings()
