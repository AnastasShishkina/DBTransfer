#import logging
from typing import Dict, Any, List
from sqlmodel import Session
from src.db.db import upsert_sqlmodel
from src.db.models import StagingBase

#log = logging.getLogger(__name__)

def load_list(meta_name: str, items: List[Dict[str, Any]], model_cls: type[StagingBase], pk_cols: list[str], session: Session):
    for raw in items:
        dto = model_cls.model_validate(raw)
        payload = dto.model_dump(by_alias=False)
        # пример нормализации "нулевых" GUID можно вставить здесь
        upsert_sqlmodel(model_cls, payload, conflict_cols=pk_cols, exclude_update={"created_at", "updated_at"}, session=session)
