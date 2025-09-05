import json
from src.handlers.registry import REGISTRY
from src.db.db import upsert_data

def handle_json(body):
    # TODO: минимальная проврека на формат JSON
    templates = json.loads(body)
    for template in templates:
        nameMetaData = template.get('НаименованиеМетаданных')
        data = template.get('Данные')

        if nameMetaData not in REGISTRY:
            # TODO: переделать
            print('%s Нет в регистре. Добавь связку метаданных и таблицы БД в REGISTRY' %(nameMetaData))
            raise Exception

        configMetaData = REGISTRY[nameMetaData]
        upsert_data(configMetaData, data)


#
# ParentModel = cfg["model"]
#         parent_rows: list[dict[str, Any]] = []
#         children_cfg = cfg.get("children", [])
#         child_rows: dict[type[SQLModel], list[dict[str, Any]]] = {c["model"]: [] for c in children_cfg}
#
#         pk_attr = cfg.get("pk_attr")  # например "goods_doc_id" (для «Прием_товара»)
#
#         for rec in data_list:
#             # родитель
#             parent_obj = ParentModel.model_validate(rec)
#             parent_dict = parent_obj.model_dump(by_alias=False, exclude_none=True)
#             parent_rows.append(parent_dict)
#
#             # если есть вложенные — обрабатываем
#             if children_cfg and pk_attr:
#                 parent_id = parent_dict[pk_attr]
#                 for c in children_cfg:
#                     arr = rec.get(c["array"], []) or []
#                     ChildModel = c["model"]
#                     fk_attr = c["fk_attr"]
#
#                     for item in arr:
#                         # прокидываем FK из родителя
#                         row_data = dict(item)
#                         row_data[fk_attr] = parent_id
#
#                         child_obj = ChildModel.model_validate(row_data)
#                         child_rows[ChildModel].append(
#                             child_obj.model_dump(by_alias=False, exclude_none=True)
#                         )
