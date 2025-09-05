from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import func
from src.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

def get_session():
    return Session(engine)

def upsert_sqlmodel(model_cls, payload: dict, conflict_cols: list[str], exclude_update: set[str] = None, session: Session = None):
    exclude_update = exclude_update or set()
    table = model_cls.__table__
    stmt = insert(table).values(**payload)
    set_map = {c.name: getattr(stmt.excluded, c.name)
               for c in table.columns
               if not c.primary_key and c.name not in exclude_update}
    if "updated_at" in table.c:
        set_map["updated_at"] = func.now()

    stmt = stmt.on_conflict_do_update(
        index_elements=[table.c[name] for name in conflict_cols],
        set_=set_map
    )
    session.exec(stmt)