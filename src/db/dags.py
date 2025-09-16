from datetime import datetime
from typing import Optional

from sqlalchemy import text, Engine
from src.db.db import engine



# Распределение прямых расходов
ALLOC_DIRECT_EXPENSES_SQL = """
    CREATE TABLE tmp_table AS (
     SELECT  
        'Прямые расходы' as type_expense,
        de.registrar_id, 
        gd.id AS goods_id,
        de.cost_category_id,
     	wh.department_id,
        de.date,
        ROUND( de.amount * gd.amount / NULLIF(SUM(gd.amount) 
        OVER (PARTITION BY de.registrar_id), 0), 2) AS amount
    FROM direct_expenses AS de
		JOIN goods_transfers AS gt ON gt.transfer_id = de.goods_doc_id
		JOIN goods AS gd ON gd.id = gt.goods_id
		JOIN transfers as tf ON tf.id = gt.transfer_id
		JOIN warehouses as wh ON tf.out_warehouse_id = wh.id
	WHERE gd.amount IS NOT NULL
        AND (:since IS NULL OR de.updated_at >= :since )
        )
"""

# Распределение складских расходов
ALLOC_WAREHOUSE_EXPENSES_SQL = """
    CREATE TABLE tmp_table AS (
    SELECT
        'Складские расходы'::text AS type_expense,
        we.registrar_id,
        gd.id AS goods_id,
        we.cost_category_id,
        we.department_id,
        we.date,
        ROUND( we.amount * gd.amount / NULLIF(SUM(gd.amount) OVER (PARTITION BY we.registrar_id), 0),2) AS amount
    FROM warehouse_expenses AS we
        JOIN departments AS de ON de.id = we.department_id
        JOIN warehouses AS wh ON wh.department_id = de.id
        JOIN goods_location AS gl ON gl.sender_warehouse_id = wh.id
        JOIN goods AS gd ON gd.id = gl.goods_id
    WHERE gl.goods_status = 2   -- отправление
        AND gl.date >= date_trunc('month', we.date)
        AND gl.date <  (date_trunc('month', we.date) + interval '1 month')
        AND (:since IS NULL OR we.updated_at >= :since )
        )
    
"""
# Распределение общих расходов
ALLOC_GENERAL_EXPENSES_SQL = """
    CREATE TABLE tmp_table AS (
    SELECT 'Общие расходы' as type_expense,
        ge.registrar_id,
        gd.id AS goods_id,
        ge.cost_category_id,
        wh_out.department_id,
        ge.date,
        ROUND( ge.amount * gd.amount / NULLIF(SUM(gd.amount) OVER (PARTITION BY ge.registrar_id), 0),2) AS amount
	FROM general_expenses AS ge
		JOIN transfers AS tr ON  (tr.date >= date_trunc('month', ge.date)
        AND tr.date <  (date_trunc('month', ge.date) + interval '1 month'))
		JOIN warehouses wh_out ON tr.out_warehouse_id= wh_out.id
		JOIN countries cn_out ON wh_out.country_id= cn_out.id
		JOIN warehouses wh_in ON tr.in_warehouse_id= wh_in.id
		JOIN countries cn_in ON wh_in.country_id= cn_in.id
		JOIN goods_transfers AS gt ON gt.transfer_id = tr.id
		JOIN goods AS gd ON gd.id = gt.goods_id
	WHERE cn_out.name='КИТАЙ'
		AND cn_in.name!='КИТАЙ'
		AND (:since IS NULL OR ge.updated_at >= :since )
       ) 

"""

DELETE_ALLOC_EXPENSES_SQL = """
        DELETE FROM dm_goods_expense_alloc d
        USING (
          SELECT DISTINCT  registrar_id, type_expense
          FROM tmp_table
        ) k
        WHERE d.registrar_id = k.registrar_id
        AND d.type_expense = k.type_expense;
    """


INSERT_ALLOC_EXPENSES_SQL = """
       INSERT INTO dm_goods_expense_alloc (type_expense, registrar_id, goods_id, department_id,cost_category_id, date, amount)
       SELECT type_expense, registrar_id, department_id, goods_id, cost_category_id, date, sum(amount)
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


def upsert_allocations(job_name, create_sql, since_date: Optional[datetime] = None, full=False) -> int:
    """
    Запуск агрегации:
    - full=True -> полный пересчёт (since=None)
    - since_date задан -> берём его
    - иначе -> берём дату последнего успешного запуска из etl_job_status
    """

    since = None if full else (since_date or get_last_success(engine, job_name))
    delete_temp_tables(engine)
    print('delete_temp_tables')
    with engine.begin() as conn:
        conn.execute(text(create_sql), {"since": since})
        conn.execute(text(DELETE_ALLOC_EXPENSES_SQL), {})
        conn.execute(text(INSERT_ALLOC_EXPENSES_SQL), {})
    delete_temp_tables(engine)
    mark_success(engine, job_name)


if __name__ == "__main__":
    upsert_allocations("alloc_direct_expenses", ALLOC_DIRECT_EXPENSES_SQL, full=True)
    upsert_allocations("alloc_warehouse_expenses", ALLOC_WAREHOUSE_EXPENSES_SQL, full=True)
    upsert_allocations("alloc_general_expenses", ALLOC_GENERAL_EXPENSES_SQL, full=True)