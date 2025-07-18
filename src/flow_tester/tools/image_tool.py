"""
Image tool for sending WhatsApp image messages.
Extracted from original notebook and enhanced.
"""

import os
import uuid
import time
import hashlib
import base64
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
import requests
import logging


class SendImageTool:
    """Tool for sending images using WhatsApp Media API v21.0."""
    
    def __init__(self, settings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
    
    def upload_to_whatsapp_media_api(
        self, 
        image_path: str, 
        phone_number_id: str, 
        access_token: str
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Upload image to WhatsApp Media API v21.0 and get media ID.
        
        Args:
            image_path: Path to image file
            phone_number_id: WhatsApp phone number ID
            access_token: WhatsApp access token
            
        Returns:
            Tuple of (media_id, mime_type, sha256_b64)
        """
        try:
            # WhatsApp Media Upload API v21.0
            url = f"https://graph.facebook.com/v21.0/{phone_number_id}/media"
            
            # Determine MIME type
            file_ext = Path(image_path).suffix.lower().lstrip('.')
            mime_type_map = {
                "jpg": "image/jpeg",
                "jpeg": "image/jpeg",
                "png": "image/png",
                "gif": "image/gif",
                "bmp": "image/bmp",
                "webp": "image/webp",
            }
            mime_type = mime_type_map.get(file_ext, "image/jpeg")
            
            with open(image_path, "rb") as f:
                files = {"file": (os.path.basename(image_path), f, mime_type)}
                data = {"type": mime_type, "messaging_product": "whatsapp"}
                headers = {"Authorization": f"Bearer {access_token}"}
                
                response = requests.post(
                    url, 
                    files=files, 
                    data=data, 
                    headers=headers,
                    timeout=self.settings.timeout_seconds
                )
            
            if response.status_code == 200:
                result = response.json()
                media_id = result.get("id")
                
                self.logger.info(f"Image upload successful! Media ID: {media_id}")
                
                # Calculate SHA256
                with open(image_path, "rb") as f:
                    file_content = f.read()
                sha256_b64 = base64.b64encode(
                    hashlib.sha256(file_content).digest()
                ).decode("utf-8")
                
                return media_id, mime_type, sha256_b64
            else:
                self.logger.error(f"WhatsApp upload failed: {response.status_code} - {response.text}")
                return None, None, None
                
        except Exception as e:
            self.logger.error(f"Error uploading to WhatsApp: {e}")
            return None, None, None
    
    def generate_payload(
        self,
        employee_phone: str,
        employee_name: str,
        media_id: str,
        mime_type: str,
        sha256: str,
        caption: str,
        reply_to: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate WhatsApp image message payload.
        
        Args:
            employee_phone: Employee phone number
            employee_name: Employee name
            media_id: WhatsApp media ID
            mime_type: Image MIME type
            sha256: Image SHA256 hash
            caption: Image caption
            reply_to: Message ID to reply to (optional)
            
        Returns:
            WhatsApp API payload
        """
        message = {
            "from": employee_phone,
            "id": f"wamid.HBgM{uuid.uuid4().hex.upper()}",
            "timestamp": int(time.time()),
            "type": "image",
            "image": {
                "id": media_id,
                "mime_type": mime_type,
                "sha256": sha256,
                "caption": caption,
            },
        }
        
        # Add context if replying to a message
        if reply_to:
            message["context"] = {"from": "917003235202", "id": reply_to}
            message["timestamp"] = str(int(time.time()))
        
        payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "476267595577986" if reply_to else str(uuid.uuid4()),
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
                self.logger.info(f"✅ Image payload sent to webhook. Status: {webhook_response.status_code}")
            except requests.exceptions.ReadTimeout:
                # This is expected - webhook received but didn't respond in time
                self.logger.info(f"✅ Image payload sent to webhook (timeout expected)")
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
        
        # Check image path
        image_path = parameters.get("image_path")
        if not image_path:
            errors.append("Image path is required")
        elif not isinstance(image_path, str):
            errors.append("Image path must be a string")
        else:
            image_file = Path(image_path)
            if not image_file.exists():
                errors.append(f"Image file not found: {image_path}")
            elif not image_file.is_file():
                errors.append(f"Image path is not a file: {image_path}")
            else:
                # Check file extension
                valid_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
                if image_file.suffix.lower() not in valid_extensions:
                    errors.append(f"Unsupported image format: {image_file.suffix}")
                
                # Check file size (max 16MB for WhatsApp)
                try:
                    file_size = image_file.stat().st_size
                    if file_size > 16 * 1024 * 1024:  # 16MB
                        errors.append(f"Image file too large: {file_size / (1024*1024):.1f}MB (max 16MB)")
                except OSError:
                    errors.append(f"Cannot access image file: {image_path}")
        
        # Check caption
        caption = parameters.get("caption", "")
        if isinstance(caption, str) and len(caption) > 1024:
            errors.append("Image caption too long (max 1024 characters)")
        
        return len(errors) == 0, errors
