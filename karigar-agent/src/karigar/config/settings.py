
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    perplexity_api_key: str = "your_perplexity_api_key"
    database_url: str = "sqlite+aiosqlite:///./karigar.db"

    class Config:
        env_file = ".env"

settings = Settings()
