import time
from functools import wraps
from datetime import date
from typing import Iterator


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


def first_day(dt: date) -> date:
    return date(dt.year, dt.month, 1)


def next_month(d: date) -> date:
    return date(d.year + (d.month == 12), (d.month % 12) + 1, 1)


def iter_months(mstart: date, mend: date) -> Iterator[tuple[date, date]]:
    cur = first_day(mstart)
    last = first_day(mend)
    while cur <= last:
        nxt = next_month(cur)
        yield cur, nxt
        cur = nxt
