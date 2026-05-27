"""
Logging configuration for structured logging
Provides JSON-formatted logs for monitoring and debugging
"""
import logging
import sys
from pythonjsonlogger import jsonlogger
from datetime import datetime


def setup_logging(app):
    """Configure structured JSON logging for the application"""
    log_handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s',
        timestamp=True
    )
    log_handler.setFormatter(formatter)
    
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO if app.config['DEBUG'] else logging.WARNING,
        handlers=[log_handler]
    )
    
    # Configure Flask logger
    app.logger.handlers = [log_handler]
    app.logger.setLevel(logging.INFO if app.config['DEBUG'] else logging.WARNING)
    
    # Configure other loggers
    logging.getLogger('werkzeug').setLevel(logging.WARNING)

    return app.logger


class Logger:
    """Custom logger for application-specific logging"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def info(self, message: str, **kwargs):
        """Log info message with additional context"""
        log_data = {
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }
        self.logger.info(log_data)
    
    def error(self, message: str, **kwargs):
        """Log error message with additional context"""
        log_data = {
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }
        self.logger.error(log_data)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with additional context"""
        log_data = {
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }
        self.logger.warning(log_data)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with additional context"""
        log_data = {
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }
        self.logger.debug(log_data)
