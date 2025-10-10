from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from sqlalchemy import text, Engine, Connection, inspect
from src.db.sql_query import (
    CREATE_VIEWS_SQL,
    UPDATE_WITH_VIEWS_SQL,
    DROP_VIEWS_SQL,
    DELETE_ALLOC_EXPENSES_SQL,
    INSERT_ALLOC_EXPENSES_SQL,
    ALLOC_DIRECT_EXPENSES_SQL,
    ALLOC_WAREHOUSE_EXPENSES_SQL,
    ALLOC_GENERAL_EXPENSES_SQL,
)
from src.utils import iter_months

PRECISION = 2  # количество знаков после запятой
INC = Decimal(1) / (Decimal(10) ** PRECISION)  # шаг инкремента (0.01 при PRECISION=2)


def get_last_success(engine: Engine, job_name: str) -> Optional[datetime]:
    q = text("select last_success_at from etl_job_status where job_name = :job")
    with engine.begin() as conn:
        row = conn.execute(q, {"job": job_name}).fetchone()
        return row[0] if row else None


def mark_success(engine: Engine, job_name: str, ts: Optional[datetime] = None) -> None:
    q = text("""
        insert into etl_job_status(job_name, last_success_at)
        values (:job, :ts)
        on conflict (job_name) do update set last_success_at = excluded.last_success_at
    """)
    with engine.begin() as conn:
        conn.execute(q, {"job": job_name, "ts": ts or datetime.now()})


def create_temp_table_key(conn: Connection, table_name: str, mstart: date, mnext: date) -> None:
    insp = inspect(conn)
    cols = {c["name"] for c in insp.get_columns(table_name)}
    has_doc = "goods_doc_id" in cols

    doc_expr = "goods_doc_id" if has_doc else "NULL::uuid"

    sql = f"""
        CREATE TEMP TABLE tmp_de_key_amount ON COMMIT DROP AS
        SELECT
            registrar_id,
            cost_category_id,
            {doc_expr} AS goods_doc_id,
            date,
            SUM(amount)::numeric AS total_amount
        FROM {table_name}
        WHERE date >= :mstart AND date < :mnext
        GROUP BY
            registrar_id,
            cost_category_id,
            {doc_expr},    
            date
    """
    conn.execute(text(sql), {"mstart": mstart, "mnext": mnext})


def delete_temp_tables(engine: Engine) -> None:
    q = text("DROP TABLE IF EXISTS tmp_table")
    with engine.begin() as conn:
        conn.execute(q, {})


def replace_allocations_for_month(engine: Engine, table_name: str, create_sql_month: str, mstart: date, mnext: date,):
    """
    Запускает один цикл для ОДНОГО месяца:
        создаёт TEMP таблицу с уникальным ключом затраты и ее суммой
        создаёт TEMP tmp_table c расчётом только за [mstart, mnext)
        прибавляет погрешность при разделении самому дорогому товару
        удаляет старые данные этого типа за месяц
        вставка агрегата
        фиксация успех прогона
    """
    with engine.begin() as conn:
        create_temp_table_key(conn, table_name, mstart, mnext)
        conn.execute(text(create_sql_month), {"mstart": mstart, "mnext": mnext, "precision": PRECISION})

        # создать вьюшки
        conn.execute(text(CREATE_VIEWS_SQL))

        # «только плюс» корректировка с твоим шагом инкремента
        conn.execute(text(UPDATE_WITH_VIEWS_SQL), {"inc": str(INC)})

        # убрать вьюшки
        conn.execute(text(DROP_VIEWS_SQL))

        # перезалить агрегат
        conn.execute(text(DELETE_ALLOC_EXPENSES_SQL), {"mstart": mstart, "mnext": mnext})
        conn.execute(text(INSERT_ALLOC_EXPENSES_SQL))

    mark_success(engine, table_name)


def recalc_period_by_months( engine: Engine,  period_start: date, period_end: date,) -> list[dict]:
    """
    Пересчитать весь период (включая конечный месяц), «месяц за месяцем».
    Возвращает короткие отчёты по каждому месяцу.
    """
    results: list[dict] = []

    for mstart, mnext in iter_months(period_start, period_end):

        replace_allocations_for_month(engine, "reg_direct_expenses",    ALLOC_DIRECT_EXPENSES_SQL,    mstart, mnext)
        replace_allocations_for_month(engine, "reg_warehouse_expenses", ALLOC_WAREHOUSE_EXPENSES_SQL, mstart, mnext)
        replace_allocations_for_month(engine, "reg_general_expenses",   ALLOC_GENERAL_EXPENSES_SQL,   mstart, mnext)

        results.append(
            {
                "month": mstart.strftime("%Y-%m"),
                "status": "ok",
            }
        )

    return results

