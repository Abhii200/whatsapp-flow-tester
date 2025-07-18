"""
Generic flow discovery logic.
Automatically discovers and loads flow configurations.
"""

import json
import asyncio
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

from flow_tester.config.flow_config import FlowConfig
from flow_tester.core.llm_analyzer import LLMAnalyzer


class FlowDiscovery:
    """Generic flow discovery and management."""
    
    def __init__(self, settings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        self.llm_analyzer = LLMAnalyzer(settings)
    
    async def discover_flows(self) -> List[Dict[str, Any]]:
        """
        Discover all available flows in the flows directory.
        
        Returns:
            List of flow information dictionaries
        """
        flows = []
        
        if not self.settings.flows_directory.exists():
            self.logger.warning(f"Flows directory not found: {self.settings.flows_directory}")
            return flows
        
        # Find all JSON files in flows directory
        json_files = list(self.settings.flows_directory.glob("*.json"))
        
        for json_file in json_files:
            try:
                flow_info = await self._analyze_flow_file(json_file)
                if flow_info:
                    flows.append(flow_info)
            except Exception as e:
                self.logger.error(f"Error analyzing flow file {json_file}: {e}")
                continue
        
        # Sort flows by name
        flows.sort(key=lambda x: x.get('name', ''))
        
        self.logger.info(f"Discovered {len(flows)} flows")
        return flows
    
    async def _analyze_flow_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Analyze a single flow file.
        
        Args:
            file_path: Path to flow JSON file
            
        Returns:
            Flow information dictionary or None if invalid
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                flow_data = json.load(f)
            
            # Create flow config for validation
            flow_config = FlowConfig.from_dict(flow_data)
            is_valid, errors = flow_config.validate()
            
            if not is_valid:
                self.logger.warning(f"Invalid flow configuration in {file_path}: {', '.join(errors)}")
                return None
            
            # Analyze user count
            user_count = await self.llm_analyzer.analyze_user_count(flow_data)
            
            # Get media requirements
            media_requirements = flow_config.get_media_requirements()
            
            # Check data source
            data_source = flow_config.get_employee_data_source()
            data_source_path = None
            if data_source:
                data_source_path = self.settings.base_path / data_source
                if not data_source_path.exists():
                    data_source_path = None
            
            # Default to main employee data if no specific source
            if not data_source_path:
                data_source_path = self.settings.default_employee_data
            
            flow_info = {
                'name': flow_config.trigger,
                'description': flow_config.description,
                'path': file_path,
                'user_count': user_count,
                'step_count': len(flow_config.flow_steps),
                'media_requirements': media_requirements,
                'data_source': str(data_source_path) if data_source_path else None,
                'data_source_exists': data_source_path.exists() if data_source_path else False,
                'config': flow_config
            }
            
            return flow_info
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in {file_path}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error analyzing {file_path}: {e}")
            return None
    
    async def load_flow_data(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Load flow data from file.
        
        Args:
            file_path: Path to flow JSON file
            
        Returns:
            Flow data dictionary or None if failed
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                flow_data = json.load(f)
            
            # Validate flow data
            flow_config = FlowConfig.from_dict(flow_data)
            is_valid, errors = flow_config.validate()
            
            if not is_valid:
                self.logger.error(f"Invalid flow data: {', '.join(errors)}")
                return None
            
            return flow_data
            
        except Exception as e:
            self.logger.error(f"Failed to load flow data from {file_path}: {e}")
            return None
    
    async def validate_flow_requirements(self, flow_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate flow requirements (data sources, media files, etc.).
        
        Args:
            flow_info: Flow information dictionary
            
        Returns:
            Validation results
        """
        validation_results = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check data source
        if flow_info.get('data_source'):
            data_source_path = Path(flow_info['data_source'])
            if not data_source_path.exists():
                validation_results['errors'].append(f"Data source not found: {data_source_path}")
                validation_results['valid'] = False
        
        # Check media requirements
        media_requirements = flow_info.get('media_requirements', {})
        
        for media_type, media_files in media_requirements.items():
            media_base_path = self.settings.get_media_path(media_type)
            
            for media_file in media_files:
                media_file_path = Path(media_file)
                
                # Check if it's an absolute path
                if media_file_path.is_absolute():
                    if not media_file_path.exists():
                        validation_results['warnings'].append(f"Media file not found: {media_file_path}")
                else:
                    # Check in media directory
                    full_media_path = media_base_path / media_file_path
                    if not full_media_path.exists():
                        validation_results['warnings'].append(f"Media file not found: {full_media_path}")
        
        return validation_results
    
    def get_flow_summary(self, flow_info: Dict[str, Any]) -> str:
        """
        Get a summary string for a flow.
        
        Args:
            flow_info: Flow information dictionary
            
        Returns:
            Summary string
        """
        summary_parts = []
        
        # Basic info
        summary_parts.append(f"📝 {flow_info['description']}")
        
        # User count
        user_count = flow_info.get('user_count', 1)
        if user_count > 1:
            summary_parts.append(f"👥 {user_count} users")
        else:
            summary_parts.append("👤 Single user")
        
        # Steps
        step_count = flow_info.get('step_count', 0)
        summary_parts.append(f"📋 {step_count} steps")
        
        # Data source
        if flow_info.get('data_source_exists'):
            summary_parts.append(f"📁 Data: {Path(flow_info['data_source']).name}")
        else:
            summary_parts.append("📁 Data: Default")
        
        # Media requirements
        media_requirements = flow_info.get('media_requirements', {})
        if media_requirements:
            media_types = list(media_requirements.keys())
            summary_parts.append(f"📎 Media: {', '.join(media_types)}")
        
        return "\n    ".join(summary_parts)
    
    async def create_flow_template(self, flow_name: str, flow_data: Dict[str, Any]) -> bool:
        """
        Create a new flow template file.
        
        Args:
            flow_name: Name of the flow
            flow_data: Flow configuration data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate flow data
            flow_config = FlowConfig.from_dict(flow_data)
            is_valid, errors = flow_config.validate()
            
            if not is_valid:
                self.logger.error(f"Invalid flow template: {', '.join(errors)}")
                return False
            
            # Create file path
            file_path = self.settings.flows_directory / f"{flow_name}.json"
            
            # Write flow data
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(flow_data, f, indent=2)
            
            self.logger.info(f"Created flow template: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create flow template: {e}")
            return False
