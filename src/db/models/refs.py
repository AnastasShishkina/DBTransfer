import uuid
from datetime import UTC, datetime
from decimal import Decimal

from pydantic import validator
from sqlalchemy import Column, DateTime, text, Index
from sqlmodel import Field, SQLModel

from .base import TimestampMixin, BaseModelConfig


class Departments(TimestampMixin, BaseModelConfig, table=True):
    """
    Справочник.ПодразделенияОрганизаций
    """
    __tablename__ = "ref_departments"

    id: uuid.UUID = Field(primary_key=True, alias="Ссылка")
    code: str | None = Field(alias="Код", max_length=50)
    name: str | None = Field(alias="Наименование", max_length=50)


class CostCategories(TimestampMixin, BaseModelConfig, table=True):
    """
    Справочник.тп_СтатьиЗатрат
    """
    __tablename__ = "ref_cost_categories"

    id: uuid.UUID = Field(primary_key=True, alias="Ссылка")
    code: str | None = Field(alias="Код", max_length=50)
    name: str | None = Field(alias="Наименование", max_length=50)


class TypesTransport(TimestampMixin, BaseModelConfig, table=True):
    """
    Справочник.тп_ВидыТранспорта
    """
    __tablename__ = "ref_types_transport"

    id: uuid.UUID = Field(primary_key=True, alias="Ссылка")
    code: str | None = Field(alias="Код", max_length=50)
    name: str | None = Field(alias="Наименование", max_length=50)


class Transports(TimestampMixin,BaseModelConfig, table=True):
    """
    Справочник.тп_Машины
    """
    __tablename__ = "ref_transports"

    id: uuid.UUID = Field(primary_key=True, alias="Ссылка")
    name: str | None = Field(alias="Наименование", max_length=50)
    type_transport_id: uuid.UUID | None = Field(alias="ВидТранспорта")


class Countries(TimestampMixin,BaseModelConfig, table=True):
    """
    Справочник.СтраныМира
    """
    __tablename__ = "ref_countries"

    id: uuid.UUID = Field(primary_key=True, alias="Ссылка")
    code: str | None = Field(alias="Код", max_length=50)
    name: str | None = Field(alias="Наименование", max_length=50)


class Cities(TimestampMixin,BaseModelConfig, table=True):
    """
    Справочник.тп_Города
    """
    __tablename__ = "ref_cities"

    id: uuid.UUID = Field(primary_key=True, alias="Ссылка")
    code: str | None = Field(alias="Код", max_length=50)
    name: str | None = Field(alias="Наименование", max_length=50)
    country_id: uuid.UUID | None = Field(alias="Страна")


class Counterparties(TimestampMixin,BaseModelConfig, table=True):
    """
    Справочник.Контрагенты
    """
    __tablename__ = "ref_counterparties"

    id: uuid.UUID = Field(primary_key=True, alias="Ссылка")
    name: str | None = Field(alias="Наименование", max_length=50)


class Routes(TimestampMixin,BaseModelConfig, table=True):
    """
    Справочник.тп_Маршруты
    """
    __tablename__ = "ref_routes"

    id: uuid.UUID = Field(primary_key=True, alias="Ссылка")
    name: str | None = Field(alias="Наименование", max_length=50)
    out_city_id: uuid.UUID | None = Field(alias="ГородОтправитель")
    in_city_id: uuid.UUID | None = Field(alias="ГородПолучатель")


class Warehouses(TimestampMixin, BaseModelConfig, table=True):
    """
    Справочник.тп_Склады
    """
    __tablename__ = "ref_warehouses"

    id: uuid.UUID = Field(primary_key=True, alias="Ссылка")
    code: str | None = Field(alias="Код", max_length=50)
    name: str | None = Field(alias="Наименование", max_length=50)
    city_id: uuid.UUID | None = Field(alias="Город")
    country_id: uuid.UUID | None = Field(alias="Страна")
    department_id: uuid.UUID | None = Field(alias="Подразделение")
    telegram_address: str | None = Field(alias="АдресСкладаТелеграм")
    customs: bool | None = Field(alias="Таможня")

    __table_args__ = (
        Index("ix_wh_department_id", "department_id"),
        Index("ix_wh_country_id", "country_id"),
    )


class CargoCategory(TimestampMixin, BaseModelConfig, table=True):
    """
    Справочник.тп_КатегорияГруза
    """
    __tablename__ = "ref_cargo_categories"

    id: uuid.UUID = Field(primary_key=True, alias="Ссылка")
    code: str | None = Field(alias="Код", max_length=50)
    name: str | None = Field(alias="Наименование", max_length=100)


class GoodsTypes(TimestampMixin, BaseModelConfig, table=True):
    """
    Справочник.тп_ВидыТоваров
    Это иерархический справочник
    parent_id это ссылка на id родительской записи
    """
    __tablename__ = "ref_goods_types"

    id: uuid.UUID = Field(primary_key=True, alias="Ссылка")
    code: str | None = Field(alias="Код", max_length=50)
    name: str | None = Field(alias="Наименование", max_length=50)
    is_group: bool| None = Field(alias="ЭтоГруппа")
    cargo_category_id: uuid.UUID | None = Field(alias="КатегорияГруза")
    parent_id: uuid.UUID | None = Field(alias="Родитель")


class PackageTypes(TimestampMixin, BaseModelConfig, table=True):
    """
    Справочник.тп_ТипыУпаковок
    """
    __tablename__ = "ref_package_types"

    id: uuid.UUID = Field(primary_key=True, alias="Ссылка")
    code: str | None = Field(alias="Код", max_length=50)
    name: str | None = Field(alias="Наименование", max_length=50)


class Clients(TimestampMixin, BaseModelConfig, table=True):
    """
    Справочник.тп_Клиенты
    """
    __tablename__ = "ref_clients"

    id: uuid.UUID = Field(primary_key=True, alias="Ссылка")
    code: str | None = Field(alias="КодКлиента", max_length=50)
    name: str | None = Field(alias="Наименование", max_length=50)

    # Данные клиента
    client_lastname: str | None = Field(alias="КлиентФамилия", max_length=50)
    client_firstname: str | None = Field(alias="КлиентИмя", max_length=50)
    client_passport_number: str | None = Field(alias="КлиентНомерПаспорта", max_length=20)
    client_passport_series: str | None = Field(alias="КлиентСерияПаспорта", max_length=20)
    client_phone_telegram: str | None = Field(alias="КлиентНомерТелефонаТелеграм", max_length=50)
    client_phone: str | None = Field(alias="КлиентНомерТелефона", max_length=50)

    # Представитель
    repr_lastname: str | None = Field(alias="ПредставительФамилия", max_length=50)
    repr_firstname: str | None = Field(alias="ПредставительИмя", max_length=50)
    repr_passport_series: str | None = Field(alias="ПредставительСерияПаспорта", max_length=20)
    repr_passport_number: str | None = Field(alias="ПредставительНомерПаспорта", max_length=20)
    repr_phone: str | None = Field(alias="ПредставительТелефона", max_length=50)

    # Региональный представитель
    rg_lastname: str | None = Field(alias="РГФамилия", max_length=50)
    rg_passport_series: str | None = Field(alias="РГСерияПаспорта", max_length=20)
    rg_passport_number: str | None = Field(alias="РГНомерПаспорта", max_length=20)
    rg_phone: str | None = Field(alias="РГНомерТелефона", max_length=50)
    rg_name: str | None = Field(alias="РегиональныйПредставитель", max_length=100)


class PriceTypes(TimestampMixin, BaseModelConfig, table=True):
    """
    Справочник.тп_ВидыЦенИСкидок
    """
    __tablename__ = "ref_price_types"

    id: uuid.UUID = Field(primary_key=True, alias="Ссылка")
    code: str | None = Field(alias="Код", max_length=50)
    name: str | None = Field(alias="Наименование", max_length=100)
    movement_type: str | None = Field(alias="ТипДвижения", max_length=50)


class Goods(TimestampMixin, BaseModelConfig, table=True):
    """
    Товары
    """
    __tablename__ = "ref_goods"

    id: uuid.UUID = Field(primary_key=True, alias="Товар")
    barcode: str | None = Field(alias="ШК")
    receipt_id: uuid.UUID | None = Field(alias="ПриемТовара")
    client_id: uuid.UUID | None = Field(alias="Клиент")
    package_type_id: uuid.UUID | None = Field(alias="ТипУпаковки")
    goods_type_id: uuid.UUID | None = Field(alias="ВидТовара")
    volume: float | None = Field(alias="Объем")
    weight: float | None = Field(alias="Вес")
    length: float | None = Field(alias="Длина")
    width: float | None = Field(alias="Ширина")
    height: float | None = Field(alias="Высота")
    price: float | None = Field(alias="Цена")
    price_per_m3: float | None = Field(alias="ЦенаЗаКуб")
    price_per_ton: float | None = Field(alias="ЦенаЗаТонну")
    amount: Decimal | None = Field(alias="Сумма")
    is_mail: bool | None = Field(alias="ЭтоПочта")
    is_return: bool | None = Field(alias="ВозвратТовара")
    by_weight: bool | None = Field(alias="ПоВесу")
    place_number: int | None = Field(alias="НомерМеста")
    total_places: int | None = Field(alias="ВсегоМест")
    order_number: str | None = Field(alias="НомерОрдера")
    days_in_transit: int | None = Field(alias="ДнейВПути")
    arrival_date: datetime | None = Field(alias="ДатаПрибытияИлиТекущая")
    total_amount: Decimal | None = Field(alias="СуммаВсего")
