import json

from src.db.db import replace_scope
from src.handlers.registry import REGISTRY
import logging

log = logging.getLogger("app")

def handle_json(body):
    # TODO: минимальная проврека на формат JSON
    templates = json.loads(body)

    for template in templates:
        nameMetaData = template.get("НаименованиеМетаданных")
        data = template.get("Данные")
        dataModel = REGISTRY.get(nameMetaData)

        if not dataModel:
            log.error("Нет в регистре. Добавь связку метаданных и таблицы БД в REGISTRY", nameMetaData)
            continue
        log.debug("Обработка %s , количество строк %i", nameMetaData, len(data))
        replace_scope(dataModel, data)


