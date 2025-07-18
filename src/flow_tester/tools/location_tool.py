"""
Location tool for sending WhatsApp location messages.
Extracted from original notebook and enhanced.
"""

import uuid
import time
from typing import Dict, Any, Optional
import requests
import logging


class SendLocationTool:
    """Tool for sending location messages."""
    
    def __init__(self, settings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
    
    def generate_payload(
        self,
        employee_phone: str,
        employee_name: str,
        latitude: float,
        longitude: float,
        reply_to: Optional[str] = None,
        timestamp: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Generate WhatsApp location message payload.
        
        Args:
            employee_phone: Employee phone number
            employee_name: Employee name
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            reply_to: Message ID to reply to (optional)
            timestamp: Message timestamp (optional)
            
        Returns:
            WhatsApp API payload
        """
        message = {
            "from": employee_phone,
            "id": f"wamid.HBgM{uuid.uuid4().hex.upper()}",
            "timestamp": timestamp or int(time.time()),
            "type": "location",
            "location": {
                "latitude": latitude,
                "longitude": longitude,
                "name": "",
                "address": "",
            },
        }
        
        # Add context if replying to a message
        if reply_to:
            message["context"] = {"id": reply_to}
        
        payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": str(uuid.uuid4()),
                    "changes": [
                        {
                            "field": "messages",
                            "value": {
                                "messaging_product": "whatsapp",
                                "metadata": {
                                    "display_phone_number": employee_phone,
                                    "phone_number_id": self.settings.whatsapp_phone_number_id,
                                },
                                "contacts": [
                                    {
                                        "profile": {"name": employee_name},
                                        "wa_id": employee_phone,
                                    }
                                ],
                                "messages": [message],
                            },
                        }
                    ],
                }
            ],
        }
        
        return payload
    
    def send(self, payload: Dict[str, Any]) -> requests.Response:
        """
        Send payload to webhook and fetch latest message.
        
        Args:
            payload: WhatsApp API payload
            
        Returns:
            HTTP response from latest_message endpoint
        """
        try:
            # Step 1: Send to webhook (port 3000) - fire and forget
            try:
                webhook_response = requests.post(
                    self.settings.webhook_endpoint,
                    json=payload,
                    timeout=2  # Very short timeout
                )
                self.logger.info(f"✅ Location payload sent to webhook. Status: {webhook_response.status_code}")
            except requests.exceptions.ReadTimeout:
                # This is expected - webhook received but didn't respond in time
                self.logger.info(f"✅ Location payload sent to webhook (timeout expected)")
            except requests.RequestException as e:
                self.logger.warning(f"⚠️ Webhook send issue: {e}")
            
            # Step 2: Wait for processing
            time.sleep(3)
            
            # Step 3: Fetch latest message from port 8000
            latest_response = requests.get(
                self.settings.latest_message_endpoint,
                timeout=10
            )
            
            self.logger.info(f"📥 Latest message response: {latest_response.text}")
            print(f"📥 Latest message response: {latest_response.text}")
            
            return latest_response
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch latest message: {e}")
            # Return a dummy response to continue flow
            from requests import Response
            dummy_response = Response()
            dummy_response.status_code = 200
            return dummy_response
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Validate tool parameters.
        
        Args:
            parameters: Tool parameters
            
        Returns:
            Tuple of (is_valid, errors)
        """
        errors = []
        
        # Check latitude
        latitude = parameters.get("latitude")
        if latitude is None:
            errors.append("Latitude is required")
        elif not isinstance(latitude, (int, float)):
            errors.append("Latitude must be a number")
        elif not (-90 <= latitude <= 90):
            errors.append("Latitude must be between -90 and 90")
        
        # Check longitude
        longitude = parameters.get("longitude")
        if longitude is None:
            errors.append("Longitude is required")
        elif not isinstance(longitude, (int, float)):
            errors.append("Longitude must be a number")
        elif not (-180 <= longitude <= 180):
            errors.append("Longitude must be between -180 and 180")
        
        return len(errors) == 0, errors
