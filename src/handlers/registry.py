from typing import NamedTuple

from sqlmodel import SQLModel

import  src.db.models as models

REGISTRY = {
    "Справочник.ПодразделенияОрганизаций": models.Departments,
    "Справочник.тп_СтатьиЗатрат": models.CostCategories,
    "Справочник.тп_ВидыТранспорта": models.TypesTransport,
    "Справочник.тп_Машины": models.Transports,
    "Справочник.тп_Города": models.Cities,
    "Справочник.СтраныМира": models.Countries,
    "Справочник.тп_Маршруты": models.Routes,
    "Справочник.тп_Склады": models.Warehouses,
    "Справочник.тп_ВидыТоваров": models.GoodsTypes,
    "Справочник.тп_Клиенты": models.Clients,
    "Справочник.тп_ТипыУпаковок": models.PackageTypes,
    "Справочник.Контрагенты": models.Counterparties,
    "Документ.тп_ПеремещениеТовара": models.Transfers,
    "Документ.тп_ПеремещениеТовара.Товары": models.GoodsTransfers,
    "Документ.тп_ПриемТовара": models.Receipts,
    "Документ.тп_ПриемТовара.Товары": models.GoodsReceipts,
    "ПрямыеЗатраты": models.DirectExpenses,
    "Товары": models.Goods,
    "МестонахождениеТовара": models.GoodsLocation,
    "ОбщиеЗатраты": models.GeneralExpenses,
    "СкладскиеЗатраты": models.WarehouseExpenses,
    "ТП_ДанныеНаУдаление": models.DeletedObject
}

class CascadeRule(NamedTuple):
    model: type[SQLModel]
    column_name: str  # как называется столбец в дочерней таблице


CASCADE_DELETED_MAP: dict[str, list[CascadeRule]] = {
    "Документ.тп_ПеремещениеТовара": [
        CascadeRule(model=models.GoodsTransfers, column_name="transfer_id"),
        CascadeRule(model=models.GoodsLocation, column_name="registrar_id"),
        CascadeRule(model=models.DirectExpenses, column_name="goods_doc_id"),
    ],
    "Документ.тп_ПриемТовара": [
        CascadeRule(model=models.GoodsReceipts, column_name="receipt_id"),
        CascadeRule(model=models.Goods, column_name="goods_receipt"),
        CascadeRule(model=models.GoodsLocation, column_name="registrar_id"),
    ],
}