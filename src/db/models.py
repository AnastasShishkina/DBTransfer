import uuid
from datetime import UTC, datetime
from decimal import Decimal

from pydantic import validator
from sqlalchemy import Column, DateTime, UniqueConstraint, text, Index
from sqlmodel import Field, SQLModel


def utcnow():
    return datetime.now(UTC)


# Базовые модели
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


class ETLJobStatus(SQLModel, table=True):
    __tablename__ = "etl_job_status"

    job_name: str = Field(primary_key=True, max_length=50)
    last_success_at: datetime = Field(sa_type=DateTime(timezone=True), nullable=False)


# Модели для трансфера из 1С
class Departments(TimestampMixin, BaseModelConfig, table=True):
    """
    Справочник.ПодразделенияОрганизаций
    """
    __tablename__ = "departments"

    id: uuid.UUID = Field(primary_key=True, alias="Ссылка")
    code: str | None = Field(alias="Код", max_length=50)
    name: str | None = Field(alias="Наименование", max_length=50)


class CostCategories(TimestampMixin, BaseModelConfig, table=True):
    """
    Справочник.тп_СтатьиЗатрат
    """
    __tablename__ = "cost_categories"

    id: uuid.UUID = Field(primary_key=True, alias="Ссылка")
    code: str | None = Field(alias="Код", max_length=50)
    name: str | None = Field(alias="Наименование", max_length=50)


class TypesTransport(TimestampMixin, BaseModelConfig, table=True):
    """
    Справочник.тп_ВидыТранспорта
    """
    __tablename__ = "types_transport"

    id: uuid.UUID = Field(primary_key=True, alias="Ссылка")
    code: str | None = Field(alias="Код", max_length=50)
    name: str | None = Field(alias="Наименование", max_length=50)


class Transports(TimestampMixin,BaseModelConfig, table=True):
    """
    Справочник.тп_Машины
    """
    __tablename__ = "transports"

    id: uuid.UUID = Field(primary_key=True, alias="Ссылка")
    name: str | None = Field(alias="Наименование", max_length=50)
    type_transport_id: uuid.UUID | None = Field(alias="ВидТранспорта")


class Countries(TimestampMixin,BaseModelConfig, table=True):
    """
    Справочник.СтраныМира
    """
    __tablename__ = "countries"

    id: uuid.UUID = Field(primary_key=True, alias="Ссылка")
    code: str | None = Field(alias="Код", max_length=50)
    name: str | None = Field(alias="Наименование", max_length=50)


class Cities(TimestampMixin,BaseModelConfig, table=True):
    """
    Справочник.тп_Города
    """
    __tablename__ = "cities"

    id: uuid.UUID = Field(primary_key=True, alias="Ссылка")
    code: str | None = Field(alias="Код", max_length=50)
    name: str | None = Field(alias="Наименование", max_length=50)
    country_id: uuid.UUID | None = Field(alias="Страна")


class Counterparties(TimestampMixin,BaseModelConfig, table=True):
    """
    Справочник.Контрагенты
    """
    id: uuid.UUID = Field(primary_key=True, alias="Ссылка")
    name: str | None = Field(alias="Наименование", max_length=50)


class Routes(TimestampMixin,BaseModelConfig, table=True):
    """
    Справочник.тп_Маршруты
    """
    __tablename__ = "routes"

    id: uuid.UUID = Field(primary_key=True, alias="Ссылка")
    name: str | None = Field(alias="Наименование", max_length=50)
    out_city_id: uuid.UUID | None = Field(alias="ГородОтправитель")
    in_city_id: uuid.UUID | None = Field(alias="ГородПолучатель")


class Warehouses(TimestampMixin, BaseModelConfig, table=True):
    """
    Справочник.тп_Склады
    """
    __tablename__ = "warehouses"

    id: uuid.UUID = Field(primary_key=True, alias="Ссылка")
    code: str | None = Field(alias="Код", max_length=50)
    name: str | None = Field(alias="Наименование", max_length=50)
    city_id: uuid.UUID | None = Field(alias="Город")
    country_id: uuid.UUID | None = Field(alias="Страна")
    department_id: uuid.UUID | None = Field(alias="Подразделение")
    __table_args__ = (
        Index("ix_wh_department_id", "department_id"),
        Index("ix_wh_country_id", "country_id"),
    )


class Transfers(TimestampMixin, BaseModelConfig, table=True):
    """
    Документ.тп_ПеремещениеТовара
    """
    __tablename__ = "transfers"

    id: uuid.UUID = Field(primary_key=True, alias="Ссылка")
    date: datetime = Field(primary_key=True, alias="Дата", nullable=False)
    number: str | None = Field(alias="Номер", max_length=50)
    out_warehouse_id: uuid.UUID | None = Field(alias="СкладОтправитель")
    in_warehouse_id: uuid.UUID | None = Field(alias="СкладПолучатель")
    route_id: uuid.UUID | None = Field(alias="Маршрут")
    transport_id: uuid.UUID | None = Field(alias="ТранспортноеСредство")
    document_id: uuid.UUID | None = Field(alias="ДокументОснование")
    __table_args__ = (
        Index("ix_tr_date", "date"),
        {"postgresql_partition_by": "RANGE (date)"},
    )


class GoodsTransfers(TimestampMixin, BaseModelConfig, table=True):
    """
    Документ.тп_ПеремещениеТовара.Товары
    """
    __tablename__ = "goods_transfers"
    __scope_delete_cols__ = ["transfer_id"]

    transfer_id: uuid.UUID = Field(primary_key=True, alias="СсылкаДокумента")
    goods_id: uuid.UUID = Field(primary_key=True, alias="Товар")

    __table_args__ = (
            Index("ix_gt_transfer_id", "transfer_id"),
            Index("ix_gt_goods_id", "goods_id"),
        )


class GoodsTypes(TimestampMixin, BaseModelConfig, table=True):
    """
    Справочник.тп_ВидыТоваров
    """
    __tablename__ = "goods_types"

    id: uuid.UUID = Field(primary_key=True, alias="Ссылка")
    code: str | None = Field(alias="Код", max_length=50)
    name: str | None = Field(alias="Наименование", max_length=50)


class Goods(TimestampMixin, BaseModelConfig, table=True):
    """
    Товары
    """
    __tablename__ = "goods"

    id: uuid.UUID = Field(primary_key=True, alias="Товар")
    barcode: str | None = Field(alias="ШК")
    goods_receipt: uuid.UUID | None = Field(alias="ПриемТовара")
    client_id: str | None = Field(alias="Клиент")
    package_type: uuid.UUID | None = Field(alias="ТипУпаковки")
    goods_type_id: uuid.UUID | None = Field(alias="ВидТовара")
    volume: float | None = Field(alias="Объем")
    weight: float | None = Field(alias="Вес")
    price_per_m3: float | None = Field(alias="ЦенаЗаКуб")
    price_per_ton: float | None = Field(alias="ЦенаЗаТонну")
    amount: Decimal | None = Field(alias="Сумма")
    is_mail: bool | None = Field(alias="ЭтоПочта")
    is_return: bool | None = Field(alias="ВозвратТовара")
    by_weight: bool | None = Field(alias="ПоВесу")
    place_number: int | None = Field(alias="НомерМеста")
    total_places: int | None = Field(alias="ВсегоМест")
    @validator('goods_receipt', pre=True)
    def _uuid_empty_to_none(cls, v):
        return None if isinstance(v, str) and v.strip() == "" else v

class PackageTypes(TimestampMixin, BaseModelConfig, table=True):
    """
    Справочник.тп_ТипыУпаковок
    """
    __tablename__ = "package_types"

    id: uuid.UUID = Field(primary_key=True, alias="Ссылка")
    code: str | None = Field(alias="Код", max_length=50)
    name: str | None = Field(alias="Наименование", max_length=50)


class Clients(TimestampMixin, BaseModelConfig, table=True):
    """
    Справочник.тп_Клиенты
    """
    __tablename__ = "clients"

    id: uuid.UUID = Field(primary_key=True, alias="Ссылка")
    code: str | None = Field(alias="КодКлиента", max_length=50)
    name: str | None = Field(alias="Наименование", max_length=50)


class GoodsLocation(TimestampMixin, BaseModelConfig, table=True):
    """
    Регистр.Сведения.МестонахождениеТовара
    """
    __tablename__ = "goods_location"
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
    __tablename__ = "direct_expenses"
    __scope_delete_cols__ = ["registrar_id"]

    registrar_id: uuid.UUID = Field(primary_key=True, alias="Регистратор")
    goods_doc_id: uuid.UUID = Field(primary_key=True, alias="ДокументСТоварами")
    date: datetime = Field(primary_key=True, alias="Дата", nullable=False)
    registrar_type: str = Field(primary_key=True, alias="ТипРегистратора", max_length=128)
    goods_doc_type: str | None = Field(alias="ТипДокументаСТоварами", max_length=128)
    cost_category_id: uuid.UUID | None = Field(alias="СтатьяЗатрат")
    route_id: uuid.UUID | None = Field(alias="Маршрут")
    department_id: uuid.UUID | None = Field(alias="Подразделение")
    supplier_id: uuid.UUID | None = Field(alias="Поставщик")
    amount: Decimal | None = Field(alias="СуммаСтавка")

    __table_args__ =(
        Index("ix_de_goods_doc_id", "goods_doc_id"),
        {"postgresql_partition_by": "RANGE (date)"},
    )

class GeneralExpenses(TimestampMixin, BaseModelConfig, table=True):
    """
    ОбщиеЗатраты
    """
    __tablename__ = "general_expenses"
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
    __tablename__ = "warehouse_expenses"
    __scope_delete_cols__ = ["registrar_id"]

    registrar_id: uuid.UUID = Field(primary_key=True, alias="Регистратор")
    date: datetime = Field(primary_key=True, alias="Период")
    movement_type: str | None = Field(alias="ВидДвижения")
    organization_id: uuid.UUID | None = Field(alias="Организация")
    cost_category_id: uuid.UUID | None = Field(alias="СтатьяЗатрат")
    department_id: uuid.UUID | None = Field(alias="Подразделение")
    amount: Decimal | None = Field(alias="СуммаUSD")
    storno: bool | None = Field(alias="Сторно")
    __table_args__ = (
        Index("ix_we_department_id", "department_id"),
        {"postgresql_partition_by": "RANGE (date)"},
    )

class Receipts(TimestampMixin, BaseModelConfig, table=True):
    """
    Документ.тп_ПриемТовара
    """
    __tablename__ = "receipts"

    id: uuid.UUID = Field(primary_key=True, alias="Ссылка")
    date: datetime = Field(primary_key=True, alias="Дата")
    number: str | None = Field(alias="Номер", max_length=50)
    warehouse_id: uuid.UUID | None = Field(alias="Склад")
    client_id: uuid.UUID | None = Field(alias="Клиент")


class GoodsReceipts(TimestampMixin, BaseModelConfig, table=True):
    """
    Документ.тп_ПеремещениеТовара.Товары
    """
    __tablename__ = "goods_receipts"
    __scope_delete_cols__ = ["receipt_id"]

    receipt_id: uuid.UUID = Field(primary_key=True, alias="СсылкаДокумента")
    goods_id: uuid.UUID = Field(primary_key=True, alias="Товар")

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

def create_all_tables(engine):
    SQLModel.metadata.create_all(engine)


def dev_drop_all_tables(engine):
    SQLModel.metadata.drop_all(engine)
