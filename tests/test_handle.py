import json
from pathlib import Path

from src.handlers.handel_message import handle_json
# tovary_random_sum.json
# "ПрямыеРасходы (2).json"
NAME_JSON = "Товары.json"  # укажи нужный файл в директории testData
FILE_PATH = Path(__file__).parent / "testData" / NAME_JSON


def main():
    with FILE_PATH.open(encoding="utf-8") as f:
        json_data = json.load(f)
    handle_json(json.dumps(json_data, ensure_ascii=False).encode("utf-8"))


if __name__ == "__main__":
    main()
