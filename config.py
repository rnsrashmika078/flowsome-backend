from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    TAVILY_API_KEY: str
    OLLAMA_BASE_URL: str = "http://4.188.251.44:11434"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
