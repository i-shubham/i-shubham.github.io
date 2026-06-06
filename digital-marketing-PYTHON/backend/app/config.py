from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:admin@localhost:5432/plugg"
    jwt_secret: str = "plugg-dev-secret-2024"
    jwt_algorithm: str = "HS256"
    access_token_expire_hours: int = 72
    port: int = 8080
    frontend_dir: str = "../"

    class Config:
        env_file = ".env"

settings = Settings()
