from loguru import logger
import sys

def setup_logger():
    # Удаляем все обработчики по умолчанию (чтобы избежать дублирования)
    logger.remove()

    # Настроим логирование в файл
    logger.add("sessions.log", level="DEBUG", format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")

    # Настроим вывод в консоль
    logger.add(sys.stdout, level="DEBUG", format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")

    return logger