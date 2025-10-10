"""
Пакет моделей БД проекта.
Разделение:
- base.py — базовые классы и миксины
- refs.py — справочники (ref_)
- docs.py — документы (doc_)
- regs.py — регистры (reg_)
- other.py — другие таблицы (служебные, агрегаты и т.д.)
"""

from sqlmodel import SQLModel

# Импортируем подмодули, чтобы зарегистрировать все таблицы в metadata
from .refs import (
    Departments,
    CostCategories,
    TypesTransport,
    Transports,
    Countries,
    Cities,
    Counterparties,
    Routes,
    Warehouses,
    CargoCategory,
    GoodsTypes,
    PackageTypes,
    Clients,
    PriceTypes,
    Goods,
)

from .docs import (
    Transfers,
    GoodsTransfers,
    Receipts,
    GoodsReceipts,
    DiscountsOnGoods,
    AdditionalTransferCosts,
    DebtReturn,
    FreightRateChange,
    RegistersAdjustment,
    GoodsAcceptanceCorrection,
    MutualSettlementCorrection,
    BarcodeRecalculation,
    DeliveryTransfer,
    AdditionalCosts,
    PaymentReceipt,
    GoodsReturn,
    PaymentReturnLink,
    ExpressAcceptanceRecalculationLink,
)

from .regs import (
    GoodsLocation,
    DirectExpenses,
    GeneralExpenses,
    WarehouseExpenses,
    CostAndPaymentGoods,
)

from .other import (
    DeletedObject,
    DmGoodsExpenseAlloc,
    TelegramChats
)

__all__ = [
    # справочники
    "Departments", "CostCategories", "TypesTransport", "Transports",
    "Countries", "Cities", "Counterparties", "Routes", "Warehouses",
    "CargoCategory", "GoodsTypes", "PackageTypes", "Clients",
    "PriceTypes", "Goods",
    # документы
    "Transfers", "GoodsTransfers", "Receipts", "GoodsReceipts",
    "DiscountsOnGoods", "AdditionalTransferCosts", "DebtReturn",
    "FreightRateChange", "RegistersAdjustment", "GoodsAcceptanceCorrection",
    "MutualSettlementCorrection", "BarcodeRecalculation", "DeliveryTransfer",
    "AdditionalCosts", "PaymentReceipt", "GoodsReturn", "PaymentReturnLink",
    "ExpressAcceptanceRecalculationLink",
    # регистры
    "GoodsLocation", "DirectExpenses", "GeneralExpenses",
    "WarehouseExpenses", "CostAndPaymentGoods",
    # другие
    "DeletedObject",
    "DmGoodsExpenseAlloc",
    "TelegramChats",

]


# metadata для Alembic и create_all
metadata = SQLModel.metadata

