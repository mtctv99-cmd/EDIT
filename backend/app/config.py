from pydantic import BaseSettings

class Settings(BaseSettings):
    app_name: str = "EDIT"
    redis_url: str = "redis://localhost:6379/0"
    database_url: str = "sqlite:///./edit.db"
    storage_root: str = "./storage"

    class Config:
        env_file = ".env"

settings = Settings()
