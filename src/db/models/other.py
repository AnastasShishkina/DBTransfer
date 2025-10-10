import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Index
from sqlmodel import Field, SQLModel
from .base import TimestampMixin, BaseModelConfig


class ETLJobStatus(SQLModel, table=True):
    __tablename__ = "etl_job_status"

    job_name: str = Field(primary_key=True, max_length=50)
    last_success_at: datetime = Field(sa_type=DateTime(timezone=True), nullable=False)


class DeletedObject(TimestampMixin, BaseModelConfig, table=True):
    """
    ТП_ДанныеНаУдаление
    """
    __tablename__ = "deleted_object"

    object_id: uuid.UUID = Field(primary_key=True, alias="Данные")
    name_metadata: str = Field(primary_key=True, alias="НаименованиеМетаданных")

# Модели таблиц для вычисления

class DmGoodsExpenseAlloc(SQLModel, table=True):
    __tablename__ = "dm_goods_expense_alloc"

    registrar_id: uuid.UUID = Field(primary_key=True)
    goods_id: uuid.UUID = Field(primary_key=True)
    cost_category_id: uuid.UUID = Field(primary_key=True)
    department_id: uuid.UUID = Field(primary_key=True)
    date: datetime = Field(primary_key=True, nullable=False)
    type_expense: str = Field()
    amount: Decimal = Field(nullable=False)
    __table_args__ = (
        Index("ix_dm_alloc_registrar_type", "registrar_id", "type_expense"),
        Index("ix_dm_alloc_registrar_date", "registrar_id", "date"),
        Index("ix_dm_alloc_goods", "goods_id", "date"),
        {"postgresql_partition_by": "RANGE (date)"},
    )


class TelegramChats(SQLModel, table=True):
    __tablename__ = "telegram_chats"

    telegram_id: int = Field(primary_key=True)
    phone_number: str | None  = Field()
    username: str | None  = Field()
    language: str | None  = Field()