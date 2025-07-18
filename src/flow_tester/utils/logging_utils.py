"""
Logging configuration utilities.
Sets up logging for the application.
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional


def setup_logging(
    log_level: str = "INFO",
    log_format: Optional[str] = None,
    log_file: Optional[Path] = None,
    console_output: bool = True
) -> logging.Logger:
    """
    Set up logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_format: Log format string
        log_file: Optional log file path
        console_output: Whether to output to console
        
    Returns:
        Configured logger
    """
    # Set default format
    if log_format is None:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=[]
    )
    
    # Get root logger
    logger = logging.getLogger()
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Add console handler
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_formatter = logging.Formatter(log_format)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    # Add file handler if specified
    if log_file:
        # Create log directory if it doesn't exist
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Create rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_formatter = logging.Formatter(log_format)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name: Logger name
        level: Optional logging level
        
    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)
    
    if level:
        logger.setLevel(getattr(logging, level.upper()))
    
    return logger


def create_execution_logger(log_file: Path) -> logging.Logger:
    """
    Create a logger for execution logs.
    
    Args:
        log_file: Path to log file
        
    Returns:
        Execution logger
    """
    logger = logging.getLogger("execution")
    logger.setLevel(logging.INFO)
    
    # Create file handler
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(file_handler)
    
    return logger


def create_error_logger(log_file: Path) -> logging.Logger:
    """
    Create a logger for error logs.
    
    Args:
        log_file: Path to error log file
        
    Returns:
        Error logger
    """
    logger = logging.getLogger("errors")
    logger.setLevel(logging.ERROR)
    
    # Create file handler
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.ERROR)
    
    # Create formatter
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
    file_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(file_handler)
    
    return logger


def set_module_log_level(module_name: str, level: str):
    """
    Set log level for a specific module.
    
    Args:
        module_name: Name of the module
        level: Log level (DEBUG, INFO, WARNING, ERROR)
    """
    logger = logging.getLogger(module_name)
    logger.setLevel(getattr(logging, level.upper()))


def disable_module_logging(module_name: str):
    """
    Disable logging for a specific module.
    
    Args:
        module_name: Name of the module to disable
    """
    logger = logging.getLogger(module_name)
    logger.disabled = True


def enable_module_logging(module_name: str):
    """
    Enable logging for a specific module.
    
    Args:
        module_name: Name of the module to enable
    """
    logger = logging.getLogger(module_name)
    logger.disabled = False
