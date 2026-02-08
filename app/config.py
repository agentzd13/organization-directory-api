from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    STATIC_API_KEY: str = "test-secret"
    DATABASE_URL: str = "sqlite+aiosqlite:///./test.db"
    
    class Config:
        env_file = ".env"

settings = Settings()
