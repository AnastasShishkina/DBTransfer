from pika import BlockingConnection

from src.config import settings
from src.handlers.handel_message import handle_json
from src.logger.logger import logger


def callback(ch_, method, properties, body):
    logger.debug("Обрабатываю сообщение")
    try:
        handle_json(body)
        ch_.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        # log.exception("Ошибка обработки: %s", e)
        logger.error("Ошибка обработки:", e)
        # с возвратом в очередь
        # ch_.basic_ack(delivery_tag=method.delivery_tag)
        ch_.basic_nack(delivery_tag=method.delivery_tag, requeue=True)


def start_consumer():
    with BlockingConnection(settings.RABBITMG_CONN_PARAMS) as connection, connection.channel() as channel:
        channel.queue_declare(queue=settings.RMQ_QUEUE, durable=True)
        channel.basic_consume(queue=settings.RMQ_QUEUE, on_message_callback=callback)

        logger.debug("Жду сообщений")
        channel.start_consuming()
