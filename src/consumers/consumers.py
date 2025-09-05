import json, pika # logging,
from sqlmodel import Session
from src.config import settings
from src.db.db import engine, get_session
from src.db.registry import REGISTRY
from src.handlers.generic_list import load_list

# = logging.getLogger(__name__)

def handle_message(body: bytes):
    payload = json.loads(body)
    assert isinstance(payload, list), "Ожидался массив блоков"
    with Session(engine) as session:
        for block in payload:
            meta = block["НаименованиеМетоданных"]
            data = block["Данные"]
            if meta not in REGISTRY:
                log.warning("Нет регистра для %s, пропускаю", meta)
                continue
            cfg = REGISTRY[meta]
            load_list(meta, data, cfg["model"], cfg["pk"], session)
        session.commit()

def start_consumer():
    conn = pika.BlockingConnection(pika.URLParameters(settings.amqp_url))
    ch = conn.channel()
    ch.queue_declare(queue=settings.amqp_queue, durable=True)

    def callback(ch_, method, properties, body):
        try:
            handle_message(body)
            ch_.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            log.exception("Ошибка обработки: %s", e)
            # можно basic_nack(requeue=false) и писать в DLQ
            ch_.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    ch.basic_qos(prefetch_count=10)
    ch.basic_consume(queue=settings.amqp_queue, on_message_callback=callback)
    log.info("Rabbit consumer started on %s", settings.amqp_queue)
    ch.start_consuming()
