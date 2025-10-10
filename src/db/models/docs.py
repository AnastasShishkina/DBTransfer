import uuid
from datetime import datetime

from sqlalchemy import Index
from sqlmodel import Field
from .base import TimestampMixin, BaseModelConfig

class Transfers(TimestampMixin, BaseModelConfig, table=True):
    """
    Документ.тп_ПеремещениеТовара
    """
    __tablename__ = "doc_transfers"
    __scope_delete_cols__ = ["id"]

    id: uuid.UUID = Field(primary_key=True, alias="Ссылка")
    date: datetime = Field(primary_key=True, alias="Дата", nullable=False)
    number: str | None = Field(alias="Номер", max_length=50)
    type_transfer: str | None = Field(alias="ВидПеремещения", max_length=50)
    out_warehouse_id: uuid.UUID | None = Field(alias="СкладОтправитель")
    in_warehouse_id: uuid.UUID | None = Field(alias="СкладПолучатель")
    route_id: uuid.UUID | None = Field(alias="Маршрут")
    transport_id: uuid.UUID | None = Field(alias="ТранспортноеСредство")
    document_id: uuid.UUID | None = Field(alias="ДокументОснование")
    cargo_category_id: uuid.UUID | None = Field(alias="КатегорияГруза")
    view_name: str | None = Field(alias="Представление", max_length=100)

    __table_args__ = (
        Index("ix_tr_date", "date"),
        {"postgresql_partition_by": "RANGE (date)"},
    )


class GoodsTransfers(TimestampMixin, BaseModelConfig, table=True):
    """
    Документ.тп_ПеремещениеТовара.Товары
    """
    __tablename__ = "doc_link_goods_transfers"
    __scope_delete_cols__ = ["transfer_id"]

    transfer_id: uuid.UUID = Field(primary_key=True, alias="СсылкаДокумента")
    goods_id: uuid.UUID = Field(primary_key=True, alias="Товар")

    __table_args__ = (
            Index("ix_gt_transfer_id", "transfer_id"),
            Index("ix_gt_goods_id", "goods_id"),
        )


class Receipts(TimestampMixin, BaseModelConfig, table=True):
    """
    Документ.тп_ПриемТовара
    """
    __tablename__ = "doc_receipts"
    __scope_delete_cols__ = ["id"]

    id: uuid.UUID = Field(primary_key=True, alias="Ссылка")
    date: datetime = Field(primary_key=True, alias="Дата")
    number: str | None = Field(alias="Номер", max_length=50)
    warehouse_id: uuid.UUID | None = Field(alias="Склад")
    client_id: uuid.UUID | None = Field(alias="Клиент")
    shop_address: str | None = Field(alias="АдресМагазинаНаименование", max_length=200)
    shop_phone: str | None = Field(alias="ТелефонМагазина", max_length=50)
    shop_name: str | None = Field(alias="НаименованиеМагазина", max_length=100)
    view_name: str | None = Field(alias="Представление", max_length=100)


class GoodsReceipts(TimestampMixin, BaseModelConfig, table=True):
    """
    Документ.тп_ПриемТовара.Товары
    """
    __tablename__ = "doc_link_goods_receipts"
    __scope_delete_cols__ = ["receipt_id"]

    receipt_id: uuid.UUID = Field(primary_key=True, alias="СсылкаДокумента")
    goods_id: uuid.UUID = Field(primary_key=True, alias="Товар")


class DiscountsOnGoods(TimestampMixin, BaseModelConfig, table=True):
    """
    Документ.тп_СкидкиНаТовар
    """
    __tablename__ = "doc_discounts_on_goods"

    id: uuid.UUID = Field(primary_key=True, alias="Ссылка")
    date: datetime | None = Field(alias="Дата")
    number: str | None = Field(alias="Номер", max_length=50)
    view_name: str | None = Field(alias="Представление", max_length=100)


class AdditionalTransferCosts(TimestampMixin, BaseModelConfig, table=True):
    """
    Документ.тп_ДополнительныеРасходыНаПеремещение
    """
    __tablename__ = "doc_additional_transfer_costs"

    id: uuid.UUID = Field(primary_key=True, alias="Ссылка")
    date: datetime | None = Field(alias="Дата")
    number: str | None = Field(alias="Номер", max_length=50)
    view_name: str | None = Field(alias="Представление", max_length=255)


class DebtReturn(TimestampMixin, BaseModelConfig, table=True):
    """
    Документ.тп_ВозвратДолга
    """
    __tablename__ = "doc_debt_return"

    id: uuid.UUID = Field(primary_key=True, alias="Ссылка")
    date: datetime | None = Field(alias="Дата")
    number: str | None = Field(alias="Номер", max_length=50)
    view_name: str | None = Field(alias="Представление", max_length=255)


class FreightRateChange(TimestampMixin, BaseModelConfig, table=True):
    """
    Документ.тп_ИзменениеСтавкиЗаПеревозку
    """
    __tablename__ = "doc_freight_rate_change"

    id: uuid.UUID = Field(primary_key=True, alias="Ссылка")
    date: datetime | None = Field(alias="Дата")
    number: str | None = Field(alias="Номер", max_length=50)
    view_name: str | None = Field(alias="Представление", max_length=255)


class RegistersAdjustment(TimestampMixin, BaseModelConfig, table=True):
    """
    Документ.тп_КорректировкаРегистров
    """
    __tablename__ = "doc_registers_adjustment"

    id: uuid.UUID = Field(primary_key=True, alias="Ссылка")
    date: datetime | None = Field(alias="Дата")
    number: str | None = Field(alias="Номер", max_length=50)
    view_name: str | None = Field(alias="Представление", max_length=255)


class GoodsAcceptanceCorrection(TimestampMixin, BaseModelConfig, table=True):
    """
    Документ.тп_ИсправлениеПриемаТовара
    """
    __tablename__ = "doc_goods_acceptance_correction"

    id: uuid.UUID = Field(primary_key=True, alias="Ссылка")
    date: datetime | None = Field(alias="Дата")
    number: str | None = Field(alias="Номер", max_length=50)
    view_name: str | None = Field(alias="Представление", max_length=255)


class MutualSettlementCorrection(TimestampMixin, BaseModelConfig, table=True):
    """
    Документ.тп_ИсправлениеВзаиморасчетов
    """
    __tablename__ = "doc_mutual_settlement_correction"

    id: uuid.UUID = Field(primary_key=True, alias="Ссылка")
    date: datetime | None = Field(alias="Дата")
    number: str | None = Field(alias="Номер", max_length=50)
    view_name: str | None = Field(alias="Представление", max_length=255)


class BarcodeRecalculation(TimestampMixin, BaseModelConfig, table=True):
    """
    Документ.тп_ПересчетШКПоПеремещениям
    """
    __tablename__ = "doc_barcode_recalculation"

    id: uuid.UUID = Field(primary_key=True, alias="Ссылка")
    date: datetime | None = Field(alias="Дата")
    number: str | None = Field(alias="Номер", max_length=50)
    view_name: str | None = Field(alias="Представление", max_length=255)


class DeliveryTransfer(TimestampMixin, BaseModelConfig, table=True):
    """
    Документ.тп_ПеремещениеПодДоставку
    """
    __tablename__ = "doc_delivery_transfer"

    id: uuid.UUID = Field(primary_key=True, alias="Ссылка")
    date: datetime | None = Field(alias="Дата")
    number: str | None = Field(alias="Номер", max_length=50)
    view_name: str | None = Field(alias="Представление", max_length=255)


class AdditionalCosts(TimestampMixin, BaseModelConfig, table=True):
    """
    Документ.тп_ДополнительныеРасходы
    """
    __tablename__ = "doc_additional_costs"

    id: uuid.UUID = Field(primary_key=True, alias="Ссылка")
    date: datetime | None = Field(alias="Дата")
    number: str | None = Field(alias="Номер", max_length=50)
    view_name: str | None = Field(alias="Представление", max_length=255)


class PaymentReceipt(TimestampMixin, BaseModelConfig, table=True):
    """
    Документ.тп_ПриемОплаты
    """
    __tablename__ = "doc_payment_receipt"

    id: uuid.UUID = Field(primary_key=True, alias="Ссылка")
    date: datetime | None = Field(alias="Дата")
    number: str | None = Field(alias="Номер", max_length=50)
    view_name: str | None = Field(alias="Представление", max_length=255)


class GoodsReturn(TimestampMixin, BaseModelConfig, table=True):
    """
    Документ.тп_ВозвратТовара
    """
    __tablename__ = "doc_goods_return"

    id: uuid.UUID = Field(primary_key=True, alias="Ссылка")
    date: datetime | None = Field(alias="Дата")
    number: str | None = Field(alias="Номер", max_length=50)
    view_name: str | None = Field(alias="Представление", max_length=255)


class PaymentReturnLink(TimestampMixin, BaseModelConfig, table=True):
    """
    ДокументСсылка.тп_ВозвратОплаты
    """
    __tablename__ = "doc_payment_return_link"

    id: uuid.UUID = Field(primary_key=True, alias="Ссылка")
    date: datetime | None = Field(alias="Дата")
    number: str | None = Field(alias="Номер", max_length=50)
    view_name: str | None = Field(alias="Представление", max_length=255)


class ExpressAcceptanceRecalculationLink(TimestampMixin, BaseModelConfig, table=True):
    """
    ДокументСсылка.тп_ПересчетЭкспрессПриемок
    """
    __tablename__ = "doc_express_acceptance_recalculation_link"

    id: uuid.UUID = Field(primary_key=True, alias="Ссылка")
    date: datetime | None = Field(alias="Дата")
    number: str | None = Field(alias="Номер", max_length=50)
    view_name: str | None = Field(alias="Представление", max_length=255)
