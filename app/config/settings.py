from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    openrouter_api_key: str = ""
    max_search_results: int = 5
    log_level: str = "INFO"

    class Config:
        env_file = ".env"


# Singleton instance
settings = Settings()
