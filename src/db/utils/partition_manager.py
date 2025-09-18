# scripts/auto_partitions.py
from __future__ import annotations
import argparse
from datetime import date, datetime
from typing import List, Dict, Tuple

from sqlalchemy import text, inspect
from sqlalchemy.engine import Engine, Connection


from src.db.db import engine
from src.db import models as app_models  # noqa
from sqlmodel import SQLModel

from src.db.models import dev_drop_all_tables


# ---------- helpers ----------

def month_bounds(year: int, month: int) -> Tuple[date, date]:
    start = date(year, month, 1)
    end = date(year + (month // 12), (month % 12) + 1, 1)
    return start, end

def table_is_partitioned_parent_in_models(table) -> bool:
    """Проверка по моделям: наличие декларативного партиционирования."""

    po = table.dialect_options.get("postgresql") if hasattr(table, "dialect_options") else {}
    if not po:
        return False
        # варианты ключей встречаются разные
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

def ensure_default_partition(conn: Connection, schema: str, parent: str) -> str:
    part_name = f"{parent}_default"
    exists = conn.execute(text("""
        SELECT 1 FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE c.relname = :rel AND n.nspname = :schema
    """), {"rel": part_name, "schema": schema}).scalar()
    if not exists:
        conn.execute(text(f"""
        DO $$
        BEGIN
          EXECUTE format('CREATE TABLE %I.%I PARTITION OF %I.%I DEFAULT',
                         :schema, :part, :schema, :parent);
        END $$;
        """), {"schema": schema, "part": part_name, "parent": parent})
        print(f"[OK] DEFAULT партиция создана: {schema}.{part_name}")
    else:
        print(f"[=] DEFAULT партиция уже есть: {schema}.{part_name}")
    return part_name

def ensure_month_partition_with_indexes(
    conn: Connection,
    schema: str,
    parent: str,
    year: int,
    month: int,
    #parent_partitioned_indexes: List[Dict],
) -> str:
    part_name = f"{parent}_{year}_{month:02d}"
    exists = conn.execute(text("""
        SELECT 1 FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE c.relname = :rel AND n.nspname = :schema
    """), {"rel": part_name, "schema": schema}).scalar()
    mstart, mnext = month_bounds(year, month)

    if not exists:
        conn.execute(text(f"""
        DO $$
        BEGIN
          EXECUTE format(
            'CREATE TABLE %I.%I PARTITION OF %I.%I FOR VALUES FROM (''%s'') TO (''%s'')',
            :schema, :part, :schema, :parent, :mstart, :mnext
          );
        END $$;
        """), {"schema": schema, "part": part_name, "parent": parent, "mstart": mstart, "mnext": mnext})
        print(f"[OK] Создана партиция: {schema}.{part_name} [{mstart} .. {mnext})")
    else:
        print(f"[=] Партиция уже есть: {schema}.{part_name}")

    # # Индексы: для каждого partitioned-индекса на родителе — создаём локальный и ATTACH
    # for pidx in parent_partitioned_indexes:
    #     cols = ", ".join([f'"{c}"' for c in pidx["column_names"]])
    #     child_idx_name = f'{pidx["name"]}__{year}_{month:02d}'
    #     # локальный индекс (если нет)
    #     conn.execute(text(f"""
    #     DO $$
    #     BEGIN
    #       IF NOT EXISTS (
    #         SELECT 1 FROM pg_class c
    #         JOIN pg_namespace n ON n.oid = c.relnamespace
    #         WHERE c.relname = :idx AND n.nspname = :schema
    #       ) THEN
    #         EXECUTE format('CREATE INDEX %I ON %I.%I ({cols})',
    #                        :idx, :schema, :part);
    #       END IF;
    #     END $$;
    #     """.replace("{cols}", cols)), {"idx": child_idx_name, "schema": schema, "part": part_name})
    #
    #     # ATTACH к родительскому partitioned-индексу (если ещё не прикреплён)
    #     conn.execute(text("""
    #     DO $$
    #     BEGIN
    #       IF NOT EXISTS (
    #         SELECT 1
    #         FROM pg_index i
    #         JOIN pg_class ic ON ic.oid = i.indexrelid
    #         JOIN pg_class tc ON tc.oid = i.indrelid
    #         JOIN pg_namespace n ON n.oid = tc.relnamespace
    #         WHERE ic.relname = :child_idx AND n.nspname = :schema
    #       ) THEN
    #         -- сам локальный индекс уже создан выше
    #         NULL;
    #       END IF;
    #
    #       -- попробовать прикрепить (если уже прикреплён — PG бросит ошибку, ловим и игнорим)
    #       BEGIN
    #         EXECUTE format('ALTER INDEX %I.%I ATTACH PARTITION %I.%I',
    #                        :schema, :parent_idx, :schema, :child_idx);
    #       EXCEPTION WHEN duplicate_object THEN
    #         -- уже прикреплён
    #         NULL;
    #       END;
    #     END $$;
    #     """), {"schema": schema, "parent_idx": pidx["name"], "child_idx": child_idx_name})

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
    Используем системные каталоги, чтобы получить имена и колонки.
    """
    # берём только partitioned-индексы (indispartition = false, но index создан на родителе; в PG это отдельный тип)
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
      AND i.indispartition = FALSE  -- сам индекс на родителе (partitioned index), не локальный индекс партиции
    ORDER BY ic.relname, k.ord
    """), {"schema": schema, "parent": parent}).fetchall()

    # сгруппируем колонки по индексу
    out: Dict[str, Dict] = {}
    for r in rows:
        info = out.setdefault(r.index_name, {"name": r.index_name, "column_names": [], "unique": r.is_unique})
        info["column_names"].append(r.column_name)
    return list(out.values())


# ---------- main ----------
def create_year_partitions(year) -> None:
    model_parents = list_partitioned_parents_from_models()
    if not model_parents:
        print("В моделях не найдено ни одной partitioned-таблицы.")
        return

    with engine.begin() as conn:
        for schema, parent in model_parents:
            # Перепроверим, что в БД таблица существует и действительно partitioned
            if not table_is_partitioned_parent_in_db(conn, schema, parent):
                print(
                    f"[!] Пропуск: {schema}.{parent} — в БД не обнаружена как partitioned (создайте родителя с PARTITION BY)."
                )
                continue

            print(f"\n=== {schema}.{parent} — год {year} ===")
            ensure_default_partition(conn, schema, parent)

            # возьмём partitioned-индексы у родителя
            #pidx = list_partitioned_indexes_on_parent(conn, schema, parent)

            # создадим 12 помесячных партиций (+индексы с attach)
            for month in range(1, 13):
                ensure_month_partition_with_indexes(conn, schema, parent, year, month)
    print("\nГотово ✅")


if __name__ == "__main__":
    create_year_partitions(datetime.now().year)
    #create_year_partitions(2025)
