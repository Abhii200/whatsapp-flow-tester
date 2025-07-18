"""
Flow-specific exceptions.
Custom exceptions for flow execution and management.
"""


class FlowException(Exception):
    """Base exception for flow-related errors."""
    pass


class FlowConfigurationError(FlowException):
    """Exception raised for flow configuration errors."""
    pass


class FlowExecutionError(FlowException):
    """Exception raised during flow execution."""
    pass


class FlowDiscoveryError(FlowException):
    """Exception raised during flow discovery."""
    pass


class FlowValidationError(FlowException):
    """Exception raised during flow validation."""
    pass


class FlowLoadError(FlowException):
    """Exception raised when loading flow data."""
    pass


class FlowTimeoutError(FlowException):
    """Exception raised when flow execution times out."""
    pass


class FlowDataError(FlowException):
    """Exception raised for flow data issues."""
    pass


class FlowStepError(FlowException):
    """Exception raised for individual flow step errors."""
    
    def __init__(self, message: str, step_index: int = None, step_description: str = None):
        super().__init__(message)
        self.step_index = step_index
        self.step_description = step_description


class ToolExecutionError(FlowException):
    """Exception raised during tool execution."""
    pass
