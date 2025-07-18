"""
Generic response handler for processing WhatsApp responses.
Handles response parsing and data extraction.
"""

import asyncio
import json
from typing import Dict, Any, Optional, List
import logging
import requests


class ResponseHandler:
    """Generic response processing and handling."""
    
    def __init__(self, settings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
    
    async def get_latest_message(self) -> Optional[Dict[str, Any]]:
        """
        Get the latest message from the message API.
        
        Returns:
            Latest message data or None if failed
        """
        try:
            response = requests.get(
                self.settings.latest_message_endpoint,
                timeout=self.settings.timeout_seconds
            )
            
            if response.status_code == 200:
                message_data = response.json()
                self.logger.debug(f"Retrieved latest message: {message_data}")
                return message_data
            else:
                self.logger.warning(f"Failed to get latest message: {response.status_code}")
                return None
                
        except requests.RequestException as e:
            self.logger.error(f"Error getting latest message: {e}")
            return None
    
    def extract_media_response(self, message_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract processed data from media message response.
        
        Args:
            message_data: Message data from API
            
        Returns:
            Extracted data or None if not found
        """
        if not message_data or not isinstance(message_data, dict):
            return None
        
        extracted_data = None
        
        # Check interactive format
        interactive_data = message_data.get("interactive")
        if interactive_data and isinstance(interactive_data, dict):
            interactive_body = interactive_data.get("body", {})
            if interactive_body and isinstance(interactive_body, dict):
                extracted_data = interactive_body.get("text")
        
        # Check text format if no interactive data
        if not extracted_data:
            text_data = message_data.get("text")
            if text_data and isinstance(text_data, dict):
                text_body = text_data.get("body", "")
                if text_body and self._is_extracted_content(text_body):
                    extracted_data = text_body
        
        if extracted_data:
            return {
                'type': 'extracted_data',
                'content': extracted_data,
                'source': message_data
            }
        
        return None
    
    def _is_extracted_content(self, text: str) -> bool:
        """
        Check if text contains extracted content.
        
        Args:
            text: Text to check
            
        Returns:
            True if text appears to be extracted content
        """
        keywords = [
            "odometer", "reading", "miles", "km", "kilometers",
            "invoice", "receipt", "amount", "total", "date",
            "extracted", "details", "confirm", "transcription",
            "voice", "audio", "spoken", "said", "transcript"
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in keywords)
    
    def extract_text_message(self, message_data: Dict[str, Any]) -> Optional[str]:
        """
        Extract text content from message.
        
        Args:
            message_data: Message data
            
        Returns:
            Text content or None
        """
        if not message_data or not isinstance(message_data, dict):
            return None
        
        # Check text field
        text_data = message_data.get("text")
        if text_data and isinstance(text_data, dict):
            return text_data.get("body", "")
        
        # Check interactive text
        interactive_data = message_data.get("interactive")
        if interactive_data and isinstance(interactive_data, dict):
            interactive_body = interactive_data.get("body", {})
            if interactive_body and isinstance(interactive_body, dict):
                return interactive_body.get("text", "")
        
        return None
    
    def extract_location_data(self, message_data: Dict[str, Any]) -> Optional[Dict[str, float]]:
        """
        Extract location data from message.
        
        Args:
            message_data: Message data
            
        Returns:
            Location data with latitude/longitude or None
        """
        if not message_data or not isinstance(message_data, dict):
            return None
        
        location_data = message_data.get("location")
        if location_data and isinstance(location_data, dict):
            latitude = location_data.get("latitude")
            longitude = location_data.get("longitude")
            
            if latitude is not None and longitude is not None:
                return {
                    'latitude': float(latitude),
                    'longitude': float(longitude),
                    'name': location_data.get("name", ""),
                    'address': location_data.get("address", "")
                }
        
        return None
    
    def extract_media_info(self, message_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract media information from message.
        
        Args:
            message_data: Message data
            
        Returns:
            Media information or None
        """
        if not message_data or not isinstance(message_data, dict):
            return None
        
        media_info = {}
        
        # Check for image
        image_data = message_data.get("image")
        if image_data and isinstance(image_data, dict):
            media_info.update({
                'type': 'image',
                'id': image_data.get("id"),
                'mime_type': image_data.get("mime_type"),
                'sha256': image_data.get("sha256"),
                'caption': image_data.get("caption", "")
            })
        
        # Check for audio/voice
        audio_data = message_data.get("audio")
        if audio_data and isinstance(audio_data, dict):
            media_info.update({
                'type': 'audio',
                'id': audio_data.get("id"),
                'mime_type': audio_data.get("mime_type"),
                'sha256': audio_data.get("sha256"),
                'voice': audio_data.get("voice", False)
            })
        
        return media_info if media_info else None
    
    async def wait_for_response(self, timeout: int = 10) -> Optional[Dict[str, Any]]:
        """
        Wait for a response with timeout.
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            Response data or None if timeout
        """
        start_time = asyncio.get_event_loop().time()
        
        while (asyncio.get_event_loop().time() - start_time) < timeout:
            message = await self.get_latest_message()
            if message:
                return message
            
            await asyncio.sleep(1)  # Wait 1 second before checking again
        
        self.logger.warning(f"Response timeout after {timeout} seconds")
        return None
    
    def format_response_summary(self, message_data: Dict[str, Any]) -> str:
        """
        Format a summary of the response.
        
        Args:
            message_data: Message data
            
        Returns:
            Formatted summary string
        """
        if not message_data:
            return "No response"
        
        summary_parts = []
        
        # Add message type
        msg_type = message_data.get("type", "unknown")
        summary_parts.append(f"Type: {msg_type}")
        
        # Add content based on type
        if msg_type == "text":
            text_content = self.extract_text_message(message_data)
            if text_content:
                # Truncate long text
                if len(text_content) > 100:
                    text_content = text_content[:100] + "..."
                summary_parts.append(f"Text: {text_content}")
        
        elif msg_type == "location":
            location_data = self.extract_location_data(message_data)
            if location_data:
                summary_parts.append(f"Location: {location_data['latitude']}, {location_data['longitude']}")
        
        elif msg_type in ["image", "audio"]:
            media_info = self.extract_media_info(message_data)
            if media_info:
                summary_parts.append(f"Media ID: {media_info.get('id', 'unknown')}")
        
        # Add timestamp if available
        timestamp = message_data.get("timestamp")
        if timestamp:
            summary_parts.append(f"Time: {timestamp}")
        
        return " | ".join(summary_parts)
    
    async def process_flow_responses(self, responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process a list of flow responses.
        
        Args:
            responses: List of response data
            
        Returns:
            Processed response summary
        """
        summary = {
            'total_responses': len(responses),
            'successful_responses': 0,
            'failed_responses': 0,
            'extracted_data': [],
            'errors': []
        }
        
        for response in responses:
            try:
                if response and isinstance(response, dict):
                    summary['successful_responses'] += 1
                    
                    # Extract any processed data
                    extracted = self.extract_media_response(response)
                    if extracted:
                        summary['extracted_data'].append(extracted)
                else:
                    summary['failed_responses'] += 1
                    
            except Exception as e:
                summary['failed_responses'] += 1
                summary['errors'].append(str(e))
        
        return summary
