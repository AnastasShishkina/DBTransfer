import json
from pathlib import Path

from src.db.db import engine
from src.handlers.handel_message import handle_json
from src.db.models import dev_drop_all_tables


FILES_PATH = Path(__file__).parent.parent / "data" # папка с json файлами


def firstLoadData(path):
    for file_path in path.glob("*.json"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                json_data = json.load(f)

            handle_json(json.dumps(json_data, ensure_ascii=False).encode("utf-8"))

            print(f"[OK] {file_path.name} обработан")
        except Exception as e:
            print(f"[ERR] {file_path.name}: {e}")


if __name__ == "__main__":
    #dev_drop_all_tables(engine)
    firstLoadData(FILES_PATH)
