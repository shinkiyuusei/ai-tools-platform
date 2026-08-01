"""
Logging configuration for structured logging
Provides JSON-formatted logs for monitoring and debugging
"""
import logging
import sys
from pythonjsonlogger import jsonlogger


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

