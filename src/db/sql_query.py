
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
            de.goods_doc_id,  
            ROUND(de.amount * gd.amount / NULLIF(SUM(gd.amount) OVER (PARTITION BY de.registrar_id, de.cost_category_id, de.goods_doc_id), 0), :precision) AS amount
        FROM direct_expenses AS de 
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
        NULL::uuid AS goods_doc_id, 
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
        NULL::uuid AS goods_doc_id, 
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

CREATE_VIEWS_SQL = """
-- v_part: ранжируем товары внутри ключа и считаем агрегаты
CREATE TEMP VIEW v_part AS
SELECT
    t.type_expense,
    t.registrar_id,
    t.cost_category_id,
    t.goods_doc_id,
    t.goods_id,
    t.amount,
    ROW_NUMBER() OVER (
        PARTITION BY t.type_expense, t.registrar_id, t.cost_category_id, t.goods_doc_id
        ORDER BY t.amount DESC
    ) AS rn,
    COUNT(*) OVER (
        PARTITION BY t.type_expense, t.registrar_id, t.cost_category_id, t.goods_doc_id
    ) AS n,
    SUM(t.amount) OVER (
        PARTITION BY t.type_expense, t.registrar_id, t.cost_category_id, t.goods_doc_id
    ) AS sum_rounded
FROM tmp_table t;

CREATE TEMP VIEW v_agg AS
SELECT
    p.type_expense,
    p.registrar_id,
    p.cost_category_id,
    p.goods_doc_id,
    MAX(p.sum_rounded) AS sum_rounded,
    k.total_amount     AS total_amount
FROM v_part p
JOIN tmp_de_key_amount k
  ON k.registrar_id     = p.registrar_id
 AND k.cost_category_id = p.cost_category_id
 AND ( (k.goods_doc_id IS NOT DISTINCT FROM p.goods_doc_id) )  
GROUP BY p.type_expense, p.registrar_id, p.cost_category_id, p.goods_doc_id, k.total_amount;
"""

UPDATE_WITH_VIEWS_SQL = """
WITH
dist AS (
    SELECT
        p.type_expense,
        p.registrar_id,
        p.cost_category_id,
        p.goods_doc_id,
        p.goods_id,
        p.amount,
        p.rn,
        p.n,
        a.total_amount,
        a.sum_rounded,
        (a.total_amount - a.sum_rounded)::numeric AS err,
        CASE WHEN (a.total_amount - a.sum_rounded) >= 0 THEN 1 ELSE -1 END AS sgn,
        (:inc)::numeric AS inc
    FROM v_part p
    JOIN v_agg  a
      ON a.type_expense    = p.type_expense
     AND a.registrar_id    = p.registrar_id
     AND a.cost_category_id= p.cost_category_id
     AND (a.goods_doc_id IS NOT DISTINCT FROM p.goods_doc_id) 
),
calc AS (
    SELECT
        d.*,
        FLOOR( (ABS(d.err))::numeric / d.inc )::bigint AS k,
        GREATEST(ABS(d.err) - (FLOOR( (ABS(d.err))::numeric / d.inc )::numeric * d.inc), 0)::numeric AS extra
    FROM dist d
),
incr AS (
    SELECT
        c.type_expense,
        c.registrar_id,
        c.cost_category_id,
        c.goods_doc_id,
        c.goods_id,
        (
          c.sgn * (
            ((c.k / c.n) * c.inc) +
            (CASE WHEN (c.k % c.n) >= c.rn THEN c.inc ELSE 0 END) +
            (CASE WHEN c.rn = 1 THEN c.extra ELSE 0 END)
          )
        )::numeric AS delta
    FROM calc c
)
UPDATE tmp_table u
SET amount = (u.amount + i.delta)
FROM incr i
WHERE u.type_expense     = i.type_expense
  AND u.registrar_id     = i.registrar_id
  AND u.cost_category_id = i.cost_category_id
  AND (u.goods_doc_id IS NOT DISTINCT FROM i.goods_doc_id) 
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