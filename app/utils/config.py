from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Config(BaseSettings):
    # Por padrão inicia com sqlite, mas pode ser alterado para Postgre no .env (DB_CONNECTION=postgresql)
    DB_CONNECTION: str = "sqlite"

    DATABASE_PATH: str = "data/app.db"

    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_DATABASE: str = "ft_machry"
    DB_USERNAME: str = "postgres"
    DB_PASSWORD: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


config = Config()