import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import Column, DateTime, Numeric, text
from sqlmodel import Field, SQLModel


def utcnow():
    return datetime.now(UTC)


class BaseModelConfig(SQLModel):
    class Config:
        allow_population_by_field_name = True


class TimestampMixin(SQLModel):
    __abstract__ = True

    created_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=text("TIMEZONE('UTC', now())"), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=text("TIMEZONE('UTC', now())"), nullable=False),
    )


class StgExpenseItem(TimestampMixin, BaseModelConfig, table=True):
    __tablename__ = "stg_expense_items"

    external_id: uuid.UUID = Field(primary_key=True, alias="Ссылка")
    version: str = Field(alias="ВерсияДанных")
    is_deleted: bool = Field(alias="ПометкаУдаления")
    parent_extid: uuid.UUID = Field(alias="Родитель")
    is_group: bool = Field(alias="ЭтоГруппа")
    code: str = Field(alias="Код", max_length=64)
    name: str = Field(alias="Наименование", max_length=255)


class StgCitiesConfig(TimestampMixin, BaseModelConfig, table=True):
    __tablename__ = "stg_cities_v1"

    external_id: uuid.UUID = Field(primary_key=True, alias="Ссылка")
    version: str = Field(alias="ВерсияДанных")
    is_deleted: bool = Field(alias="ПометкаУдаления")
    parent_extid: uuid.UUID = Field(alias="Родитель")
    is_group: bool = Field(alias="ЭтоГруппа")
    code: str = Field(alias="Код")
    name: str = Field(alias="Наименование")


class StgCitiesV2(TimestampMixin, BaseModelConfig, table=True):
    __tablename__ = "stg_cities_v2"

    external_id: uuid.UUID = Field(primary_key=True, alias="Ссылка")
    version: str = Field(default=None, alias="ВерсияДанных")
    is_deleted: bool = Field(alias="ПометкаУдаления")
    code: str = Field(alias="Код")
    name: str = Field(alias="Наименование")


class StgExpenseRecord(TimestampMixin, BaseModelConfig, table=True):
    __tablename__ = "stg_expense_records"

    registrar_id: uuid.UUID = Field(primary_key=True, alias="Регистратор")
    goods_doc_id: uuid.UUID = Field(primary_key=True, alias="ДокументСТоварами")
    date: datetime = Field(primary_key=True, alias="Дата", sa_type=DateTime(timezone=True), nullable=False)
    registrar_type: str = Field(alias="ТипРегистратора", max_length=128)
    goods_doc_type: str = Field(alias="ТипДокументаСТоварами", max_length=128)
    expense_item_id: uuid.UUID = Field(alias="СтатьяЗатрат")
    route_id: uuid.UUID = Field(alias="Маршрут")
    department_id: uuid.UUID = Field(alias="Подразделение")
    supplier_id: uuid.UUID = Field(alias="Поставщик")
    amount_rate: Decimal = Field(alias="СуммаСтавка", sa_column=Column(Numeric(18, 2)))
    # TODO: В таблица должны быть партиции, если мы хотим быстро по ним данные доставать. Но их нужно объявлять автоматически
    # __table_args__ = (
    #     {"postgresql_partition_by": "RANGE (date)"},
    # )


def create_all_tables(engine):
    SQLModel.metadata.create_all(engine)


def dev_drop_all_tables(engine):
    SQLModel.metadata.drop_all(engine)
