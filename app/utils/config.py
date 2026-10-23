from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Config(BaseSettings):
    DATABASE_PATH: str = "data/app.db"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


config = Config()