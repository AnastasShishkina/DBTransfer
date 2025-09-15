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
    "Документ.тп_ПеремещениеТовара": models.Transfers,
    "Документ.тп_ПеремещениеТовара.Товары": models.GoodsTransfers,
    "ПрямыеЗатраты": models.DirectExpenses,
    "Товары": models.Goods,
    "Справочник.тп_ВидыТоваров": models.GoodsTypes,
    "Справочник.тп_Клиенты": models.Clients,
    "Справочник.тп_ТипыУпаковок": models.PackageTypes,
    "МестонахождениеТовара": models.GoodsLocation,
    "ОбщиеЗатраты": models.GeneralExpenses,
    "СкладскиеЗатраты": models.WarehouseExpenses,
    "Документ.тп_ПриемТовара": models.Receipts,
    "Документ.тп_ПриемТовара.Товары": models.GoodsReceipts,



}