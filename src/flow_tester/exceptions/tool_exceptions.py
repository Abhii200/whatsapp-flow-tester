"""
Tool-specific exceptions.
Custom exceptions for tool execution and management.
"""


class ToolException(Exception):
    """Base exception for tool-related errors."""
    pass


class ToolCreationError(ToolException):
    """Exception raised when creating tools."""
    pass


class ToolExecutionError(ToolException):
    """Exception raised during tool execution."""
    pass


class ToolValidationError(ToolException):
    """Exception raised during tool parameter validation."""
    pass


class ToolConfigurationError(ToolException):
    """Exception raised for tool configuration errors."""
    pass


class ToolNotFoundError(ToolException):
    """Exception raised when a tool is not found."""
    pass


class ToolTimeoutError(ToolException):
    """Exception raised when tool execution times out."""
    pass


class MediaUploadError(ToolException):
    """Exception raised during media upload."""
    pass


class MediaValidationError(ToolException):
    """Exception raised during media validation."""
    pass


class WebhookError(ToolException):
    """Exception raised during webhook communication."""
    pass


class APIError(ToolException):
    """Exception raised during API calls."""
    
    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data
