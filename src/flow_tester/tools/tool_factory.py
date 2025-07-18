"""
Generic tool factory for creating WhatsApp tools.
Factory pattern implementation for dynamic tool creation.
"""

from typing import Optional, Dict, Any
import logging

from flow_tester.tools.text_tool import SendTextTool
from flow_tester.tools.location_tool import SendLocationTool
from flow_tester.tools.image_tool import SendImageTool
from flow_tester.tools.voice_tool import SendVoiceTool


class ToolFactory:
    """Factory for creating WhatsApp tools."""
    
    def __init__(self, settings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        
        # Tool registry
        self._tools = {
            "send_text": SendTextTool,
            "send_location": SendLocationTool,
            "send_image": SendImageTool,
            "send_voice": SendVoiceTool,
        }
    
    def create_tool(self, tool_type: str) -> Optional[object]:
        """
        Create a tool instance by type.
        
        Args:
            tool_type: Type of tool to create
            
        Returns:
            Tool instance or None if invalid type
        """
        if tool_type not in self._tools:
            self.logger.error(f"Unknown tool type: {tool_type}")
            return None
        
        try:
            tool_class = self._tools[tool_type]
            return tool_class(self.settings)
        except Exception as e:
            self.logger.error(f"Failed to create tool {tool_type}: {e}")
            return None
    
    def get_available_tools(self) -> Dict[str, str]:
        """
        Get list of available tools.
        
        Returns:
            Dictionary of tool types and descriptions
        """
        return {
            "send_text": "Send text messages",
            "send_location": "Send location coordinates",
            "send_image": "Send image files",
            "send_voice": "Send voice recordings",
        }
    
    def validate_tool_parameters(self, tool_type: str, parameters: Dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Validate parameters for a specific tool.
        
        Args:
            tool_type: Type of tool
            parameters: Tool parameters
            
        Returns:
            Tuple of (is_valid, errors)
        """
        tool = self.create_tool(tool_type)
        if not tool:
            return False, [f"Invalid tool type: {tool_type}"]
        
        if not hasattr(tool, 'validate_parameters'):
            return True, []  # Tool doesn't have validation
        
        try:
            return tool.validate_parameters(parameters)
        except Exception as e:
            self.logger.error(f"Parameter validation failed for {tool_type}: {e}")
            return False, [f"Parameter validation error: {e}"]
    
    def register_tool(self, tool_type: str, tool_class: type):
        """
        Register a new tool type.
        
        Args:
            tool_type: Type identifier for the tool
            tool_class: Tool class to register
        """
        self._tools[tool_type] = tool_class
        self.logger.info(f"Registered new tool: {tool_type}")
    
    def unregister_tool(self, tool_type: str):
        """
        Unregister a tool type.
        
        Args:
            tool_type: Type identifier to unregister
        """
        if tool_type in self._tools:
            del self._tools[tool_type]
            self.logger.info(f"Unregistered tool: {tool_type}")
    
    def is_tool_available(self, tool_type: str) -> bool:
        """
        Check if a tool type is available.
        
        Args:
            tool_type: Tool type to check
            
        Returns:
            True if tool is available, False otherwise
        """
        return tool_type in self._tools
