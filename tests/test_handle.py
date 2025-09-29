import json
from pathlib import Path

from sqlalchemy import text

from src.db.db import engine
from src.db.models import dev_drop_all_tables
from src.handlers.handel_message import handle_json
# tovary_random_sum.json
# "ПрямыеРасходы (2).json"
NAME_JSON = "Товары.json"  # укажи нужный файл в директории testData
FILE_PATH = Path(__file__).parent / "testData" / NAME_JSON


def main():
    with FILE_PATH.open(encoding="utf-8") as f:
        json_data = json.load(f)
    handle_json(json.dumps(json_data, ensure_ascii=False).encode("utf-8"))

def delete_temp_tables(engine) -> None:
    q = text("DROP TABLE IF EXISTS alembic_version")
    with engine.begin() as conn:
        conn.execute(q, {})

if __name__ == "__main__":
    dev_drop_all_tables(engine)
    delete_temp_tables(engine)
    # main()
