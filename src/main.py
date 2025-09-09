from src.consumers.consumers import start_consumer
from src.db.db import engine
from src.db.models import create_all_tables, dev_drop_all_tables

# TODO: добавить логирование в едином формате со слоем логирования

if __name__ == "__main__":
    # setup_logging()
    print("test")
    dev_drop_all_tables(engine)
    create_all_tables(engine)

    print("test2")
    start_consumer()

    # from sqlalchemy import text
    # from sqlmodel import create_engine
    # from src.config import settings
    #
    # engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
    # with engine.connect() as conn:
    #     print(conn.execute(text("select version()")).scalar())
