from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",        # charge automatiquement .env en local
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = "local"
    service_name: str = "interpretation_service"

    # Groq / LangChain
    groq_api_key: str
    groq_model: str = "llama-3.1-8b-instant"
    groq_stt_model: str = "whisper-large-v3"

    # Plus tard : d'autres APIs, URLs, etc.
    # openai_api_key: str | None = None
    # rabbitmq_url: str | None = None

settings = Settings()

