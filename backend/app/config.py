from pydantic_settings import BaseSettings, SettingsConfigDict
from cryptography.fernet import Fernet
#from cryptography.fernet import InvalidToken
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_env: str = "dev"
    database_url: str = "sqlite:///./pharmacy.db"
    jwt_secret: str = "dev-only-secret"
    otp_secret: str = "dev-only-otp"
    fernet_key: str = ""
    gemini_api_key: str = ""
    cors_origins: str = "http://localhost:5173"   # comma-separated
    otp_requests_per_10_min: int = 5
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


def assert_safe_config() -> None:
    """Refuse to start outside dev with placeholder or invalid secrets."""
    if settings.app_env == "dev":
        return

    weak = [
        n for n, v in {
            "JWT_SECRET": settings.jwt_secret,
            "OTP_SECRET": settings.otp_secret,
        }.items()
        if v in ("", "change-me", "dev-only-secret", "dev-only-otp")
        or len(v) < 24
    ]

    try:
        Fernet(settings.fernet_key.encode())
    except (ValueError, TypeError):
        weak.append("FERNET_KEY")

    if weak:
        raise RuntimeError(
            f"Unsafe configuration for APP_ENV={settings.app_env}: "
            f"set strong values for {', '.join(weak)}"
        )