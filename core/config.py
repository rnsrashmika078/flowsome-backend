from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    groq_api_key: str
    chat_model_text: str
    chat_model_file: str
    DATABASE_URL:str    

    class Config:
        env_file = ".env"


settings = Settings()
