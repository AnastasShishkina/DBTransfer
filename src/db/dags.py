from datetime import datetime, date
from typing import Optional, Iterator

from sqlalchemy import text, Engine
from src.db.db import engine
from src.utils import iter_months

# Распределение прямых расходов
ALLOC_DIRECT_EXPENSES_SQL = """
    CREATE TEMP TABLE tmp_table ON COMMIT DROP AS
    SELECT
        'Прямые расходы' AS type_expense,
        de.registrar_id,
        gd.id AS goods_id,
        de.cost_category_id,
        wh.department_id,
        de.date,
        ROUND(de.amount * gd.amount / NULLIF(SUM(gd.amount) OVER (PARTITION BY de.registrar_id), 0), 2) AS amount
    FROM direct_expenses AS de
    JOIN goods_transfers AS gt ON gt.transfer_id = de.goods_doc_id
    JOIN goods AS gd ON gd.id = gt.goods_id
    JOIN transfers AS tf ON tf.id = gt.transfer_id
    JOIN warehouses AS wh ON tf.out_warehouse_id = wh.id
    WHERE gd.amount IS NOT NULL
      AND de.date >= :mstart AND de.date < :mnext   
"""

# Распределение складских расходов
ALLOC_WAREHOUSE_EXPENSES_SQL = """
    CREATE TEMP TABLE tmp_table ON COMMIT DROP AS
    SELECT
        'Складские расходы' AS type_expense,
        we.registrar_id,
        gd.id AS goods_id,
        we.cost_category_id,
        we.department_id,
        we.date,
        ROUND(we.amount * gd.amount / NULLIF(SUM(gd.amount) OVER (PARTITION BY we.registrar_id), 0), 2) AS amount
    FROM warehouse_expenses AS we
    JOIN departments AS de ON de.id = we.department_id
    JOIN warehouses AS wh ON wh.department_id = de.id
    JOIN goods_location AS gl ON gl.sender_warehouse_id = wh.id
    JOIN goods AS gd ON gd.id = gl.goods_id
    WHERE gl.goods_status = 2  -- отправление
      AND we.date >= :mstart AND we.date < :mnext
      AND gl.date >= :mstart AND gl.date < :mnext
    
"""
# Распределение общих расходов
ALLOC_GENERAL_EXPENSES_SQL = """
    CREATE TEMP TABLE tmp_table ON COMMIT DROP AS
    SELECT
        'Общие расходы' AS type_expense,
        ge.registrar_id,
        gd.id AS goods_id,
        ge.cost_category_id,
        wh_out.department_id,
        ge.date,
        ROUND(ge.amount * gd.amount / NULLIF(SUM(gd.amount) OVER (PARTITION BY ge.registrar_id), 0), 2) AS amount
    FROM general_expenses AS ge
    JOIN transfers AS tr
      ON tr.date >= :mstart AND tr.date < :mnext
    JOIN warehouses AS wh_out ON tr.out_warehouse_id = wh_out.id
    JOIN countries  AS cn_out ON wh_out.country_id = cn_out.id
    JOIN warehouses AS wh_in  ON tr.in_warehouse_id = wh_in.id
    JOIN countries  AS cn_in  ON wh_in.country_id  = cn_in.id
    JOIN goods_transfers AS gt ON gt.transfer_id = tr.id
    JOIN goods AS gd ON gd.id = gt.goods_id
    WHERE ge.date >= :mstart AND ge.date < :mnext
      AND cn_out.name = 'КИТАЙ'
      AND cn_in.name <> 'КИТАЙ'
    ;

"""

DELETE_ALLOC_EXPENSES_SQL = """
        DELETE FROM dm_goods_expense_alloc d
        WHERE d.date >= :mstart AND d.date < :mnext
        AND d.type_expense IN (SELECT DISTINCT type_expense FROM tmp_table);
    """


INSERT_ALLOC_EXPENSES_SQL = """
       INSERT INTO dm_goods_expense_alloc 
       (type_expense, registrar_id, goods_id, department_id, cost_category_id, date, amount)
       SELECT type_expense, registrar_id, goods_id, department_id, cost_category_id, date, sum(amount)
       FROM tmp_table
       group by type_expense, registrar_id, goods_id, department_id, cost_category_id, date;
             """


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


def delete_temp_tables(engine: Engine) -> None:
    q = text("DROP TABLE IF EXISTS tmp_table")
    with engine.begin() as conn:
        conn.execute(q, {})


def replace_allocations_for_month(engine: Engine, job_name: str, create_sql_month: str, mstart: date, mnext: date,):
    """
    Запускает один цикл для ОДНОГО месяца:
      1) создаёт TEMP tmp_table c расчётом только за [mstart, mnext)
      2) удаляет старые данные этого типа за месяц
      3) заливает агрегат
      4) фиксирует успех прогона
    """
    with engine.begin() as conn:
        conn.execute(text(create_sql_month), {"mstart": mstart, "mnext": mnext})
        conn.execute(text(DELETE_ALLOC_EXPENSES_SQL), {"mstart": mstart, "mnext": mnext})
        conn.execute(text(INSERT_ALLOC_EXPENSES_SQL))
    mark_success(engine, job_name)



def recalc_period_by_months( engine: Engine,  period_start: date, period_end: date,) -> list[dict]:
    """
    Пересчитать весь период (включая конечный месяц), «месяц за месяцем».
    Возвращает короткие отчёты по каждому месяцу.
    """
    results: list[dict] = []

    for mstart, mnext in iter_months(period_start, period_end):

        replace_allocations_for_month(engine, "alloc_direct_expenses",    ALLOC_DIRECT_EXPENSES_SQL,    mstart, mnext)
        replace_allocations_for_month(engine, "alloc_warehouse_expenses", ALLOC_WAREHOUSE_EXPENSES_SQL, mstart, mnext)
        replace_allocations_for_month(engine, "alloc_general_expenses",   ALLOC_GENERAL_EXPENSES_SQL,   mstart, mnext)

        results.append({
            "month": mstart.strftime("%Y-%m"),
            "from": mstart.isoformat(),
            "to_exclusive": mnext.isoformat(),
            "status": "ok",
        })

    return results
