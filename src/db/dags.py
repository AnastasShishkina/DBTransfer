from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Iterator

from sqlalchemy import text, Engine
from src.db.db import engine
from src.utils import iter_months

PRECISION = 2  # количество знаков после запятой
INC = Decimal(1) / (Decimal(10) ** PRECISION)  # шаг инкремента (0.01 при PRECISION=2)

# Распределение прямых расходов
ALLOC_DIRECT_EXPENSES_SQL = """
    CREATE TEMP TABLE tmp_table ON COMMIT DROP AS
        SELECT
            'Прямые расходы' AS type_expense,
            t_de.registrar_id,
            gd.id AS goods_id,
            t_de.cost_category_id,
            wh.department_id,
            t_de.date,
            ROUND(t_de.total_amount * gd.amount / NULLIF(SUM(gd.amount) OVER (PARTITION BY t_de.registrar_id, t_de.cost_category_id), 0), :precision) AS amount
        FROM tmp_de_key_amount AS t_de
        JOIN direct_expenses AS de ON (t_de.registrar_id = de.registrar_id AND t_de.cost_category_id = de.cost_category_id)
        JOIN goods_transfers AS gt ON gt.transfer_id = de.goods_doc_id
        JOIN goods AS gd ON gd.id = gt.goods_id
        JOIN transfers AS tf ON tf.id = gt.transfer_id
        JOIN warehouses AS wh ON tf.out_warehouse_id = wh.id
        WHERE gd.amount IS NOT NULL
        AND de.date >= :mstart AND de.date < :mnext
        ;
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
        ROUND(we.amount * gd.amount / NULLIF(SUM(gd.amount) OVER (PARTITION BY we.registrar_id), 0), :precision) AS amount
    FROM warehouse_expenses AS we
    JOIN departments AS de ON de.id = we.department_id
    JOIN warehouses AS wh ON wh.department_id = de.id
    JOIN goods_location AS gl ON gl.sender_warehouse_id = wh.id
    JOIN goods AS gd ON gd.id = gl.goods_id
	JOIN transfers AS tf ON tf.id =  gl.registrar_id
    WHERE gl.goods_status = 2  -- отправление
      AND gd.amount IS NOT NULL  
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
        ROUND(ge.amount * gd.amount / NULLIF(SUM(gd.amount) OVER (PARTITION BY ge.registrar_id), 0), :precision) AS amount
    FROM general_expenses AS ge
    JOIN transfers AS tr
      ON tr.date >= :mstart AND tr.date < :mnext AND tr.type_transfer = 'Погрузка в машину'
    JOIN warehouses AS wh_out ON tr.out_warehouse_id = wh_out.id
    JOIN countries  AS cn_out ON wh_out.country_id = cn_out.id
    JOIN warehouses AS wh_in  ON tr.in_warehouse_id = wh_in.id
    JOIN countries  AS cn_in  ON wh_in.country_id  = cn_in.id
    JOIN goods_transfers AS gt ON gt.transfer_id = tr.id
    JOIN goods AS gd ON gd.id = gt.goods_id
    WHERE gd.amount IS NOT NULL
      AND cn_out.name = 'КИТАЙ'
      AND cn_in.name <> 'КИТАЙ'
	  AND ge.date >= :mstart AND ge.date < :mnext
    ;

"""


UPDATE_ALLOC_EXPENSES_SQL ="""
    WITH tmp_sum_amount AS (
        SELECT DISTINCT ON (tmp.type_expense, tmp.registrar_id, tmp.cost_category_id)
               tmp.ctid,
               tmp.type_expense,
               tmp.registrar_id,
               tmp.cost_category_id,
               tmp.goods_id,
               SUM(tmp.amount) OVER ( PARTITION BY tmp.type_expense, tmp.registrar_id, tmp.cost_category_id) AS sum_amount,
               t_de.total_amount
        FROM tmp_table AS tmp
        JOIN tmp_de_key_amount AS t_de
          ON t_de.registrar_id    = tmp.registrar_id
         AND t_de.cost_category_id = tmp.cost_category_id
        ORDER BY
            tmp.type_expense,
            tmp.registrar_id,
            tmp.cost_category_id,
            tmp.amount DESC,
            tmp.goods_id,
            tmp.ctid
    ),
       delta as (
        SELECT ctid, (total_amount - sum_amount) AS delta
        FROM tmp_sum_amount)     
    UPDATE tmp_table AS u
    SET amount = u.amount + t_s.delta
    FROM delta AS t_s
    WHERE u.ctid     = t_s.ctid ;
                           """

CREATE_VIEWS_SQL = """
-- v_part: ранжируем товары внутри ключа и считаем агрегаты
CREATE TEMP VIEW v_part AS
SELECT
    t.type_expense,
    t.registrar_id,
    t.cost_category_id,
    t.goods_id,
    t.amount,  -- уже округлено до PRECISION при формировании tmp_table
    ROW_NUMBER() OVER (
        PARTITION BY t.type_expense, t.registrar_id, t.cost_category_id
        ORDER BY t.amount DESC--, t.goods_id
    ) AS rn,
    COUNT(*) OVER (
        PARTITION BY t.type_expense, t.registrar_id, t.cost_category_id
    ) AS n,
    SUM(t.amount) OVER (
        PARTITION BY t.type_expense, t.registrar_id, t.cost_category_id
    ) AS sum_rounded
FROM tmp_table t;

-- v_agg: исходная (требуемая) сумма по ключу
CREATE TEMP VIEW v_agg AS
SELECT
    p.type_expense,
    p.registrar_id,
    p.cost_category_id,
    MAX(p.sum_rounded) AS sum_rounded,
    k.total_amount     AS total_amount
FROM v_part p
JOIN tmp_de_key_amount k
  ON k.registrar_id     = p.registrar_id
 AND k.cost_category_id = p.cost_category_id
GROUP BY p.type_expense, p.registrar_id, p.cost_category_id, k.total_amount;
"""

UPDATE_WITH_VIEWS_SQL = """
WITH
dist AS (
    SELECT
        p.type_expense,
        p.registrar_id,
        p.cost_category_id,
        p.goods_id,
        p.amount,
        p.rn,
        p.n,
        a.total_amount,
        a.sum_rounded,
        (a.total_amount - a.sum_rounded)::numeric AS err,  -- предполагаем err >= 0
        (:inc)::numeric AS inc
    FROM v_part p
    JOIN v_agg  a
      ON a.type_expense     = p.type_expense
     AND a.registrar_id     = p.registrar_id
     AND a.cost_category_id = p.cost_category_id
),
calc AS (
    SELECT
        d.*,
        FLOOR(ABS(d.err) / d.inc)::bigint AS k,  -- число «шагов» по inc
        GREATEST(ABS(d.err) - (FLOOR(ABS(d.err) / d.inc)::numeric * d.inc), 0)::numeric AS extra
        -- extra ∈ [0, inc)
    FROM dist d
),
incr AS (
    SELECT
        c.type_expense,
        c.registrar_id,
        c.cost_category_id,
        c.goods_id,
        (
          ((c.k / c.n) * c.inc) +                                     -- базовая равная раздача
          (CASE WHEN (c.k % c.n) >= c.rn THEN c.inc ELSE 0 END) +      -- «хвост» шагов первым (k % n) товарам
          (CASE WHEN c.rn = 1 THEN c.extra ELSE 0 END)                 -- дробный остаток целиком самому дорогому
        )::numeric AS delta
    FROM calc c
)
UPDATE tmp_table u
SET amount = (u.amount + i.delta)  -- только плюсуем
FROM incr i
WHERE u.type_expense     = i.type_expense
  AND u.registrar_id     = i.registrar_id
  AND u.cost_category_id = i.cost_category_id
  AND u.goods_id         = i.goods_id;
"""

DROP_VIEWS_SQL = """
DROP VIEW IF EXISTS v_agg;
DROP VIEW IF EXISTS v_part;
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


def create_temp_table_key(conn, table_name: str, mstart: date, mnext: date) -> None:
    create_sql = f"""
               CREATE TEMP TABLE tmp_de_key_amount ON COMMIT DROP AS
                SELECT DISTINCT ON (registrar_id, cost_category_id)
                registrar_id,
                cost_category_id,
                date  AS date,
                amount AS total_amount
                FROM {table_name}
                WHERE date >= '{mstart}' AND date < '{mnext}'
           """
    conn.exec_driver_sql(create_sql)


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

        replace_allocations_for_month(engine, "direct_expenses",    ALLOC_DIRECT_EXPENSES_SQL,    mstart, mnext)
        replace_allocations_for_month(engine, "warehouse_expenses", ALLOC_WAREHOUSE_EXPENSES_SQL, mstart, mnext)
        replace_allocations_for_month(engine, "general_expenses",   ALLOC_GENERAL_EXPENSES_SQL,   mstart, mnext)

        results.append(
            {
                "month": mstart.strftime("%Y-%m"),
                "from": mstart.isoformat(),
                "to_exclusive": mnext.isoformat(),
                "status": "ok",
            }
        )

    return results

