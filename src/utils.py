import time
from functools import wraps
from itertools import islice
from datetime import datetime
from typing import Optional
from sqlalchemy import text


def timeit(func):
    """Декоратор: Время выполнения функции"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            dt = (time.perf_counter() - start) * 1000
            print(f"{func.__name__} заняла {dt:.2f} ms")

    return wrapper


def job_status(engine):
    """
    Декоратор: Сохраняет дату последнего запуска. Эта дата используется при вычислении инкремента.
    Перед запуском берёт last_success_at из etl_job_status по имени функции,
    после успешного выполнения обновляет last_success_at=now() (UPSERT).
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            job_name = fn.__name__
            with engine.begin() as conn:
                last_success_at: Optional[datetime] = conn.execute(
                    text("""
                        select last_success_at
                        from etl_job_status
                        where job_name = :job
                    """),
                    {"job": job_name},
                ).scalar()
            kwargs.setdefault("last_success_at", last_success_at)
            result = fn(*args, **kwargs)

            with engine.begin() as conn:
                conn.execute(
                    text("""
                        insert into etl_job_status (job_name, last_success_at)
                        values (:job, now())
                        on conflict (job_name) do update
                          set last_success_at = excluded.last_success_at
                    """),
                    {"job": job_name},
                )
            return result

        return wrapper

    return decorator


def _chunked(iterable, size):
    """Получение среза данных размера size"""
    it = iter(iterable)
    while True:
        chunk = list(islice(it, size))
        if not chunk:
            break
        yield chunk