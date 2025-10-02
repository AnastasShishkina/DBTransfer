import json
from pathlib import Path
from src.logger.logger import setup_logging
setup_logging()
from src.handlers.handel_message import handle_json
import logging
log = logging.getLogger("app")
FILES_PATH = Path(__file__).parent.parent / "data" # папка с json файлами


def firstLoadData(path):
    for file_path in path.glob("*.json"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                json_data = json.load(f)

            handle_json(json.dumps(json_data, ensure_ascii=False).encode("utf-8"))
            log.info("Файл успешно обработан: %s", file_path.name)
        except Exception as e:
            log.error("Ошибка в обработке файла : %s , %s ", file_path.name, e)



if __name__ == "__main__":
    firstLoadData(FILES_PATH)
