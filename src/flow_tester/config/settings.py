"""
Settings and configuration management.
Handles environment variables and default values.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


class Settings:
    """Application settings management."""
    
    def __init__(self):
        # Load environment variables
        self._load_env()
        
        # Base paths
        self.base_path = Path(__file__).parent.parent.parent.parent
        self.src_path = self.base_path / "src"
        
        # API Configuration
        self.whatsapp_access_token = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
        self.whatsapp_phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        
        # Server URLs
        self.nestjs_server_url = os.getenv("NESTJS_SERVER_URL", "http://localhost:3000")
        self.message_api_url = os.getenv("MESSAGE_API_URL", "http://localhost:8000")
        
        # Directory paths
        self.flows_directory = self.base_path / os.getenv("FLOWS_DIRECTORY", "flows")
        self.media_directory = self.base_path / os.getenv("MEDIA_DIRECTORY", "media")
        self.results_directory = self.base_path / os.getenv("RESULTS_DIRECTORY", "results")
        self.data_directory = self.base_path / "data"
        
        # Default employee data
        self.default_employee_data = self.data_directory / os.getenv("DEFAULT_EMPLOYEE_DATA", "employees.xlsx")
        
        # Execution settings
        self.execution_delay = int(os.getenv("EXECUTION_DELAY", "2"))
        self.max_retries = int(os.getenv("MAX_RETRIES", "3"))
        self.timeout_seconds = int(os.getenv("TIMEOUT_SECONDS", "30"))
        
        # Logging configuration
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.log_format = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        
        # API endpoints
        self.latest_message_endpoint = f"{self.message_api_url}/latest_message"
        self.media_upload_endpoint = f"{self.message_api_url}/media/upload"
        self.webhook_endpoint = f"{self.nestjs_server_url}/process-whatsapp-webhook"
        
        # Create directories if they don't exist
        self._create_directories()
    
    def _load_env(self):
        """Load environment variables from .env file."""
        env_path = Path(__file__).parent.parent.parent.parent / ".env"
        if env_path.exists():
            load_dotenv(env_path)
    
    def _create_directories(self):
        """Create necessary directories."""
        directories = [
            self.flows_directory,
            self.media_directory,
            self.results_directory,
            self.data_directory,
            self.results_directory / "logs",
            self.results_directory / "logs" / "execution_logs",
            self.results_directory / "logs" / "error_logs",
            self.results_directory / "reports",
            self.results_directory / "reports" / "flow_results",
            self.results_directory / "reports" / "analytics",
            self.media_directory / "temp",
            self.media_directory / "images",
            self.media_directory / "images" / "odometer",
            self.media_directory / "images" / "receipts",
            self.media_directory / "images" / "maintenance",
            self.media_directory / "audio",
            self.media_directory / "audio" / "voice_notes",
            self.media_directory / "audio" / "recordings",
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def validate_configuration(self) -> tuple[bool, list[str]]:
        """
        Validate configuration settings.
        
        Returns:
            tuple: (is_valid, list_of_errors)
        """
        errors = []
        
        # Required API keys
        if not self.whatsapp_access_token:
            errors.append("WHATSAPP_ACCESS_TOKEN is required")
        
        if not self.whatsapp_phone_number_id:
            errors.append("WHATSAPP_PHONE_NUMBER_ID is required")
        
        if not self.openai_api_key:
            errors.append("OPENAI_API_KEY is required")
        
        # Directory validation
        if not self.flows_directory.exists():
            errors.append(f"Flows directory not found: {self.flows_directory}")
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def get_media_path(self, media_type: str, subfolder: str = "") -> Path:
        """
        Get media path for specific type.
        
        Args:
            media_type: Type of media (images, audio)
            subfolder: Subfolder within media type
            
        Returns:
            Path to media directory
        """
        path = self.media_directory / media_type
        if subfolder:
            path = path / subfolder
        return path
    
    def get_log_file_path(self, log_type: str, filename: str) -> Path:
        """
        Get log file path.
        
        Args:
            log_type: Type of log (execution_logs, error_logs)
            filename: Log filename
            
        Returns:
            Path to log file
        """
        return self.results_directory / "logs" / log_type / filename
    
    def get_report_file_path(self, report_type: str, filename: str) -> Path:
        """
        Get report file path.
        
        Args:
            report_type: Type of report (flow_results, analytics)
            filename: Report filename
            
        Returns:
            Path to report file
        """
        return self.results_directory / "reports" / report_type / filename
    
    @property
    def is_configured(self) -> bool:
        """Check if basic configuration is complete."""
        return bool(
            self.whatsapp_access_token and
            self.whatsapp_phone_number_id and
            self.openai_api_key
        )
    
    def __str__(self) -> str:
        """String representation of settings."""
        return f"Settings(configured={self.is_configured}, flows_dir={self.flows_directory})"
