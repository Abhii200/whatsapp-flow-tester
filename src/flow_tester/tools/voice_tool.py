"""
Voice tool for sending WhatsApp voice messages.
Extracted from original notebook and enhanced.
"""

import os
import uuid
import time
import hashlib
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
import requests
import logging


class SendVoiceTool:
    """Tool for sending voice messages using FastAPI Media Upload."""
    
    def __init__(self, settings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
    
    def upload_to_fastapi_media(self, voice_path: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Upload voice file to FastAPI media server and get media ID.
        
        Args:
            voice_path: Path to voice file
            
        Returns:
            Tuple of (media_id, mime_type, sha256_hash)
        """
        try:
            # Determine MIME type
            file_ext = Path(voice_path).suffix.lower().lstrip('.')
            mime_type_map = {
                "wav": "audio/wav",
                "mp3": "audio/mpeg",
                "mp4": "audio/mp4",
                "ogg": "audio/ogg",
                "flac": "audio/flac",
                "m4a": "audio/mp4",
                "aac": "audio/aac",
                "opus": "audio/opus",
            }
            mime_type = mime_type_map.get(file_ext, "audio/wav")
            
            with open(voice_path, "rb") as f:
                file_content = f.read()
                files = {
                    "file": (os.path.basename(voice_path), file_content, mime_type)
                }
                
                self.logger.info(f"Uploading voice: {os.path.basename(voice_path)} ({len(file_content)} bytes)")
                
                response = requests.post(
                    self.settings.media_upload_endpoint,
                    files=files,
                    timeout=self.settings.timeout_seconds
                )
            
            if response.status_code == 200:
                result = response.json()
                full_media_id = result.get("id")  # e.g., "media_abc123"
                
                # Extract clean ID (remove "media_" prefix if present)
                if full_media_id and full_media_id.startswith("media_"):
                    clean_media_id = full_media_id.replace("media_", "")
                else:
                    clean_media_id = full_media_id
                
                self.logger.info(f"Voice upload successful! Media ID: {clean_media_id}")
                
                # Calculate SHA256
                sha256_hash = hashlib.sha256(file_content).hexdigest()
                
                return clean_media_id, mime_type, sha256_hash
            else:
                self.logger.error(f"Voice upload failed: {response.status_code} - {response.text}")
                return None, None, None
                
        except Exception as e:
            self.logger.error(f"Error uploading voice: {e}")
            return None, None, None
    
    def generate_payload(
        self,
        employee_phone: str,
        employee_name: str,
        media_id: str,
        mime_type: str,
        sha256: str,
        reply_to: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate WhatsApp voice message payload.
        
        Args:
            employee_phone: Employee phone number
            employee_name: Employee name
            media_id: Media ID
            mime_type: Audio MIME type
            sha256: Audio SHA256 hash
            reply_to: Message ID to reply to (optional)
            
        Returns:
            WhatsApp API payload
        """
        message = {
            "from": employee_phone,
            "id": f"wamid.HBgM{uuid.uuid4().hex.upper()}",
            "timestamp": int(time.time()),
            "type": "audio",
            "audio": {
                "id": media_id,
                "mime_type": mime_type,
                "sha256": sha256,
                "voice": True,  # Indicates this is a voice message
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
                self.logger.info(f"✅ Voice payload sent to webhook. Status: {webhook_response.status_code}")
            except requests.exceptions.ReadTimeout:
                # This is expected - webhook received but didn't respond in time
                self.logger.info(f"✅ Voice payload sent to webhook (timeout expected)")
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
        
        # Check voice path
        voice_path = parameters.get("voice_path")
        if not voice_path:
            errors.append("Voice path is required")
        elif not isinstance(voice_path, str):
            errors.append("Voice path must be a string")
        else:
            voice_file = Path(voice_path)
            if not voice_file.exists():
                errors.append(f"Voice file not found: {voice_path}")
            elif not voice_file.is_file():
                errors.append(f"Voice path is not a file: {voice_path}")
            else:
                # Check file extension
                valid_extensions = {'.wav', '.mp3', '.mp4', '.ogg', '.flac', '.m4a', '.aac', '.opus'}
                if voice_file.suffix.lower() not in valid_extensions:
                    errors.append(f"Unsupported audio format: {voice_file.suffix}")
                
                # Check file size (max 16MB for WhatsApp)
                try:
                    file_size = voice_file.stat().st_size
                    if file_size > 16 * 1024 * 1024:  # 16MB
                        errors.append(f"Voice file too large: {file_size / (1024*1024):.1f}MB (max 16MB)")
                except OSError:
                    errors.append(f"Cannot access voice file: {voice_path}")
        
        return len(errors) == 0, errors
