#!/usr/bin/env python3
"""
Main entry point for WhatsApp Flow Tester.
Dynamic flow discovery and execution system.
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from flow_tester.config.settings import Settings
from flow_tester.core.flow_discovery import FlowDiscovery
from flow_tester.core.interactive_menu import InteractiveMenu
from flow_tester.core.flow_engine import FlowEngine
from flow_tester.services.employee_loader import EmployeeLoader
from flow_tester.utils.logging_utils import setup_logging

# Rich imports for beautiful output
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    from rich import print as rprint
    console = Console()
except ImportError:
    console = None
    rprint = print


class WhatsAppFlowTester:
    """Main application class for WhatsApp Flow Tester."""
    
    def __init__(self):
        self.settings = Settings()
        self.logger = setup_logging()
        self.flow_discovery = FlowDiscovery(self.settings)
        self.interactive_menu = InteractiveMenu(console)
        self.flow_engine = FlowEngine(self.settings)
        self.employee_loader = EmployeeLoader(self.settings)
        
    async def run(self):
        """Main application entry point."""
        try:
            # Display welcome message
            self._display_welcome()
            
            # Discover available flows
            flows = await self._discover_flows()
            if not flows:
                self._display_error("No flows found in the flows directory.")
                return
            
            # Interactive flow selection
            selected_flow = await self._select_flow(flows)
            if not selected_flow:
                self._display_info("No flow selected. Exiting.")
                return
            
            # Load and validate flow
            flow_data = await self._load_flow_data(selected_flow)
            if not flow_data:
                return
            
            # Load employees
            employees = await self._load_employees(flow_data)
            if not employees:
                return
            
            # Execute flow
            await self._execute_flow(flow_data, employees)
            
        except KeyboardInterrupt:
            self._display_info("\nOperation cancelled by user.")
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            self._display_error(f"Unexpected error: {e}")
    
    def _display_welcome(self):
        """Display welcome message."""
        if console:
            welcome_text = Text("🚀 WhatsApp Flow Tester", style="bold blue")
            welcome_panel = Panel(
                welcome_text,
                subtitle="Dynamic Flow Testing Framework",
                border_style="blue"
            )
            console.print(welcome_panel)
            console.print()
        else:
            print("🚀 WhatsApp Flow Tester")
            print("Dynamic Flow Testing Framework")
            print("=" * 50)
    
    def _display_error(self, message: str):
        """Display error message."""
        if console:
            console.print(f"❌ {message}", style="bold red")
        else:
            print(f"❌ {message}")
    
    def _display_info(self, message: str):
        """Display info message."""
        if console:
            console.print(f"ℹ️ {message}", style="blue")
        else:
            print(f"ℹ️ {message}")
    
    def _display_success(self, message: str):
        """Display success message."""
        if console:
            console.print(f"✅ {message}", style="green")
        else:
            print(f"✅ {message}")
    
    async def _discover_flows(self) -> List[Dict]:
        """Discover available flows."""
        try:
            flows = await self.flow_discovery.discover_flows()
            self._display_success(f"Discovered {len(flows)} flow(s)")
            return flows
        except Exception as e:
            self.logger.error(f"Flow discovery failed: {e}")
            self._display_error(f"Flow discovery failed: {e}")
            return []
    
    async def _select_flow(self, flows: List[Dict]) -> Optional[Dict]:
        """Interactive flow selection."""
        try:
            return await self.interactive_menu.select_flow(flows)
        except Exception as e:
            self.logger.error(f"Flow selection failed: {e}")
            self._display_error(f"Flow selection failed: {e}")
            return None
    
    async def _load_flow_data(self, flow_info: Dict) -> Optional[Dict]:
        """Load and validate flow data."""
        try:
            flow_data = await self.flow_discovery.load_flow_data(flow_info['path'])
            if not flow_data:
                self._display_error(f"Failed to load flow: {flow_info['name']}")
                return None
            
            self._display_success(f"Loaded flow: {flow_data.get('trigger', 'Unknown')}")
            return flow_data
        except Exception as e:
            self.logger.error(f"Flow loading failed: {e}")
            self._display_error(f"Flow loading failed: {e}")
            return None
    
    async def _load_employees(self, flow_data: Dict) -> Optional[List[Dict]]:
        """Load employee data."""
        try:
            employees = await self.employee_loader.load_employees(flow_data)
            if not employees:
                self._display_error("Failed to load employee data")
                return None
            
            self._display_success(f"Loaded {len(employees)} employee(s)")
            return employees
        except Exception as e:
            self.logger.error(f"Employee loading failed: {e}")
            self._display_error(f"Employee loading failed: {e}")
            return None
    
    async def _execute_flow(self, flow_data: Dict, employees: List[Dict]):
        """Execute the flow."""
        try:
            self._display_info(f"Executing flow for {len(employees)} employee(s)...")
            
            results = await self.flow_engine.execute_flow(flow_data, employees)
            
            # Display results
            successful = sum(1 for r in results if r.get('success', False))
            success_rate = (successful / len(results)) * 100 if results else 0
            
            if console:
                results_text = Text(f"Execution Complete", style="bold green")
                results_panel = Panel(
                    f"✅ Successful: {successful}/{len(results)}\n"
                    f"📊 Success Rate: {success_rate:.1f}%",
                    title="Results",
                    border_style="green"
                )
                console.print(results_panel)
            else:
                print(f"\n✅ Execution Complete")
                print(f"Successful: {successful}/{len(results)}")
                print(f"Success Rate: {success_rate:.1f}%")
                
        except RuntimeError as e:
            self.logger.error(f"Flow execution failed: {e}")
            self._display_error(f"Flow execution failed: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error during execution: {e}")
            self._display_error(f"Unexpected error during execution: {e}")


async def main():
    """Main function."""
    app = WhatsAppFlowTester()
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())
