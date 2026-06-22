from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    session_secret_key: str = "change-this-dev-session-secret"

    class Config:
        env_file = ".env"


settings = Settings()
