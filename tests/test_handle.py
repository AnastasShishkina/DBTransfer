import json
from pika import ConnectionParameters, BlockingConnection
from src.config import settings
from pathlib import Path
from src.handlers.handel_message import handle_json

NAME_JSON = "ПрямыеРасходы.json" #укажи нужнвй файл в директории testData
FILE_PATH = Path(__file__).parent / "testData" / NAME_JSON

def main():
    with FILE_PATH.open(encoding="utf-8") as f:
        json_data = json.load(f)
    handle_json(json.dumps(json_data, ensure_ascii=False).encode("utf-8"))


if __name__ == '__main__':
    main()