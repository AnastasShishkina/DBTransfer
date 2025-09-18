import uuid
from typing import Any

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import Table, MetaData, insert, select, and_, exists
from sqlmodel import Session, create_engine

from src.config import settings
from src.utils import _chunked, timeit

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, echo=False)  # echo=True


def replace_scope(dataModel, rows):
    """
       Полная замена строк по переданным PK:
       1) CREATE TEMP TABLE AS SELECT * FROM (VALUES ... ) v(cols...)
       2) DELETE target USING temp по PK
       3) INSERT target(cols) SELECT cols FROM temp
    """
    if not rows:
        return
    normalized = []
    for raw in rows:
        dto = dataModel.model_validate(raw)
        normalized.append(dto.dict(by_alias=False, exclude_unset=True))

    target_tbl = dataModel.__table__

    with engine.begin() as conn:
        prep = conn.dialect.identifier_preparer
        def qtbl(tbl) -> str:
            return f"{prep.quote_schema(tbl.schema)}.{prep.quote(tbl.name)}" if tbl.schema else prep.quote(tbl.name)

        target_name = qtbl(target_tbl)
        tmp_name = f"tmp_{target_tbl.name}_{uuid.uuid4().hex[:8]}"
        tmp_qname = prep.quote(tmp_name)

        # TEMP по структуре приёмника
        conn.exec_driver_sql(f"CREATE TEMP TABLE {tmp_qname} (LIKE {target_name} INCLUDING DEFAULTS);")

        # рефлексия TEMP, чтобы использовать Core-инсерты
        temp_tbl = Table(tmp_name, MetaData(), autoload_with=conn)

        # bulk INSERT в TEMP
        conn.execute(insert(temp_tbl), normalized)

        # DELETE из приёмника по scope (из модели или PK)

        # список колонок, по которым чистим срез
        scope_columns = getattr(dataModel, "__scope_delete_cols__", None) or [
            col.name for col in target_tbl.primary_key.columns
        ]

        # равенство по всем колонкам скоупа между целевой и временной таблицами
        scope_conditions = and_(*(target_tbl.c[column_name] == temp_tbl.c[column_name] for column_name in scope_columns)
        )

        # DELETE из целевой всех строк, для которых во временной есть запись с тем же скоупом
        delete_stmt = target_tbl.delete().where(exists(select(1).select_from(temp_tbl).where(scope_conditions)))
        conn.execute(delete_stmt)

        # INSERT из TEMP в приёмник (только нужные колонки)
        insert_cols = list(normalized[0].keys())
        sel = select(*(temp_tbl.c[c] for c in insert_cols))
        conn.execute(insert(target_tbl).from_select(insert_cols, sel))

        conn.exec_driver_sql(f"DROP TABLE IF EXISTS {tmp_qname};")
