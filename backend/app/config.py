from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_env: str = "dev"
    database_url: str = "sqlite:///./pharmacy.db"
    jwt_secret: str = "dev-only-secret"
    otp_secret: str = "dev-only-otp"
    fernet_key: str = ""
    gemini_api_key: str = ""
    ai_provider: str = "auto"  # auto | gemini | mock
    gemini_model: str = "gemini-2.5-flash"
    ai_timeout_seconds: int = 20
    ai_confidence_threshold: float = 0.7
    match_threshold: float = 0.75
    upload_dir: str = "./uploads"
    max_upload_bytes: int = 5 * 1024 * 1024
    otp_ttl_seconds: int = 300
    otp_max_attempts: int = 5


settings = Settings()
