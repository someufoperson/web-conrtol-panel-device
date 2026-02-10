from loguru import logger
import sys

def setup_logger():
    logger.remove()
    logger.add("sessions.log", level="DEBUG", format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")
    logger.add(sys.stdout, level="DEBUG", format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")
    return logger