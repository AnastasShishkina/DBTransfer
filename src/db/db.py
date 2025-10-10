import uuid

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import Table, MetaData, insert, select, and_, exists, inspect
from sqlmodel import create_engine

from src.config import settings
from src.db.models import DeletedObject
from src.db.registry import REGISTRY, CASCADE_DELETED_MAP
from sqlalchemy import delete as sa_delete
import logging

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, echo=False)  # echo=True
log = logging.getLogger("app")

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


def delete_with_cascade():
    with engine.begin() as conn:
        log.debug("Старт удаления")
        stmt = select(DeletedObject.object_id, DeletedObject.name_metadata)
        rows = conn.execute(stmt).all()
        for object_id, name_metadata in rows:
            log.info("Удаляем %s %s", str(object_id), str(name_metadata))
            dataModel = REGISTRY.get(name_metadata)
            # удаляем  связные объекты
            for rule in CASCADE_DELETED_MAP.get(name_metadata, []):
                log.debug("rule.model %s %s",str(rule.model),str(rule.column_name))
                child_table = rule.model
                column = getattr(child_table, rule.column_name)
                conn.execute(sa_delete(child_table).where(column == object_id))

            # удаляем  объект (по PK или по полю удаления т.к. поле должно быть одно)
            pk_column = (getattr(dataModel, "__scope_delete_cols__", None)
                             or next(iter(inspect(dataModel).primary_key)))

            conn.execute(sa_delete(dataModel).where(pk_column == object_id))

            # удаляем из таблицы удаленных объектов
            pk_column = DeletedObject.object_id
            conn.execute(sa_delete(DeletedObject).where(pk_column == object_id))