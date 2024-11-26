from core.config import settings
import logging
import sys

def setup_logging():
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create handlers
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # Create file handler
    file_handler = logging.FileHandler('app.log')
    file_handler.setFormatter(formatter)

    # Set log level based on DEBUG setting
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Set FastAPI logging
    logging.getLogger("fastapi").setLevel(log_level)
    logging.getLogger("uvicorn").setLevel(log_level)

    return root_logger 