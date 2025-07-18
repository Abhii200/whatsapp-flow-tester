"""
LLM analyzer for parsing flow steps.
Uses OpenAI GPT to analyze and categorize flow steps.
"""

import json
import re
from typing import Dict, Any, Optional
import logging

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


class LLMAnalyzer:
    """LLM-powered flow step analyzer."""
    
    def __init__(self, settings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        
        if OpenAI and self.settings.openai_api_key:
            self.client = OpenAI(api_key=self.settings.openai_api_key)
        else:
            self.client = None
            self.logger.warning("OpenAI client not available. Using fallback analysis.")
    
    async def analyze_step(self, step: str, employee_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze flow step and determine tool and parameters.
        
        Args:
            step: Step description
            employee_data: Employee data for context
            
        Returns:
            Dictionary with tool and parameters
        """
        if self.client:
            return await self._analyze_with_llm(step, employee_data)
        else:
            return self._analyze_with_fallback(step)
    
    async def _analyze_with_llm(self, step: str, employee_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analyze step using LLM."""
        try:
            # Add employee context if provided
            context_info = ""
            if employee_data:
                employee_name = employee_data.get("Employee Name", "User")
                context_info = f"\nEmployee Name: {employee_name}"
            
            prompt = f"""
            Analyze this WhatsApp flow step and determine the tool and parameters:
            
            Step: {step}{context_info}
            
            IMPORTANT RULES:
            - For text messages, extract ONLY the actual message text in quotes
            - For voice messages, look for audio file paths or voice indicators
            - Do NOT add employee names to message body unless specifically asked
            - Keep messages simple and direct
            
            Return JSON format:
            {{
                "tool": "send_text" | "send_location" | "send_image" | "send_voice",
                "parameters": {{
                    "body": "exact text from quotes only" (for send_text),
                    "latitude": number, "longitude": number (for send_location),
                    "caption": "image description", "image_path": "path/to/image" (for send_image),
                    "voice_path": "path to voice file" (for send_voice)
                }}
            }}
            
            Examples:
            - "User sends message 'Hello'" -> {{"tool": "send_text", "parameters": {{"body": "Hello"}}}}
            - "User sends voice message 'voice.wav'" -> {{"tool": "send_voice", "parameters": {{"voice_path": "voice.wav"}}}}
            - "User sends location" -> {{"tool": "send_location", "parameters": {{"latitude": 16.5423, "longitude": 81.4969}}}}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a WhatsApp flow analyzer. Return only valid JSON. Support text, location, image, and voice tools."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
            )
            
            raw_content = response.choices[0].message.content.strip()
            
            # Clean JSON content
            if raw_content.startswith("```") and raw_content.endswith("```"):
                raw_content = raw_content[raw_content.find("{"):raw_content.rfind("}") + 1]
            
            tool_info = json.loads(raw_content)
            
            # Extract file paths for media tools
            if tool_info["tool"] == "send_image":
                match = re.search(r"'([^']*\.(jpg|jpeg|png|gif|bmp|webp))'", step, re.IGNORECASE)
                if match:
                    tool_info["parameters"]["image_path"] = match.group(1)
            
            elif tool_info["tool"] == "send_voice":
                match = re.search(r"'([^']*\.(wav|mp3|mp4|ogg|flac|m4a|aac|opus))'", step, re.IGNORECASE)
                if match:
                    tool_info["parameters"]["voice_path"] = match.group(1)
            
            return tool_info
            
        except (json.JSONDecodeError, Exception) as e:
            self.logger.error(f"LLM analysis failed: {e}")
            return self._analyze_with_fallback(step)
    
    def _analyze_with_fallback(self, step: str) -> Dict[str, Any]:
        """Fallback analysis without LLM."""
        step_lower = step.lower()
        
        # Location detection
        if "latitude" in step_lower and "longitude" in step_lower:
            # Extract coordinates
            lat_match = re.search(r"latitude[:\s]+([0-9.-]+)", step_lower)
            lon_match = re.search(r"longitude[:\s]+([0-9.-]+)", step_lower)
            
            latitude = float(lat_match.group(1)) if lat_match else 16.542298847112292
            longitude = float(lon_match.group(1)) if lon_match else 81.4968731867673
            
            return {
                "tool": "send_location",
                "parameters": {
                    "latitude": latitude,
                    "longitude": longitude
                }
            }
        
        # Image detection
        elif any(keyword in step_lower for keyword in ['image', 'photo', 'picture', 'upload']):
            # Extract image path
            image_match = re.search(r"'([^']*\.(jpg|jpeg|png|gif|bmp|webp))'", step, re.IGNORECASE)
            image_path = image_match.group(1) if image_match else ""
            
            return {
                "tool": "send_image",
                "parameters": {
                    "image_path": image_path,
                    "caption": "Image"
                }
            }
        
        # Voice detection
        elif any(keyword in step_lower for keyword in ['voice', 'audio', 'recording']):
            # Extract voice path
            voice_match = re.search(r"'([^']*\.(wav|mp3|mp4|ogg|flac|m4a|aac|opus))'", step, re.IGNORECASE)
            voice_path = voice_match.group(1) if voice_match else ""
            
            return {
                "tool": "send_voice",
                "parameters": {
                    "voice_path": voice_path
                }
            }
        
        # Text message detection
        elif "message" in step_lower:
            # Extract message text
            message_match = re.search(r"'([^']*)'", step)
            message_text = message_match.group(1) if message_match else "test message"
            
            return {
                "tool": "send_text",
                "parameters": {
                    "body": message_text
                }
            }
        
        # Default fallback
        else:
            return {
                "tool": "unknown",
                "parameters": {}
            }
    
    async def analyze_user_count(self, flow_data: Dict[str, Any]) -> int:
        """
        Analyze flow description to determine user count.
        
        Args:
            flow_data: Flow configuration data
            
        Returns:
            Number of users/employees
        """
        if not self.client:
            return self._extract_user_count_fallback(flow_data)
        
        try:
            description = flow_data.get("description", "")
            flow_steps = flow_data.get("flow_steps", [])
            
            flow_content = f"Description: {description}\nSteps: {' '.join(flow_steps)}"
            
            prompt = f"""
            Analyze this WhatsApp flow and extract the number of users/employees:
            
            {flow_content}
            
            RULES:
            - Look for numbers like "20 users", "10 employees", "50 people", "100 workers"
            - If no specific number found, return 1
            - Return ONLY the number, nothing else
            
            Examples:
            - "Expense flow for 20 users" → 20
            - "10 employees send receipts" → 10
            - "Single user odometer reading" → 1
            - "No user count mentioned" → 1
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "Extract user count from flow description. Return only number."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=5,
            )
            
            user_count = int(response.choices[0].message.content.strip())
            return max(1, user_count)
            
        except Exception as e:
            self.logger.error(f"User count analysis failed: {e}")
            return self._extract_user_count_fallback(flow_data)
    
    def _extract_user_count_fallback(self, flow_data: Dict[str, Any]) -> int:
        """Fallback user count extraction."""
        description = flow_data.get("description", "").lower()
        
        # Look for numbers in description
        import re
        number_patterns = [
            r"(\d+)\s+users?",
            r"(\d+)\s+employees?",
            r"(\d+)\s+people",
            r"(\d+)\s+workers?",
            r"for\s+(\d+)",
        ]
        
        for pattern in number_patterns:
            match = re.search(pattern, description)
            if match:
                return int(match.group(1))
        
        # Check if explicitly mentioned as single user
        if any(keyword in description for keyword in ['single', 'one', 'individual']):
            return 1
        
        # Default to 1 if no specific count found
        return 1
