"""
Flow configuration mapping and validation.
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
import json


class FlowConfig:
    """Flow configuration management."""
    
    def __init__(self, config_data: Dict[str, Any]):
        self.config_data = config_data
        self.trigger = config_data.get("trigger", "")
        self.description = config_data.get("description", "")
        self.flow_steps = config_data.get("flow_steps", [])
        self.data_source = config_data.get("data_source", "")
        self.media_paths = config_data.get("media_paths", [])
        self.validation_rules = config_data.get("validation_rules", {})
        self.success_criteria = config_data.get("success_criteria", {})
        self.user_count = config_data.get("user_count", 1)
        self.required_media = config_data.get("required_media", [])
        self.timeout_seconds = config_data.get("timeout_seconds", 30)
        self.retry_count = config_data.get("retry_count", 3)
    
    def validate(self) -> tuple[bool, List[str]]:
        """
        Validate flow configuration.
        
        Returns:
            tuple: (is_valid, list_of_errors)
        """
        errors = []
        
        # Required fields
        # 'trigger' is optional for API-generated flows
        
        if not self.description:
            errors.append("Flow description is required")
        
        if not self.flow_steps:
            errors.append("Flow steps are required")
        
        # Validate flow steps
        for i, step in enumerate(self.flow_steps):
            if not isinstance(step, str) or not step.strip():
                errors.append(f"Flow step {i+1} is invalid")
        
        # Validate media paths if specified
        for media_path in self.media_paths:
            if not isinstance(media_path, str):
                errors.append(f"Invalid media path: {media_path}")
        
        # Validate user count
        if not isinstance(self.user_count, int) or self.user_count < 1:
            errors.append("User count must be a positive integer")
        
        # Validate timeout
        if not isinstance(self.timeout_seconds, int) or self.timeout_seconds < 1:
            errors.append("Timeout must be a positive integer")
        
        # Validate retry count
        if not isinstance(self.retry_count, int) or self.retry_count < 0:
            errors.append("Retry count must be a non-negative integer")
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def get_media_requirements(self) -> Dict[str, List[str]]:
        """
        Get media requirements for this flow.
        
        Returns:
            Dict mapping media types to required paths
        """
        requirements = {}
        
        # Analyze flow steps for media requirements
        for step in self.flow_steps:
            step_lower = step.lower()
            
            # Image requirements
            if any(keyword in step_lower for keyword in ['image', 'photo', 'picture', 'upload']):
                if 'images' not in requirements:
                    requirements['images'] = []
                
                # Extract image paths from step
                import re
                image_pattern = r"'([^']*\.(jpg|jpeg|png|gif|bmp|webp))'"
                matches = re.findall(image_pattern, step, re.IGNORECASE)
                for match in matches:
                    requirements['images'].append(match[0])
            
            # Audio requirements
            if any(keyword in step_lower for keyword in ['voice', 'audio', 'recording']):
                if 'audio' not in requirements:
                    requirements['audio'] = []
                
                # Extract audio paths from step
                import re
                audio_pattern = r"'([^']*\.(wav|mp3|mp4|ogg|flac|m4a|aac|opus))'"
                matches = re.findall(audio_pattern, step, re.IGNORECASE)
                for match in matches:
                    requirements['audio'].append(match[0])
        
        return requirements
    
    def get_employee_data_source(self) -> Optional[str]:
        """
        Get employee data source path.
        
        Returns:
            Path to employee data file or None if not specified
        """
        return self.data_source if self.data_source else None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self.config_data
    
    @classmethod
    def from_file(cls, file_path: Path) -> 'FlowConfig':
        """
        Load flow configuration from file.
        
        Args:
            file_path: Path to configuration file
            
        Returns:
            FlowConfig instance
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        return cls(config_data)
    
    @classmethod
    def from_dict(cls, config_data: Dict[str, Any]) -> 'FlowConfig':
        """
        Create flow configuration from dictionary.
        
        Args:
            config_data: Configuration dictionary
            
        Returns:
            FlowConfig instance
        """
        return cls(config_data)
    
    def __str__(self) -> str:
        """String representation."""
        return f"FlowConfig(trigger={self.trigger}, steps={len(self.flow_steps)})"
    
    def __repr__(self) -> str:
        """String representation."""
        return self.__str__()
