import json

from src.db.db import replace_scope
from src.db.registry import REGISTRY
import logging

log = logging.getLogger("app")


class AppError(Exception):
    """Базовая ошибка приложения."""

class MetadataNotRegistered(AppError):
    def __init__(self, name_meta: str):
        super().__init__(f"Неизвестные метаданные: {name_meta}. Добавьте связку в REGISTRY.")

class DataFormatError(AppError):
    pass


def handle_json(body):
    templates = json.loads(body)
    for template in templates:
        name_meta  = template.get("НаименованиеМетаданных")
        items = template.get("Данные")
        dataModel = REGISTRY.get(name_meta)

        if not dataModel:
            log.error("Новое название метаданных %s. Нет связки в REGISTRY", name_meta)
            raise MetadataNotRegistered(name_meta)

        if not isinstance(items, list):
            raise DataFormatError(f"В '{name_meta}' поле 'Данные' должно быть списком")

        log.debug("Обработка %s , количество строк %i", name_meta, len(items))
        replace_scope(dataModel, items)

