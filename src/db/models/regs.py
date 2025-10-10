import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Index
from sqlmodel import Field
from .base import TimestampMixin, BaseModelConfig


class GoodsLocation(TimestampMixin, BaseModelConfig, table=True):
    """
    Регистр.Сведения.МестонахождениеТовара
    """
    __tablename__ = "reg_goods_location"
    __scope_delete_cols__ = ["registrar_id"]

    registrar_id: uuid.UUID = Field(primary_key=True, alias="Регистратор")
    date: datetime = Field(primary_key=True, alias="Период")
    goods_id: uuid.UUID = Field(primary_key=True, alias="Товар")
    registrar_type: str = Field(primary_key=True, alias="ТипРегистратора")
    warehouse_id: uuid.UUID | None = Field(alias="Склад")
    car_id: uuid.UUID | None = Field(alias="Машина")
    arrival_route_id: uuid.UUID | None = Field(alias="МаршрутПрихода")
    sender_warehouse_id: uuid.UUID | None = Field(alias="СкладОтправитель")
    goods_status: int | None = Field(alias="СтатусТовара")


class DirectExpenses(TimestampMixin, BaseModelConfig, table=True):
    """
    ПрямыеЗатраты
    """
    __tablename__ = "reg_direct_expenses"
    __scope_delete_cols__ = ["registrar_id"]

    registrar_id: uuid.UUID = Field(primary_key=True, alias="Регистратор")
    goods_doc_id: uuid.UUID = Field(primary_key=True, alias="ДокументСТоварами")
    date: datetime = Field(primary_key=True, alias="Дата", nullable=False)
    registrar_type: str = Field(primary_key=True, alias="ТипРегистратора", max_length=128)
    goods_doc_type: str | None = Field(alias="ТипДокументаСТоварами", max_length=128)
    cost_category_id: uuid.UUID | None = Field(primary_key=True, alias="СтатьяЗатрат")
    route_id: uuid.UUID | None = Field(alias="Маршрут")
    department_id: uuid.UUID | None = Field(alias="Подразделение")
    amount: Decimal | None = Field(alias="СуммаСтавка")

    __table_args__ =(
        Index("ix_de_goods_doc_id", "goods_doc_id"),
        {"postgresql_partition_by": "RANGE (date)"},
    )


class GeneralExpenses(TimestampMixin, BaseModelConfig, table=True):
    """
    ОбщиеЗатраты
    """
    __tablename__ = "reg_general_expenses"
    __scope_delete_cols__ = ["registrar_id"]

    registrar_id: uuid.UUID = Field(primary_key=True, alias="Регистратор")
    date: datetime = Field(primary_key=True, alias="Период")
    cost_category_id: uuid.UUID = Field(primary_key=True, alias="СтатьяЗатрат")
    is_previous_period: bool | None = Field(alias="ЭтоРасходПрошлогоПериода")
    amount: Decimal | None = Field(alias="СуммаUSD")

    __table_args__ = (
        {"postgresql_partition_by": "RANGE (date)"},)


class WarehouseExpenses(TimestampMixin, BaseModelConfig, table=True):
    """
    СкладскиеЗатраты
    """
    __tablename__ = "reg_warehouse_expenses"
    __scope_delete_cols__ = ["registrar_id"]

    registrar_id: uuid.UUID = Field(primary_key=True, alias="Регистратор")
    date: datetime = Field(primary_key=True, alias="Период")
    movement_type: str | None = Field(alias="ВидДвижения")
    organization_id: uuid.UUID | None = Field(alias="Организация")
    cost_category_id: uuid.UUID | None = Field(primary_key=True, alias="СтатьяЗатрат")
    department_id: uuid.UUID | None = Field(alias="Подразделение")
    amount: Decimal | None = Field(alias="СуммаUSD")
    storno: bool | None = Field(alias="Сторно")

    __table_args__ = (
        Index("ix_we_department_id", "department_id"),
        {"postgresql_partition_by": "RANGE (date)"},
    )


class CostAndPaymentGoods(TimestampMixin, BaseModelConfig, table=True):
    """
    ТЗСтоимостьИОплатаТоваров
    """
    __tablename__ = "reg_cost_and_payment_goods"
    __scope_delete_cols__ = ["registrar_id"]

    registrar_id: uuid.UUID = Field(primary_key=True, alias="Регистратор")
    date: datetime = Field(primary_key=True, alias="Дата")
    goods_id: uuid.UUID = Field(primary_key=True, alias="Товар")
    registrar_type: str = Field(primary_key=True, alias="ТипРегистратора")

    amount: float | None = Field(alias="Сумма")
    price_type_id: uuid.UUID | None = Field(alias="ВидЦены")
    storno: bool | None = Field(alias="Сторно")