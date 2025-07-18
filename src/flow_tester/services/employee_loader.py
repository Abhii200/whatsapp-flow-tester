"""
Generic employee data loading service.
Supports CSV and Excel formats.
"""

import asyncio
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

try:
    import pandas as pd
except ImportError:
    pd = None

from flow_tester.core.llm_analyzer import LLMAnalyzer


class EmployeeLoader:
    """Generic employee data loader."""
    
    def __init__(self, settings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        self.llm_analyzer = LLMAnalyzer(settings)
    
    async def load_employees(self, flow_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Load employee data for flow execution."""
        if not pd:
            self.logger.error("pandas not available. Cannot load employee files.")
            return self._get_default_employees()
        
        # Determine user count
        user_count = await self.llm_analyzer.analyze_user_count(flow_data)
        
        # Determine data source
        data_source = self._get_data_source(flow_data)
        
        # Load employees from CSV or Excel
        employees = await self._load_from_excel(data_source, user_count)
        
        if not employees:
            self.logger.warning("No employees loaded from file, using default")
            employees = self._get_default_employees()
        
        return employees[:user_count]  # Limit to requested count
    
    def _get_data_source(self, flow_data: Dict[str, Any]) -> Path:
        """
        Determine data source path.
        
        Args:
            flow_data: Flow configuration data
            
        Returns:
            Path to data source
        """
        # Check if flow specifies a data source
        data_source = flow_data.get("data_source")
        if data_source:
            data_path = self.settings.base_path / data_source
            if data_path.exists():
                return data_path
        
        # Use default employee data
        return self.settings.default_employee_data
    
    async def _load_from_excel(self, file_path: Path, user_count: int) -> List[Dict[str, Any]]:
        """
        Load employees from Excel or CSV file.
        
        Args:
            file_path: Path to Excel or CSV file
            user_count: Number of employees to load
            
        Returns:
            List of employee data
        """
        try:
            if not file_path.exists():
                self.logger.error(f"Data file not found: {file_path}")
                return []
            
            # Load file based on extension
            if file_path.suffix.lower() == '.csv':
                df = pd.read_csv(file_path)
                self.logger.info(f"Loaded CSV file: {file_path} ({len(df)} rows)")
            else:
                df = pd.read_excel(file_path)
                self.logger.info(f"Loaded Excel file: {file_path} ({len(df)} rows)")
            
            employees = []
            
            # Process each row
            for i in range(min(user_count, len(df))):
                row = df.iloc[i]
                
                # Get phone number (try multiple column names)
                phone = self._extract_phone(row)
                if not phone:
                    self.logger.warning(f"Row {i+1}: No phone number found")
                    continue
                
                # Get employee name (try multiple column names)
                name = self._extract_name(row)
                if not name:
                    self.logger.warning(f"Row {i+1}: No name found")
                    name = f"Employee {i+1}"
                
                employees.append({
                    "Employee Phone": phone,
                    "Employee Name": name,
                    "raw_data": row.to_dict()  # Store original data
                })
            
            self.logger.info(f"Loaded {len(employees)} employees from Excel")
            return employees
            
        except Exception as e:
            self.logger.error(f"Error loading Excel file {file_path}: {e}")
            return []
    
    def _extract_phone(self, row: pd.Series) -> Optional[str]:
        """
        Extract phone number from Excel row.
        
        Args:
            row: Pandas Series representing a row
            
        Returns:
            Phone number string or None
        """
        # Try multiple column names
        phone_columns = [
            'Employee Phone', 'employee_phone', 'Phone', 'phone',
            'Mobile', 'mobile', 'PhoneNumber', 'phone_number',
            'Contact', 'contact', 'Number', 'number'
        ]
        
        for col in phone_columns:
            if col in row.index:
                phone = str(row[col]).strip()
                if phone and phone.lower() not in ['nan', 'none', '']:
                    return phone
        
        return None
    
    def _extract_name(self, row: pd.Series) -> Optional[str]:
        """
        Extract employee name from Excel row.
        
        Args:
            row: Pandas Series representing a row
            
        Returns:
            Employee name string or None
        """
        # Try multiple column names
        name_columns = [
            'Employee Name', 'employee_name', 'Name', 'name',
            'FullName', 'full_name', 'FirstName', 'first_name',
            'LastName', 'last_name', 'DisplayName', 'display_name'
        ]
        
        for col in name_columns:
            if col in row.index:
                name = str(row[col]).strip()
                if name and name.lower() not in ['nan', 'none', '']:
                    return name
        
        return None
    
    def _get_default_employees(self) -> List[Dict[str, Any]]:
        """
        Get default employee data as fallback.
        
        Returns:
            List of default employee data
        """
        return [
            {
                "Employee Phone": "919705184409",
                "Employee Name": "Nikhil",
                "raw_data": {}
            }
        ]
    
    async def validate_employee_data(self, employees: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate employee data.
        
        Args:
            employees: List of employee data
            
        Returns:
            Validation results
        """
        validation_results = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        if not employees:
            validation_results['errors'].append("No employee data provided")
            validation_results['valid'] = False
            return validation_results
        
        for i, employee in enumerate(employees):
            # Check required fields
            if not employee.get('Employee Phone'):
                validation_results['errors'].append(f"Employee {i+1}: Missing phone number")
                validation_results['valid'] = False
            
            if not employee.get('Employee Name'):
                validation_results['warnings'].append(f"Employee {i+1}: Missing name")
            
            # Validate phone number format
            phone = employee.get('Employee Phone', '')
            if phone and not self._is_valid_phone(phone):
                validation_results['warnings'].append(f"Employee {i+1}: Invalid phone format: {phone}")
        
        return validation_results
    
    def _is_valid_phone(self, phone: str) -> bool:
        """
        Basic phone number validation.
        
        Args:
            phone: Phone number string
            
        Returns:
            True if valid format, False otherwise
        """
        # Remove common separators
        clean_phone = phone.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '')
        
        # Check if it's all digits and reasonable length
        return clean_phone.isdigit() and 10 <= len(clean_phone) <= 15
    
    async def get_employee_count_from_file(self, file_path: Path) -> int:
        """
        Get employee count from Excel file.
        
        Args:
            file_path: Path to Excel file
            
        Returns:
            Number of employees in file
        """
        try:
            if not pd or not file_path.exists():
                return 0
            
            df = pd.read_excel(file_path)
            return len(df)
            
        except Exception as e:
            self.logger.error(f"Error counting employees in {file_path}: {e}")
            return 0
    
    async def create_employee_template(self, file_path: Path, sample_data: List[Dict[str, Any]]) -> bool:
        """
        Create an employee data template Excel file.
        
        Args:
            file_path: Path where to create the template
            sample_data: Sample employee data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not pd:
                self.logger.error("pandas not available. Cannot create Excel template.")
                return False
            
            # Create DataFrame from sample data
            df = pd.DataFrame(sample_data)
            
            # Save to Excel
            df.to_excel(file_path, index=False)
            
            self.logger.info(f"Created employee template: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating employee template: {e}")
            return False
