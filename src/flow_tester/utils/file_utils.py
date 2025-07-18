"""
File operation utilities.
Handles file I/O operations and path management.
"""

import os
import shutil
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import logging


class FileUtils:
    """File operation utilities."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def ensure_directory_exists(self, directory: Union[str, Path]) -> Path:
        """
        Ensure directory exists, create if it doesn't.
        
        Args:
            directory: Directory path
            
        Returns:
            Path object
        """
        dir_path = Path(directory)
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path
    
    def read_json_file(self, file_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
        """
        Read JSON file safely.
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            JSON data or None if failed
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error reading JSON file {file_path}: {e}")
            return None
    
    def write_json_file(self, file_path: Union[str, Path], data: Dict[str, Any], indent: int = 2) -> bool:
        """
        Write JSON file safely.
        
        Args:
            file_path: Path to JSON file
            data: Data to write
            indent: JSON indentation
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure directory exists
            self.ensure_directory_exists(Path(file_path).parent)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=indent, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error writing JSON file {file_path}: {e}")
            return False
    
    def copy_file(self, source: Union[str, Path], destination: Union[str, Path]) -> bool:
        """
        Copy file safely.
        
        Args:
            source: Source file path
            destination: Destination file path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            source_path = Path(source)
            dest_path = Path(destination)
            
            if not source_path.exists():
                self.logger.error(f"Source file does not exist: {source}")
                return False
            
            # Ensure destination directory exists
            self.ensure_directory_exists(dest_path.parent)
            
            shutil.copy2(source_path, dest_path)
            return True
            
        except Exception as e:
            self.logger.error(f"Error copying file from {source} to {destination}: {e}")
            return False
    
    def move_file(self, source: Union[str, Path], destination: Union[str, Path]) -> bool:
        """
        Move file safely.
        
        Args:
            source: Source file path
            destination: Destination file path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            source_path = Path(source)
            dest_path = Path(destination)
            
            if not source_path.exists():
                self.logger.error(f"Source file does not exist: {source}")
                return False
            
            # Ensure destination directory exists
            self.ensure_directory_exists(dest_path.parent)
            
            shutil.move(str(source_path), str(dest_path))
            return True
            
        except Exception as e:
            self.logger.error(f"Error moving file from {source} to {destination}: {e}")
            return False
    
    def delete_file(self, file_path: Union[str, Path]) -> bool:
        """
        Delete file safely.
        
        Args:
            file_path: Path to file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Error deleting file {file_path}: {e}")
            return False
    
    def get_file_size(self, file_path: Union[str, Path]) -> int:
        """
        Get file size in bytes.
        
        Args:
            file_path: Path to file
            
        Returns:
            File size in bytes, 0 if error
        """
        try:
            return Path(file_path).stat().st_size
        except Exception:
            return 0
    
    def get_file_extension(self, file_path: Union[str, Path]) -> str:
        """
        Get file extension.
        
        Args:
            file_path: Path to file
            
        Returns:
            File extension (without dot)
        """
        return Path(file_path).suffix.lower().lstrip('.')
    
    def is_file_type(self, file_path: Union[str, Path], extensions: List[str]) -> bool:
        """
        Check if file has one of the specified extensions.
        
        Args:
            file_path: Path to file
            extensions: List of extensions (without dots)
            
        Returns:
            True if file has one of the extensions
        """
        file_ext = self.get_file_extension(file_path)
        return file_ext in [ext.lower() for ext in extensions]
    
    def find_files_by_pattern(self, directory: Union[str, Path], pattern: str) -> List[Path]:
        """
        Find files matching a pattern.
        
        Args:
            directory: Directory to search
            pattern: Glob pattern
            
        Returns:
            List of matching file paths
        """
        try:
            dir_path = Path(directory)
            if not dir_path.exists():
                return []
            
            return list(dir_path.glob(pattern))
            
        except Exception as e:
            self.logger.error(f"Error finding files with pattern {pattern} in {directory}: {e}")
            return []
    
    def create_backup(self, file_path: Union[str, Path], backup_suffix: str = ".bak") -> bool:
        """
        Create a backup of a file.
        
        Args:
            file_path: Path to file
            backup_suffix: Backup file suffix
            
        Returns:
            True if successful, False otherwise
        """
        try:
            source_path = Path(file_path)
            if not source_path.exists():
                return False
            
            backup_path = source_path.with_suffix(source_path.suffix + backup_suffix)
            return self.copy_file(source_path, backup_path)
            
        except Exception as e:
            self.logger.error(f"Error creating backup of {file_path}: {e}")
            return False
    
    def cleanup_old_files(self, directory: Union[str, Path], max_age_days: int, pattern: str = "*") -> int:
        """
        Clean up old files in a directory.
        
        Args:
            directory: Directory to clean
            max_age_days: Maximum age in days
            pattern: File pattern to match
            
        Returns:
            Number of files deleted
        """
        try:
            import time
            
            dir_path = Path(directory)
            if not dir_path.exists():
                return 0
            
            current_time = time.time()
            max_age_seconds = max_age_days * 24 * 60 * 60
            deleted_count = 0
            
            for file_path in dir_path.glob(pattern):
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > max_age_seconds:
                        if self.delete_file(file_path):
                            deleted_count += 1
            
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old files in {directory}: {e}")
            return 0
    
    def get_directory_size(self, directory: Union[str, Path]) -> int:
        """
        Get total size of directory in bytes.
        
        Args:
            directory: Directory path
            
        Returns:
            Total size in bytes
        """
        try:
            dir_path = Path(directory)
            if not dir_path.exists():
                return 0
            
            total_size = 0
            for path in dir_path.rglob('*'):
                if path.is_file():
                    total_size += path.stat().st_size
            
            return total_size
            
        except Exception as e:
            self.logger.error(f"Error calculating directory size for {directory}: {e}")
            return 0
