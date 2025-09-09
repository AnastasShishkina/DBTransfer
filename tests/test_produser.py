import json
from pathlib import Path

from pika import BlockingConnection

from src.config import settings

#Дополнительные справочники.json
# ПрямыеРасходы.json
NAME_JSON = "ПрямыеРасходы.json" #укажи нужнвй файл в директории testData
FILE_PATH = Path(__file__).parent / "testData" / NAME_JSON

def main():
    with FILE_PATH.open(encoding="utf-8") as f:
        json_data = json.load(f)

    with BlockingConnection(settings.RABBITMG_CONN_PARAMS) as connection:
        with connection.channel() as channel:
            channel.queue_declare(queue='test', durable=True)
            channel.basic_publish(
                exchange='',
                routing_key='test',
                body=json.dumps(json_data, ensure_ascii=False).encode("utf-8")
            )
            print("Sent %r" % (NAME_JSON))

if __name__ == '__main__':
    main()