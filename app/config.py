from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./data/televera.db"

    @property
    def async_database_url(self) -> str:
        """Konverterar Railway's postgresql:// → postgresql+asyncpg:// för SQLAlchemy."""
        url = self.database_url
        if url.startswith("postgresql://") or url.startswith("postgres://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1) \
                      .replace("postgres://", "postgresql+asyncpg://", 1)
        return url  # SQLite-URL förblir oförändrad
    scrape_api_key: str = "change-me-in-production"
    scrape_cron_hours: str = "0,6,12,18"
    scrape_timezone: str = "Europe/Stockholm"
    scrape_stale_after_hours: int = 8
    request_timeout_seconds: int = 30
    playwright_headless: bool = True
    allowed_origins: str = "http://localhost:3000,http://localhost:8080,http://127.0.0.1:8080,https://televera.se"
    environment: str = "development"
    google_sheets_webhook_url: str = ""
    google_service_account_json: str = ""
    google_sheets_spreadsheet_id: str = ""
    google_sheets_worksheet_name: str = "Orders"
    resend_api_key: str = ""
    order_email_from: str = ""
    order_admin_email: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_from_name: str = "Televera"
    smtp_reply_to: str = ""
    smtp_use_tls: bool = True
    order_submission_timeout_seconds: int = 10
    public_base_url: str = "https://cashmyphone-production.up.railway.app"

    @property
    def origins_list(self) -> List[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
