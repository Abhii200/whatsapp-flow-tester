"""
Data validation utilities.
Provides validation functions for various data types.
"""

import re
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
import logging


class ValidationUtils:
    """Data validation utilities."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def validate_phone_number(self, phone: str) -> bool:
        """
        Validate phone number format.
        
        Args:
            phone: Phone number string
            
        Returns:
            True if valid, False otherwise
        """
        if not phone or not isinstance(phone, str):
            return False
        
        # Remove common separators
        clean_phone = re.sub(r'[+\-\s\(\)]', '', phone)
        
        # Check if it's all digits and reasonable length
        return clean_phone.isdigit() and 10 <= len(clean_phone) <= 15
    
    def validate_email(self, email: str) -> bool:
        """
        Validate email format.
        
        Args:
            email: Email string
            
        Returns:
            True if valid, False otherwise
        """
        if not email or not isinstance(email, str):
            return False
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_pattern, email) is not None
    
    def validate_url(self, url: str) -> bool:
        """
        Validate URL format.
        
        Args:
            url: URL string
            
        Returns:
            True if valid, False otherwise
        """
        if not url or not isinstance(url, str):
            return False
        
        url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        return re.match(url_pattern, url) is not None
    
    def validate_coordinates(self, latitude: Union[str, float], longitude: Union[str, float]) -> bool:
        """
        Validate latitude and longitude coordinates.
        
        Args:
            latitude: Latitude value
            longitude: Longitude value
            
        Returns:
            True if valid, False otherwise
        """
        try:
            lat = float(latitude)
            lon = float(longitude)
            
            return -90 <= lat <= 90 and -180 <= lon <= 180
            
        except (ValueError, TypeError):
            return False
    
    def validate_date_format(self, date_str: str, format_str: str = "%Y-%m-%d") -> bool:
        """
        Validate date string format.
        
        Args:
            date_str: Date string
            format_str: Expected format
            
        Returns:
            True if valid, False otherwise
        """
        try:
            import datetime
            datetime.datetime.strptime(date_str, format_str)
            return True
        except (ValueError, TypeError):
            return False
    
    def validate_file_path(self, file_path: Union[str, Path], must_exist: bool = True) -> bool:
        """
        Validate file path.
        
        Args:
            file_path: Path to file
            must_exist: Whether file must exist
            
        Returns:
            True if valid, False otherwise
        """
        try:
            path = Path(file_path)
            
            if must_exist:
                return path.exists() and path.is_file()
            else:
                return path.parent.exists() if path.parent != path else True
                
        except Exception:
            return False
    
    def validate_file_extension(self, file_path: Union[str, Path], allowed_extensions: List[str]) -> bool:
        """
        Validate file extension.
        
        Args:
            file_path: Path to file
            allowed_extensions: List of allowed extensions (without dots)
            
        Returns:
            True if valid, False otherwise
        """
        try:
            path = Path(file_path)
            file_ext = path.suffix.lower().lstrip('.')
            
            return file_ext in [ext.lower() for ext in allowed_extensions]
            
        except Exception:
            return False
    
    def validate_json_structure(self, data: Dict[str, Any], required_keys: List[str]) -> tuple[bool, List[str]]:
        """
        Validate JSON structure has required keys.
        
        Args:
            data: JSON data
            required_keys: List of required keys
            
        Returns:
            Tuple of (is_valid, missing_keys)
        """
        if not isinstance(data, dict):
            return False, required_keys
        
        missing_keys = [key for key in required_keys if key not in data]
        return len(missing_keys) == 0, missing_keys
    
    def validate_string_length(self, value: str, min_length: int = 0, max_length: int = None) -> bool:
        """
        Validate string length.
        
        Args:
            value: String value
            min_length: Minimum length
            max_length: Maximum length (optional)
            
        Returns:
            True if valid, False otherwise
        """
        if not isinstance(value, str):
            return False
        
        if len(value) < min_length:
            return False
        
        if max_length is not None and len(value) > max_length:
            return False
        
        return True
    
    def validate_numeric_range(self, value: Union[int, float, str], min_val: Union[int, float] = None, max_val: Union[int, float] = None) -> bool:
        """
        Validate numeric value is within range.
        
        Args:
            value: Numeric value
            min_val: Minimum value (optional)
            max_val: Maximum value (optional)
            
        Returns:
            True if valid, False otherwise
        """
        try:
            num_val = float(value)
            
            if min_val is not None and num_val < min_val:
                return False
            
            if max_val is not None and num_val > max_val:
                return False
            
            return True
            
        except (ValueError, TypeError):
            return False
    
    def validate_choice(self, value: Any, choices: List[Any]) -> bool:
        """
        Validate value is one of allowed choices.
        
        Args:
            value: Value to validate
            choices: List of allowed choices
            
        Returns:
            True if valid, False otherwise
        """
        return value in choices
    
    def validate_regex_pattern(self, value: str, pattern: str) -> bool:
        """
        Validate string matches regex pattern.
        
        Args:
            value: String value
            pattern: Regex pattern
            
        Returns:
            True if valid, False otherwise
        """
        try:
            return re.match(pattern, value) is not None
        except re.error:
            return False
    
    def validate_flow_step(self, step: str) -> tuple[bool, List[str]]:
        """
        Validate flow step format.
        
        Args:
            step: Flow step string
            
        Returns:
            Tuple of (is_valid, errors)
        """
        errors = []
        
        if not step or not isinstance(step, str):
            errors.append("Step must be a non-empty string")
            return False, errors
        
        step = step.strip()
        
        if len(step) < 10:
            errors.append("Step description too short")
        
        if len(step) > 500:
            errors.append("Step description too long")
        
        # Check for basic structure
        if not any(keyword in step.lower() for keyword in ['user', 'send', 'upload', 'message']):
            errors.append("Step should describe a user action")
        
        return len(errors) == 0, errors
    
    def validate_media_file(self, file_path: Union[str, Path], file_type: str) -> tuple[bool, List[str]]:
        """
        Validate media file.
        
        Args:
            file_path: Path to media file
            file_type: Type of media (image, audio, video)
            
        Returns:
            Tuple of (is_valid, errors)
        """
        errors = []
        
        if not self.validate_file_path(file_path, must_exist=True):
            errors.append(f"File not found: {file_path}")
            return False, errors
        
        # Define allowed extensions by type
        allowed_extensions = {
            'image': ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'],
            'audio': ['wav', 'mp3', 'mp4', 'ogg', 'flac', 'm4a', 'aac', 'opus'],
            'video': ['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm']
        }
        
        if file_type not in allowed_extensions:
            errors.append(f"Unsupported file type: {file_type}")
            return False, errors
        
        if not self.validate_file_extension(file_path, allowed_extensions[file_type]):
            errors.append(f"Invalid file extension for {file_type}")
        
        # Check file size (max 16MB for WhatsApp)
        try:
            file_size = Path(file_path).stat().st_size
            max_size = 16 * 1024 * 1024  # 16MB
            
            if file_size > max_size:
                errors.append(f"File too large: {file_size / (1024*1024):.1f}MB (max 16MB)")
        except Exception:
            errors.append("Cannot access file")
        
        return len(errors) == 0, errors
    
    def validate_employee_data(self, employee: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate employee data structure.
        
        Args:
            employee: Employee data dictionary
            
        Returns:
            Tuple of (is_valid, errors)
        """
        errors = []
        
        # Check required fields
        if not employee.get('Employee Phone'):
            errors.append("Employee phone number is required")
        elif not self.validate_phone_number(employee['Employee Phone']):
            errors.append("Invalid phone number format")
        
        if not employee.get('Employee Name'):
            errors.append("Employee name is required")
        elif not self.validate_string_length(employee['Employee Name'], min_length=2, max_length=100):
            errors.append("Employee name must be 2-100 characters")
        
        return len(errors) == 0, errors
