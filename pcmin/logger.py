from loguru import logger
from config import LOG_LEVEL, NAME, LOG_FILENAME

logger.add(LOG_FILENAME, rotation='32MB')