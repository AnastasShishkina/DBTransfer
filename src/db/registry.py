from typing import NamedTuple

from sqlmodel import SQLModel

import src.db.models as models

REGISTRY = {
    # Справочники
    "Справочник.ПодразделенияОрганизаций": models.Departments,
    "Справочник.тп_СтатьиЗатрат": models.CostCategories,
    "Справочник.тп_ВидыТранспорта": models.TypesTransport,
    "Справочник.тп_Машины": models.Transports,
    "Справочник.СтраныМира": models.Countries,
    "Справочник.тп_Города": models.Cities,
    "Справочник.Контрагенты": models.Counterparties,
    "Справочник.тп_Маршруты": models.Routes,
    "Справочник.тп_Склады": models.Warehouses,
    "Справочник.тп_КатегорияГруза": models.CargoCategory,
    "Справочник.тп_ВидыТоваров": models.GoodsTypes,
    "Справочник.тп_ТипыУпаковок": models.PackageTypes,
    "Справочник.тп_Клиенты": models.Clients,
    "Справочник.тп_ВидыЦенИСкидок": models.PriceTypes,
    "Товары": models.Goods,

    # Документы
    "Документ.тп_ПеремещениеТовара": models.Transfers,
    "Документ.тп_ПеремещениеТовара.Товары": models.GoodsTransfers,
    "Документ.тп_ПриемТовара": models.Receipts,
    "Документ.тп_ПриемТовара.Товары": models.GoodsReceipts,
    "Документ.тп_СкидкиНаТовар": models.DiscountsOnGoods,
    "Документ.тп_ДополнительныеРасходыНаПеремещение": models.AdditionalTransferCosts,
    "Документ.тп_ВозвратДолга": models.DebtReturn,
    "Документ.тп_ИзменениеСтавкиЗаПеревозку": models.FreightRateChange,
    "Документ.тп_КорректировкаРегистров": models.RegistersAdjustment,
    "Документ.тп_ИсправлениеПриемаТовара": models.GoodsAcceptanceCorrection,
    "Документ.тп_ИсправлениеВзаиморасчетов": models.MutualSettlementCorrection,
    "Документ.тп_ПересчетШКПоПеремещениям": models.BarcodeRecalculation,
    "Документ.тп_ПеремещениеПодДоставку": models.DeliveryTransfer,
    "Документ.тп_ДополнительныеРасходы": models.AdditionalCosts,
    "Документ.тп_ПриемОплаты": models.PaymentReceipt,
    "Документ.тп_ВозвратТовара": models.GoodsReturn,
    "ДокументСсылка.тп_ВозвратОплаты": models.PaymentReturnLink,
    "ДокументСсылка.тп_ПересчетЭкспрессПриемок": models.ExpressAcceptanceRecalculationLink,

    # Регистры
    "МестонахождениеТовара": models.GoodsLocation,
    "ПрямыеЗатраты": models.DirectExpenses,
    "ОбщиеЗатраты": models.GeneralExpenses,
    "СкладскиеЗатраты": models.WarehouseExpenses,
    "ТЗСтоимостьИОплатаТоваров": models.CostAndPaymentGoods,

    # Другое
    "ТП_ДанныеНаУдаление": models.DeletedObject,

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
        CascadeRule(model=models.Goods, column_name="receipt_id"),
        CascadeRule(model=models.GoodsLocation, column_name="registrar_id"),
    ],
}