from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openrouter_api_key: str = ""
    sarvam_api_key: str = ""
    database_url: str = "sqlite:///./tutor.db"
    gemini_model: str = "google/gemini-3-flash-preview"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    sarvam_base_url: str = "https://api.sarvam.ai"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
