# app/registry.py
from src.db.models import StgExpenseItem, StgCitiesV1, StgCitiesV2

REGISTRY = {
    "Справочники.тп_СтатьиЗатрат": {
        "model": StgExpenseItem,
        "pk": ["external_id"],
    },
    "Справочники.тп_Города": {
        "model": StgCitiesV1,
        "pk": ["external_id"],
    },
    "Справочники.тп_Города2": {
        "model": StgCitiesV2,
        "pk": ["external_id"],
    },
    # ... добавляешь новые источники по мере появления
}