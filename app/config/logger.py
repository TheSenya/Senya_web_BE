import logging
import sys
from logging import Formatter, StreamHandler
from app.core.config import settings

class ColoredFormatter(Formatter):
    """Custom formatter adding color to log levels."""
    
    # ANSI color codes
    COLORS = {
        logging.DEBUG: '\033[94m',    # Blue
        logging.INFO: '\033[92m',     # Green
        logging.WARNING: '\033[93m',  # Yellow
        logging.ERROR: '\033[91m',    # Red
        logging.CRITICAL: '\033[91m'  # Red
    }
    RESET = '\033[0m'  # Reset color

    def format(self, record):
        # Store original level name
        original_levelname = record.levelname
        # Colorize the level name
        color = self.COLORS.get(record.levelno, self.RESET)
        record.levelname = f'{color}{original_levelname}{self.RESET}'
        # Format the message
        formatted = super().format(record)
        # Restore original level name to prevent side effects
        record.levelname = original_levelname
        return formatted

def setup_logger(name="app"):
    """Configure and return a logger with colored console output."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Console handler with colored output
    console_handler = StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    
    # Simplified format with colored level names
    formatter = ColoredFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    return logger

# Global logger instance
logger = setup_logger()