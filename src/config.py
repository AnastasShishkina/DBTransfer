from pathlib import Path

from pydantic import BaseSettings

ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    LOGGER_LEVEL: str

    @property
    def DATABASE_URL(self):
        return f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


    @property
    def LOG_LEVEL(self):
        return self.LOGGER_LEVEL

    class Config:
        env_file = str(ROOT / ".env")
        env_file_encoding = "utf-8"


settings = Settings()
