from __future__ import annotations
from datetime import date, datetime
from typing import List, Dict, Tuple

from sqlalchemy import text
from sqlalchemy.engine import Connection

from src.db.db import engine
from src.db import models as app_models  # noqa
from sqlmodel import SQLModel

from src.db.models import dev_drop_all_tables

# ---------- helpers ----------

PARTITIONS_SCHEMA = "partitions"  # здесь будут жить дочерние партиции

def ensure_schema_exists(conn: Connection, schema: str) -> None:
    conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema};"))

def month_bounds(year: int, month: int) -> Tuple[date, date]:
    start = date(year, month, 1)
    end = date(year + (month // 12), (month % 12) + 1, 1)
    return start, end

def table_is_partitioned_parent_in_models(table) -> bool:
    """Проверка по моделям: наличие декларативного партиционирования."""
    po = table.dialect_options.get("postgresql") if hasattr(table, "dialect_options") else {}
    if not po:
        return False
    # варианты ключей (в зависимости от версии/генератора)
    v = po.get("partition_by") or po.get("postgresql_partition_by")
    return bool(v)

def table_is_partitioned_parent_in_db(conn: Connection, schema: str, name: str) -> bool:
    return bool(conn.execute(text("""
        SELECT 1
        FROM pg_partitioned_table pt
        JOIN pg_class c ON c.oid = pt.partrelid
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = :schema AND c.relname = :name
    """), {"schema": schema, "name": name}).scalar())

def ensure_default_partition(conn: Connection, parent_schema: str, parent: str, child_schema: str = PARTITIONS_SCHEMA) -> str:
    """Создаёт DEFAULT-партицию в схеме child_schema, прикреплённую к parent_schema.parent"""
    ensure_schema_exists(conn, child_schema)
    part_name = f"{parent}_default"

    exists = conn.execute(text("""
        SELECT 1 FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE c.relname = :rel AND n.nspname = :schema
    """), {"rel": part_name, "schema": child_schema}).scalar()

    if not exists:
        conn.execute(text("""
        DO $$
        BEGIN
          EXECUTE format(
            'CREATE TABLE %I.%I PARTITION OF %I.%I DEFAULT',
            :child_schema, :part, :parent_schema, :parent
          );
        END $$;
        """), {"child_schema": child_schema, "part": part_name, "parent_schema": parent_schema, "parent": parent})
        print(f"[OK] DEFAULT партиция создана: {child_schema}.{part_name} (родитель {parent_schema}.{parent})")
    else:
        print(f"[=] DEFAULT партиция уже есть: {child_schema}.{part_name}")

    return part_name

def ensure_month_partition_with_indexes(
    conn: Connection,
    parent_schema: str,
    parent: str,
    year: int,
    month: int,
    child_schema: str = PARTITIONS_SCHEMA,
) -> str:
    """Создаёт месячную партицию в схеме child_schema и прикрепляет к parent_schema.parent"""
    ensure_schema_exists(conn, child_schema)
    part_name = f"{parent}_{year}_{month:02d}"

    exists = conn.execute(text("""
        SELECT 1 FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE c.relname = :rel AND n.nspname = :schema
    """), {"rel": part_name, "schema": child_schema}).scalar()

    mstart, mnext = month_bounds(year, month)

    if not exists:
        conn.execute(text("""
        DO $$
        BEGIN
          EXECUTE format(
            'CREATE TABLE %I.%I PARTITION OF %I.%I FOR VALUES FROM (''%s'') TO (''%s'')',
            :child_schema, :part, :parent_schema, :parent, :mstart, :mnext
          );
        END $$;
        """), {
            "child_schema": child_schema,
            "part": part_name,
            "parent_schema": parent_schema,
            "parent": parent,
            "mstart": mstart,
            "mnext": mnext
        })
        print(f"[OK] Создана партиция: {child_schema}.{part_name} [{mstart} .. {mnext}) → родитель {parent_schema}.{parent}")
    else:
        print(f"[=] Партиция уже есть: {child_schema}.{part_name}")

    return part_name

def get_schema_and_name(table) -> Tuple[str, str]:
    sch = table.schema or "public"
    return sch, table.name

def list_partitioned_parents_from_models() -> List[Tuple[str, str]]:
    """Возвращает [(schema, table_name)] из моделей, у которых включено декларативное партиционирование."""
    parents = []
    for table in SQLModel.metadata.tables.values():
        if table_is_partitioned_parent_in_models(table):
            parents.append(get_schema_and_name(table))
    return parents

def list_partitioned_indexes_on_parent(conn: Connection, schema: str, parent: str) -> List[Dict]:
    """
    Возвращает список partitioned-индексов у родителя (индексы, созданные на родителе).
    """
    rows = conn.execute(text("""
    SELECT
      ic.relname AS index_name,
      a.attname  AS column_name,
      i.indisunique AS is_unique,
      i.indnkeyatts
    FROM pg_index i
    JOIN pg_class ic ON ic.oid = i.indexrelid
    JOIN pg_class tc ON tc.oid = i.indrelid
    JOIN pg_namespace n ON n.oid = tc.relnamespace
    JOIN unnest(i.indkey) WITH ORDINALITY AS k(attnum, ord) ON TRUE
    JOIN pg_attribute a ON a.attrelid = tc.oid AND a.attnum = k.attnum
    WHERE n.nspname = :schema
      AND tc.relname = :parent
      AND i.indisvalid = TRUE
      AND i.indisready = TRUE
      AND i.indispartition = FALSE
    ORDER BY ic.relname, k.ord
    """), {"schema": schema, "parent": parent}).fetchall()

    out: Dict[str, Dict] = {}
    for r in rows:
        info = out.setdefault(r.index_name, {"name": r.index_name, "column_names": [], "unique": r.is_unique})
        info["column_names"].append(r.column_name)
    return list(out.values())


# ---------- main ----------

def create_year_partitions(year = datetime.now().year) -> None:
    model_parents = list_partitioned_parents_from_models()
    if not model_parents:
        print("В моделях не найдено ни одной partitioned-таблицы.")
        return

    with engine.begin() as conn:
        # гарантируем, что схема для партиций существует
        ensure_schema_exists(conn, PARTITIONS_SCHEMA)

        for parent_schema, parent in model_parents:
            # Перепроверим, что в БД таблица существует и действительно partitioned
            if not table_is_partitioned_parent_in_db(conn, parent_schema, parent):
                print(f"[!] Пропуск: {parent_schema}.{parent} — в БД не обнаружена как partitioned (создайте родителя с PARTITION BY).")
                continue

            print(f"\n=== {parent_schema}.{parent} — год {year} → партиции в {PARTITIONS_SCHEMA} ===")

            # DEFAULT-партиция в partitions
            ensure_default_partition(conn, parent_schema=parent_schema, parent=parent, child_schema=PARTITIONS_SCHEMA)

            # Если нужно учитывать индексы-родителя, можно получить их тут (оставлено как задел):
            # pidx = list_partitioned_indexes_on_parent(conn, parent_schema, parent)

            # создаём 12 месяцев в partitions
            for month in range(1, 13):
                ensure_month_partition_with_indexes(
                    conn,
                    parent_schema=parent_schema,
                    parent=parent,
                    year=year,
                    month=month,
                    child_schema=PARTITIONS_SCHEMA,
                )

    print("\nГотово ✅")


if __name__ == "__main__":
    #dev_drop_all_tables(engine)
    create_year_partitions(datetime.now().year)
    # create_year_partitions(2025)
