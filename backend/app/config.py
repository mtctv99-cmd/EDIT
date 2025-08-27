"""Application configuration via environment variables.

This module uses ``pydantic-settings``'s :class:`BaseSettings` to load
configuration values. Pydantic v2 removed ``BaseSettings`` from the core
package, so we import it from ``pydantic_settings`` for compatibility.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration loaded from environment or ``.env`` file."""

    model_config = SettingsConfigDict(env_file=".env")

    app_name: str = "EDIT"
    redis_url: str = "redis://localhost:6379/0"
    database_url: str = "sqlite:///./edit.db"
    storage_root: str = "./storage"


settings = Settings()

