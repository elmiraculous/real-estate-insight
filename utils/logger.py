import logging
import os
from config import BASE_DIR

def setup_logger(name: str, log_file: str = "app.log", level=logging.INFO):
    log_path = os.path.join(BASE_DIR, "logs")
    os.makedirs(log_path, exist_ok=True)
    file_path = os.path.join(log_path, log_file)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        file_handler = logging.FileHandler(file_path)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
