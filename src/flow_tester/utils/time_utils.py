"""
Time conversion utilities.
Handles time zone conversions and timestamp operations.
"""

import datetime
import time
from typing import Optional, Union, Dict
import logging

try:
    import pytz
except ImportError:
    pytz = None


class TimeUtils:
    """Time conversion and manipulation utilities."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.ist_timezone = None
        
        if pytz:
            self.ist_timezone = pytz.timezone("Asia/Kolkata")
    
    def convert_time_to_timestamp(self, time_str: str) -> int:
        """
        Convert time string (HH:MM:SS) to timestamp.
        
        Args:
            time_str: Time string in HH:MM:SS format
            
        Returns:
            Unix timestamp
        """
        try:
            time_parts = time_str.split(":")
            hour, minute, second = map(int, time_parts)
            
            if self.ist_timezone:
                now = datetime.datetime.now(self.ist_timezone)
                today = now.date()
                dt = self.ist_timezone.localize(
                    datetime.datetime.combine(today, datetime.time(hour, minute, second))
                )
                return int(dt.timestamp())
            else:
                # Fallback without timezone
                now = datetime.datetime.now()
                today = now.date()
                dt = datetime.datetime.combine(today, datetime.time(hour, minute, second))
                return int(dt.timestamp())
                
        except Exception as e:
            self.logger.error(f"Time conversion error: {e}")
            return int(time.time())
    
    def get_current_timestamp(self) -> int:
        """
        Get current timestamp.
        
        Returns:
            Current Unix timestamp
        """
        return int(time.time())
    
    def timestamp_to_datetime(self, timestamp: Union[int, float]) -> datetime.datetime:
        """
        Convert timestamp to datetime.
        
        Args:
            timestamp: Unix timestamp
            
        Returns:
            Datetime object
        """
        return datetime.datetime.fromtimestamp(timestamp)
    
    def format_timestamp(self, timestamp: Union[int, float], format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        """
        Format timestamp as string.
        
        Args:
            timestamp: Unix timestamp
            format_str: Format string
            
        Returns:
            Formatted timestamp string
        """
        dt = self.timestamp_to_datetime(timestamp)
        return dt.strftime(format_str)
    
    def get_ist_datetime(self) -> Optional[datetime.datetime]:
        """
        Get current IST datetime.
        
        Returns:
            IST datetime or None if pytz not available
        """
        if self.ist_timezone:
            return datetime.datetime.now(self.ist_timezone)
        return None
    
    def convert_to_ist(self, timestamp: Union[int, float]) -> Optional[datetime.datetime]:
        """
        Convert timestamp to IST datetime.
        
        Args:
            timestamp: Unix timestamp
            
        Returns:
            IST datetime or None if pytz not available
        """
        if self.ist_timezone:
            utc_dt = datetime.datetime.fromtimestamp(timestamp, tz=pytz.UTC)
            return utc_dt.astimezone(self.ist_timezone)
        return None
    
    def add_delay_to_timestamp(self, timestamp: Union[int, float], delay_seconds: int) -> int:
        """
        Add delay to timestamp.
        
        Args:
            timestamp: Original timestamp
            delay_seconds: Delay in seconds
            
        Returns:
            New timestamp with delay added
        """
        return int(timestamp + delay_seconds)
    
    def get_date_string(self, timestamp: Optional[Union[int, float]] = None) -> str:
        """
        Get date string for file naming.
        
        Args:
            timestamp: Optional timestamp, uses current time if None
            
        Returns:
            Date string in YYYY-MM-DD format
        """
        if timestamp is None:
            timestamp = self.get_current_timestamp()
        
        dt = self.timestamp_to_datetime(timestamp)
        return dt.strftime("%Y-%m-%d")
    
    def get_datetime_string(self, timestamp: Optional[Union[int, float]] = None) -> str:
        """
        Get datetime string for file naming.
        
        Args:
            timestamp: Optional timestamp, uses current time if None
            
        Returns:
            Datetime string in YYYY-MM-DD_HH-MM-SS format
        """
        if timestamp is None:
            timestamp = self.get_current_timestamp()
        
        dt = self.timestamp_to_datetime(timestamp)
        return dt.strftime("%Y-%m-%d_%H-%M-%S")
    
    def calculate_duration(self, start_timestamp: Union[int, float], end_timestamp: Union[int, float]) -> Dict[str, Union[int, float]]:
        """
        Calculate duration between two timestamps.
        
        Args:
            start_timestamp: Start timestamp
            end_timestamp: End timestamp
            
        Returns:
            Duration information
        """
        duration_seconds = end_timestamp - start_timestamp
        
        return {
            'seconds': duration_seconds,
            'minutes': duration_seconds / 60,
            'hours': duration_seconds / 3600,
            'formatted': self._format_duration(duration_seconds)
        }
    
    def _format_duration(self, seconds: float) -> str:
        """
        Format duration in human-readable format.
        
        Args:
            seconds: Duration in seconds
            
        Returns:
            Formatted duration string
        """
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"
