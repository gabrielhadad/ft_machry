import os


class Config:
    DATABASE_PATH = os.environ.get("DATABASE_PATH", "data/app.db")
