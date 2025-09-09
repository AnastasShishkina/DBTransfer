from pathlib import Path

from pika import ConnectionParameters
from pydantic import BaseSettings

ROOT = Path(__file__).resolve().parents[1]



class Settings(BaseSettings):
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    RMQ_HOST: str
    RMQ_PORT: str
    RMQ_USER: str
    RMQ_PASSWORD: str
    RMQ_QUEUE: str
    RMQ_QUARANTINE_QUEUE: str
    LOG_LEVEL: str

    @property
    def DATABASE_URL(self):
        return f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def RABBITMG_CONN_PARAMS(self):
        return ConnectionParameters( host=self.RMQ_HOST, port=self.RMQ_PORT,)
    #
    # @property
    # def LOG_LEVEL(self):
    #     return self.LOG_LEVEL

    class Config:
        env_file = str(ROOT / ".env")
        env_file_encoding = "utf-8"

settings = Settings()