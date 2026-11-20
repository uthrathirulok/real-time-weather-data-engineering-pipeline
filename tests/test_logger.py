
from logging.handlers import RotatingFileHandler

from src import logger as logger_module


def test_logger_creates_rotating_file_handler():
    logger = logger_module.get_logger()

    file_handlers = [
        handler
        for handler in logger.handlers
        if isinstance(handler, RotatingFileHandler)
    ]

    assert len(file_handlers) == 1

    file_handler = file_handlers[0]

    assert file_handler.maxBytes == 5 * 1024 * 1024
    assert file_handler.backupCount == 5
    assert file_handler.encoding == "utf-8"


def test_logger_has_console_handler():
    logger = logger_module.get_logger()

    console_handlers = [
        handler
        for handler in logger.handlers
        if type(handler).__name__ == "StreamHandler"
    ]

    assert len(console_handlers) == 1


def test_logger_does_not_add_duplicate_handlers():
    logger = logger_module.get_logger()

    initial_handler_count = len(logger.handlers)

    logger_module.get_logger()

    assert len(logger.handlers) == initial_handler_count


def test_logger_does_not_propagate_messages():
    logger = logger_module.get_logger()

    assert logger.propagate is False
