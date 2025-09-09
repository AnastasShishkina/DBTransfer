from src.db.models import StgCitiesConfig, StgCitiesV2, StgExpenseItem, StgExpenseRecord

REGISTRY = {
    "Справочники.тп_СтатьиЗатрат": {"model": StgExpenseItem},
    "Справочники.тп_Города": {"model": StgCitiesConfig},
    "Справочники.тп_Города2": {"model": StgCitiesV2},
    "ПрямыеЗатраты": {"model": StgExpenseRecord},
    # Вложенная структура:
    # "Прием_товара": {
    #     "model": StgGoodsReceipt,           # куда пишем корневой объект
    #     "pk_attr": "goods_doc_id",          # как звать PK в модели (чтобы прокинуть в детей)
    #     "children": [
    #         {
    #             "array": "Товары",          # ключ массива в JSON
    #             "model": StgGoodsReceiptItem,
    #             "fk_attr": "goods_doc_id",  # имя FK-поля в дочерней модели
    #         },
    #         {
    #             "array": "ДополнительныеРасходы",
    #             "model": StgGoodsReceiptExpense,
    #             "fk_attr": "goods_doc_id",
    #         },
    #     ],
    # },
}
