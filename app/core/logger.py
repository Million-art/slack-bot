"""
Logging configuration for the Slack Data Manager Bot.
"""

import os
import logging
import logging.handlers
import json
from datetime import datetime
from typing import Dict, Any

def setup_logging():
    """
    Setup logging configuration for the application.
    """
    # Create logs directory if it doesn't exist
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Get log level from environment
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    log_file = os.getenv('LOG_FILE', 'logs/app.log')
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level))
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(getattr(logging, log_level))
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Error file handler
    error_handler = logging.handlers.RotatingFileHandler(
        'logs/error.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    error_handler.setFormatter(error_formatter)
    root_logger.addHandler(error_handler)
    
    # Audit log handler
    audit_handler = logging.handlers.RotatingFileHandler(
        'logs/audit.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=10
    )
    audit_handler.setLevel(logging.INFO)
    audit_formatter = logging.Formatter(
        '%(asctime)s - %(message)s'
    )
    audit_handler.setFormatter(audit_formatter)
    
    # Create audit logger
    audit_logger = logging.getLogger('audit')
    audit_logger.addHandler(audit_handler)
    audit_logger.setLevel(logging.INFO)
    audit_logger.propagate = False
    
    # Create performance logger
    perf_handler = logging.handlers.RotatingFileHandler(
        'logs/performance.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    perf_handler.setLevel(logging.INFO)
    perf_formatter = logging.Formatter(
        '%(asctime)s - %(message)s'
    )
    perf_handler.setFormatter(perf_formatter)
    
    perf_logger = logging.getLogger('performance')
    perf_logger.addHandler(perf_handler)
    perf_logger.setLevel(logging.INFO)
    perf_logger.propagate = False

def get_logger(name: str = None) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name (str, optional): Logger name
        
    Returns:
        logging.Logger: Logger instance
    """
    return logging.getLogger(name)

def log_audit_event(user_id: str, action: str, details: Dict[str, Any] = None):
    """
    Log an audit event.
    
    Args:
        user_id (str): User ID
        action (str): Action performed
        details (dict, optional): Additional details
    """
    audit_logger = logging.getLogger('audit')
    
    log_data = {
        'timestamp': datetime.utcnow().isoformat(),
        'user_id': user_id,
        'action': action,
        'ip_address': get_client_ip(),
        'user_agent': get_user_agent()
    }
    
    if details:
        log_data.update(details)
    
    audit_logger.info(json.dumps(log_data))

def log_performance_metric(operation: str, duration: float, details: Dict[str, Any] = None):
    """
    Log a performance metric.
    
    Args:
        operation (str): Operation name
        duration (float): Duration in seconds
        details (dict, optional): Additional details
    """
    perf_logger = logging.getLogger('performance')
    
    log_data = {
        'timestamp': datetime.utcnow().isoformat(),
        'operation': operation,
        'duration': duration,
        'duration_ms': duration * 1000
    }
    
    if details:
        log_data.update(details)
    
    perf_logger.info(json.dumps(log_data))

def log_error(error: Exception, context: Dict[str, Any] = None):
    """
    Log an error with context.
    
    Args:
        error (Exception): The error that occurred
        context (dict, optional): Additional context
    """
    logger = logging.getLogger(__name__)
    
    error_data = {
        'error_type': type(error).__name__,
        'error_message': str(error),
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if context:
        error_data.update(context)
    
    logger.error(f"ERROR: {json.dumps(error_data)}", exc_info=True)

def get_client_ip():
    """Get the client IP address."""
    # Check for forwarded headers
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    
    # Check for real IP header
    real_ip = request.headers.get('X-Real-IP')
    if real_ip:
        return real_ip
    
    # Fallback to remote address
    return request.remote_addr

def get_user_agent():
    """Get the user agent string."""
    return request.headers.get('User-Agent', 'Unknown')

# Import request after function definition to avoid circular imports
from flask import request 