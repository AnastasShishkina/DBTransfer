import logging
from src.config import settings

LOG_LEVEL = settings.LOG_LEVEL

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
)

logger = logging.getLogger("dbtransfer")