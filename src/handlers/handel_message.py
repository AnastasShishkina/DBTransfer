import json

from src.db.db import upsert_data
from src.handlers.registry import REGISTRY


def handle_json(body):
    # TODO: минимальная проврека на формат JSON
    templates = json.loads(body)
    for template in templates:
        nameMetaData = template.get("НаименованиеМетаданных")
        data = template.get("Данные")
        dataModel = REGISTRY.get(nameMetaData)

        if not dataModel:
            print("Нет в регистре. Добавь связку метаданных и таблицы БД в REGISTRY", nameMetaData)
            continue

        upsert_data(dataModel, data)


