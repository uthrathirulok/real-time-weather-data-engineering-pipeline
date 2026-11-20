
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


# Find the main project directory
PROJECT_DIR = Path(__file__).resolve().parent.parent

# Create the logs directory if it doesn't exist
LOG_DIR = PROJECT_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Log file location
LOG_FILE = LOG_DIR / "pipeline.log"

# Log rotation settings
MAX_LOG_SIZE = 5 * 1024 * 1024  # 5 MB
BACKUP_COUNT = 5


def get_logger():
    """
    Configure and return the weather pipeline logger.
    """

    logger = logging.getLogger("weather_pipeline")
    logger.setLevel(logging.INFO)

    # Prevent duplicate logging handlers
    if not logger.handlers:

        # Log format
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s"
        )

        # Save logs to a rotating file
        file_handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=MAX_LOG_SIZE,
            backupCount=BACKUP_COUNT,
            encoding="utf-8"
        )

        file_handler.setFormatter(formatter)

        # Display logs in the terminal
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        # Avoid duplicate messages through the root logger
        logger.propagate = False

    return logger
