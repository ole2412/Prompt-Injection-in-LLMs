import logging
import os


def init_logger(level=logging.DEBUG, log_file='./logs/chatbot.log', force_run=True):
    logger = logging.getLogger("ShieldyLogger")

    if force_run:
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
    else:
        if logger.hasHandlers():
            return

    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt='%d.%m.%Y %H:%M:%S')
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.setLevel(level)
    logger.propagate = False

if __name__ == "__main__":
    init_logger()
