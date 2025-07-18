"""
Generic interactive selection menu system.
Provides user-friendly flow selection interface.
"""

import sys
from typing import Dict, List, Any, Optional
import logging


class InteractiveMenu:
    """Interactive menu system for flow selection."""
    
    def __init__(self, console=None):
        self.console = console
        self.logger = logging.getLogger(__name__)
    
    async def select_flow(self, flows: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Interactive flow selection menu.
        
        Args:
            flows: List of available flows
            
        Returns:
            Selected flow or None if cancelled
        """
        if not flows:
            self._print("No flows available for selection.")
            return None
        
        # Display header
        self._print_header("Available Flows")
        
        # Display flows
        for i, flow in enumerate(flows, 1):
            self._display_flow_option(i, flow)
        
        # Get user selection
        while True:
            try:
                choice = input(f"\nSelect flow (1-{len(flows)}, 'q' to quit): ").strip()
                
                if choice.lower() == 'q':
                    return None
                
                choice_num = int(choice)
                if 1 <= choice_num <= len(flows):
                    selected_flow = flows[choice_num - 1]
                    self._print_success(f"Selected: {selected_flow['name']}")
                    return selected_flow
                else:
                    self._print_error(f"Please enter a number between 1 and {len(flows)}")
                    
            except ValueError:
                self._print_error("Please enter a valid number or 'q' to quit")
            except KeyboardInterrupt:
                self._print("\nOperation cancelled.")
                return None
    
    def _display_flow_option(self, index: int, flow: Dict[str, Any]):
        """Display a single flow option."""
        name = flow.get('name', 'Unknown')
        description = flow.get('description', 'No description')
        user_count = flow.get('user_count', 1)
        step_count = flow.get('step_count', 0)
        
        # Basic info
        if self.console:
            self.console.print(f"\n[bold blue]{index}. {name}[/bold blue]")
            self.console.print(f"   [dim]{description}[/dim]")
            
            # Additional info
            info_parts = []
            if user_count > 1:
                info_parts.append(f"👥 {user_count} users")
            else:
                info_parts.append("👤 Single user")
            
            info_parts.append(f"📋 {step_count} steps")
            
            # Data source info
            if flow.get('data_source_exists'):
                data_source = flow.get('data_source', '')
                data_name = data_source.split('/')[-1] if data_source else 'Unknown'
                info_parts.append(f"📁 Data: {data_name}")
            else:
                info_parts.append("📁 Data: Default")
            
            # Media requirements
            media_requirements = flow.get('media_requirements', {})
            if media_requirements:
                media_types = list(media_requirements.keys())
                info_parts.append(f"📎 Media: {', '.join(media_types)}")
            
            self.console.print(f"   {' | '.join(info_parts)}")
        else:
            print(f"\n{index}. {name}")
            print(f"   {description}")
            
            # Additional info
            info_parts = []
            if user_count > 1:
                info_parts.append(f"Users: {user_count}")
            else:
                info_parts.append("Single user")
            
            info_parts.append(f"Steps: {step_count}")
            
            # Data source info
            if flow.get('data_source_exists'):
                data_source = flow.get('data_source', '')
                data_name = data_source.split('/')[-1] if data_source else 'Unknown'
                info_parts.append(f"Data: {data_name}")
            else:
                info_parts.append("Data: Default")
            
            # Media requirements
            media_requirements = flow.get('media_requirements', {})
            if media_requirements:
                media_types = list(media_requirements.keys())
                info_parts.append(f"Media: {', '.join(media_types)}")
            
            print(f"   {' | '.join(info_parts)}")
    
    def _print_header(self, title: str):
        """Print section header."""
        if self.console:
            self.console.print(f"\n[bold cyan]🚀 {title}[/bold cyan]")
            self.console.print("[dim]" + "=" * (len(title) + 4) + "[/dim]")
        else:
            print(f"\n🚀 {title}")
            print("=" * (len(title) + 4))
    
    def _print_success(self, message: str):
        """Print success message."""
        if self.console:
            self.console.print(f"[green]✅ {message}[/green]")
        else:
            print(f"✅ {message}")
    
    def _print_error(self, message: str):
        """Print error message."""
        if self.console:
            self.console.print(f"[red]❌ {message}[/red]")
        else:
            print(f"❌ {message}")
    
    def _print(self, message: str):
        """Print regular message."""
        if self.console:
            self.console.print(message)
        else:
            print(message)
    
    async def confirm_execution(self, flow_name: str, user_count: int) -> bool:
        """
        Confirm flow execution.
        
        Args:
            flow_name: Name of the flow
            user_count: Number of users
            
        Returns:
            True if confirmed, False otherwise
        """
        if self.console:
            self.console.print(f"\n[yellow]⚠️  About to execute flow: {flow_name}[/yellow]")
            self.console.print(f"[yellow]   Users: {user_count}[/yellow]")
        else:
            print(f"\n⚠️  About to execute flow: {flow_name}")
            print(f"   Users: {user_count}")
        
        try:
            confirm = input("Continue? (y/N): ").strip().lower()
            return confirm in ['y', 'yes']
        except KeyboardInterrupt:
            return False
    
    async def display_execution_progress(self, current: int, total: int, employee_name: str = ""):
        """
        Display execution progress.
        
        Args:
            current: Current execution number
            total: Total executions
            employee_name: Current employee name
        """
        if self.console:
            progress = f"[{current}/{total}]"
            if employee_name:
                self.console.print(f"[blue]📋 {progress} Executing for {employee_name}[/blue]")
            else:
                self.console.print(f"[blue]📋 {progress} Executing...[/blue]")
        else:
            progress = f"[{current}/{total}]"
            if employee_name:
                print(f"📋 {progress} Executing for {employee_name}")
            else:
                print(f"📋 {progress} Executing...")
    
    async def display_results_summary(self, results: List[Dict[str, Any]]):
        """
        Display execution results summary.
        
        Args:
            results: List of execution results
        """
        if not results:
            self._print("No results to display.")
            return
        
        successful = sum(1 for r in results if r.get('success', False))
        total = len(results)
        success_rate = (successful / total) * 100 if total > 0 else 0
        
        self._print_header("Execution Results")
        
        if self.console:
            self.console.print(f"[green]✅ Successful: {successful}/{total}[/green]")
            self.console.print(f"[blue]📊 Success Rate: {success_rate:.1f}%[/blue]")
            
            # Show failed executions
            failed_results = [r for r in results if not r.get('success', False)]
            if failed_results:
                self.console.print(f"\n[red]❌ Failed Executions ({len(failed_results)}):[/red]")
                for result in failed_results:
                    employee_name = result.get('employee', {}).get('Employee Name', 'Unknown')
                    error = result.get('error', 'Unknown error')
                    self.console.print(f"   [red]• {employee_name}: {error}[/red]")
        else:
            print(f"✅ Successful: {successful}/{total}")
            print(f"📊 Success Rate: {success_rate:.1f}%")
            
            # Show failed executions
            failed_results = [r for r in results if not r.get('success', False)]
            if failed_results:
                print(f"\n❌ Failed Executions ({len(failed_results)}):")
                for result in failed_results:
                    employee_name = result.get('employee', {}).get('Employee Name', 'Unknown')
                    error = result.get('error', 'Unknown error')
                    print(f"   • {employee_name}: {error}")
    
    async def show_flow_validation_results(self, flow_name: str, validation_results: Dict[str, Any]):
        """
        Show flow validation results.
        
        Args:
            flow_name: Name of the flow
            validation_results: Validation results
        """
        if validation_results.get('valid', True):
            self._print_success(f"Flow '{flow_name}' validation passed")
        else:
            self._print_error(f"Flow '{flow_name}' validation failed")
            
            errors = validation_results.get('errors', [])
            if errors:
                self._print("Errors:")
                for error in errors:
                    if self.console:
                        self.console.print(f"   [red]• {error}[/red]")
                    else:
                        print(f"   • {error}")
        
        warnings = validation_results.get('warnings', [])
        if warnings:
            self._print("Warnings:")
            for warning in warnings:
                if self.console:
                    self.console.print(f"   [yellow]• {warning}[/yellow]")
                else:
                    print(f"   • {warning}")
    
    async def display_configuration_status(self, settings):
        """
        Display configuration status.
        
        Args:
            settings: Settings object
        """
        self._print_header("Configuration Status")
        
        is_valid, errors = settings.validate_configuration()
        
        if is_valid:
            self._print_success("Configuration is valid")
        else:
            self._print_error("Configuration has issues:")
            for error in errors:
                if self.console:
                    self.console.print(f"   [red]• {error}[/red]")
                else:
                    print(f"   • {error}")
        
        # Show key paths
        if self.console:
            self.console.print(f"\n[dim]Flows Directory: {settings.flows_directory}[/dim]")
            self.console.print(f"[dim]Media Directory: {settings.media_directory}[/dim]")
            self.console.print(f"[dim]Results Directory: {settings.results_directory}[/dim]")
        else:
            print(f"\nFlows Directory: {settings.flows_directory}")
            print(f"Media Directory: {settings.media_directory}")
            print(f"Results Directory: {settings.results_directory}")
