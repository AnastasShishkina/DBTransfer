from datetime import UTC, datetime

from pydantic import validator
from sqlalchemy import Column, DateTime, text
from sqlmodel import Field, SQLModel


def utcnow():
    return datetime.now(UTC)


class BaseModelConfig(SQLModel):

    # превращает "" в None ДО валидации типов
    @validator("*", pre=True)
    def _uuid_empty_to_none(cls, v):
        return None if isinstance(v, str) and v.strip() == "" else v
    #
    class Config:
        allow_population_by_field_name = True


class TimestampMixin(SQLModel):
    __abstract__ = True

    created_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=text("TIMEZONE('UTC', now())"), nullable=False),
    )


def create_all_tables(engine):
    SQLModel.metadata.create_all(engine)


def dev_drop_all_tables(engine):
    SQLModel.metadata.drop_all(engine)
