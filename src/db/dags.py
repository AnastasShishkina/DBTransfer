from datetime import datetime
from typing import Optional

from sqlalchemy import text, Engine
from src.db.db import engine



# Распределение прямых расходов
ALLOC_DIRECT_EXPENSES_SQL = """
    WITH alloc(type_expense, registrar_id, goods_id, cost_category_id, date, amount) as
    (SELECT  
        'Прямые расходы' as type_expense,
        de.registrar_id, 
        gd.id AS goods_id,
        de.cost_category_id,
        de.date,
        ROUND( de.amount * gd.amount / NULLIF(SUM(gd.amount) 
        OVER (PARTITION BY de.registrar_id), 0), 2) AS amount
        FROM direct_expenses de, goods_transfers gt, goods gd
        WHERE de.goods_doc_id = gt.transfer_id
        AND gt.goods_id = gd.id
        AND gd.amount is NOT NULL
        AND (:since IS NULL OR de.updated_at >= :since )
    )
    insert into dm_goods_expense_alloc (type_expense, registrar_id, goods_id, cost_category_id, date, amount)
    select  type_expense, registrar_id, goods_id, cost_category_id, date, amount
    from alloc
    on conflict (type_expense, registrar_id, goods_id, cost_category_id) do update
    set amount = excluded.amount
"""

# Распределение складских расходов
ALLOC_WAREHOUSE_EXPENSES_SQL = """
    WITH alloc(type_expense, registrar_id, goods_id, cost_category_id, date, amount) as
    (SELECT 
        'Складские расходы' as type_expense,
        we.registrar_id, 
        gd.id AS goods_id,
        we.cost_category_id,
        we.date,
        ROUND( we.amount * gd.amount / NULLIF(SUM(gd.amount) OVER (PARTITION BY we.registrar_id), 0), 2 ) AS amount
        FROM warehouse_expenses we,
        departments de ,
        warehouses wh ,
        goods_location gl ,
        goods gd
        WHERE
        we.department_id = de.id
        AND de.id = wh.department_id
        AND gl.sender_warehouse_id = wh.id
        AND gl.goods_status = 2 --отправление
        AND gl.date >= date_trunc('month', we.date)
        AND gl.date <  (date_trunc('month', we.date) + interval '1 month')
        AND gl.goods_id = gd.id
        AND (:since IS NULL OR we.updated_at >= :since )
    )
    INSERT INTO dm_goods_expense_alloc (type_expense, registrar_id, goods_id, cost_category_id, date, amount)
    SELECT type_expense, registrar_id, goods_id, cost_category_id, date, sum(amount)
    FROM alloc
    GROUP BY  type_expense, registrar_id, goods_id, cost_category_id, date
    ON conflict (type_expense, registrar_id, goods_id, cost_category_id) do update
    set amount = excluded.amount
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


def upsert_allocations(job_name, sql, since_date: Optional[datetime] = None, full=False) -> int:
    """
    Запуск агрегации:
    - full=True -> полный пересчёт (since=None)
    - since_date задан -> берём его
    - иначе -> берём дату последнего успешного запуска из etl_job_status
    """

    since = None if full else (since_date or get_last_success(engine, job_name))
    with engine.begin() as conn:
        res = conn.execute(text(sql), {"since": since})
        affected = res.rowcount if res.rowcount is not None else 0
    mark_success(engine, job_name)
    return affected


if __name__ == "__main__":
    upsert_allocations("alloc_direct_expenses", ALLOC_DIRECT_EXPENSES_SQL)
    upsert_allocations("warehouse_expenses", ALLOC_WAREHOUSE_EXPENSES_SQL)
