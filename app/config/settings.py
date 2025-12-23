from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API metadata
    project_name: str = "Fact-Check API"
    api_version: str = "1"

    # OpenRouter
    openrouter_api_key: str = ""
    openrouter_api_url: str = "https://openrouter.ai/api/v1"
    max_search_results: int = 5

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"


# Singleton instance
settings = Settings()
