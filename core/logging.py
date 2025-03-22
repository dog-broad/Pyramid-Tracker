import sys
import logging
from typing import Optional
import structlog
from core.config import get_settings
from structlog.stdlib import LoggerFactory

def configure_logging(debug: bool = False, log_file: Optional[str] = None) -> None:
    """Configure structured logging and write to both console and a file"""
    level = logging.INFO
    if debug or get_settings().log.log_debug:
        level = logging.DEBUG
    
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.dev.ConsoleRenderer()
        ],
        context_class=dict,
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard logging for console output
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(handler)
    
    # Configure logging to file if log_file is provided
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        root_logger.addHandler(file_handler)
    
    # Prevent logging of mongodb to appear
    logging.getLogger("pymongo").setLevel(logging.WARNING)
    logging.getLogger("motor").setLevel(logging.WARNING)

def get_logger(name: Optional[str] = None) -> structlog.BoundLogger:
    """Get a structured logger"""
    return structlog.get_logger(name)
