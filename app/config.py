from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./data/cashmyphone.db"

    @property
    def async_database_url(self) -> str:
        """Konverterar Railway's postgresql:// → postgresql+asyncpg:// för SQLAlchemy."""
        url = self.database_url
        if url.startswith("postgresql://") or url.startswith("postgres://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1) \
                      .replace("postgres://", "postgresql+asyncpg://", 1)
        return url  # SQLite-URL förblir oförändrad
    scrape_api_key: str = "change-me-in-production"
    scrape_interval_hours: int = 6
    request_timeout_seconds: int = 30
    playwright_headless: bool = True
    allowed_origins: str = "http://localhost:3000,https://cashmyphone.se"
    environment: str = "development"

    @property
    def origins_list(self) -> List[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
