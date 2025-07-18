"""
Generic flow execution engine.
Handles flow execution with dynamic tool selection.
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging

from flow_tester.tools.tool_factory import ToolFactory
from flow_tester.core.llm_analyzer import LLMAnalyzer
from flow_tester.services.response_handler import ResponseHandler
from flow_tester.config.flow_config import FlowConfig


class FlowEngine:
    """Generic flow execution engine."""
    
    def __init__(self, settings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        self.tool_factory = ToolFactory(settings)
        self.llm_analyzer = LLMAnalyzer(settings)
        self.response_handler = ResponseHandler(settings)
    
    async def execute_flow(self, flow_data: Dict[str, Any], employees: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Execute flow for multiple employees.
        
        Args:
            flow_data: Flow configuration data
            employees: List of employee data
            
        Returns:
            List of execution results
        """
        flow_config = FlowConfig.from_dict(flow_data)
        
        # Validate flow configuration
        is_valid, errors = flow_config.validate()
        if not is_valid:
            raise ValueError(f"Invalid flow configuration: {', '.join(errors)}")
        
        results = []
        is_multi_user = len(employees) > 1
        
        self.logger.info(f"Starting flow execution for {len(employees)} employee(s)")
        
        for i, employee in enumerate(employees):
            try:
                self.logger.info(f"Executing flow for employee {i+1}/{len(employees)}: {employee.get('Employee Name', 'Unknown')}")
                
                result = await self._execute_single_flow(flow_config, employee, is_multi_user)
                results.append(result)
                
                # Add delay between employees in multi-user mode
                if is_multi_user and i < len(employees) - 1:
                    await asyncio.sleep(self.settings.execution_delay)
                    
            except Exception as e:
                self.logger.error(f"Error executing flow for employee {employee.get('Employee Name', 'Unknown')}: {e}")
                results.append({
                    'employee': employee,
                    'success': False,
                    'error': str(e),
                    'timestamp': time.time()
                })
        
        self.logger.info(f"Flow execution completed. Success rate: {sum(1 for r in results if r.get('success', False))}/{len(results)}")
        return results
    
    async def _execute_single_flow(self, flow_config: FlowConfig, employee: Dict[str, Any], is_multi_user: bool) -> Dict[str, Any]:
        """
        Execute flow for a single employee.
        
        Args:
            flow_config: Flow configuration
            employee: Employee data
            is_multi_user: Whether this is part of multi-user execution
            
        Returns:
            Execution result
        """
        employee_phone = employee.get('Employee Phone', '')
        employee_name = employee.get('Employee Name', '')
        
        if not employee_phone:
            raise ValueError(f"Employee phone number is required for {employee_name}")
        
        context = {"last_message_id": None}
        executed_steps = []
        
        try:
            # Send Stop message for multi-user mode
            if is_multi_user:
                await self._send_stop_message(employee_phone, employee_name, context)
            
            # Execute flow steps
            for step_index, step in enumerate(flow_config.flow_steps):
                try:
                    step_result = await self._execute_step(step, employee, context, step_index)
                    executed_steps.append(step_result)
                    
                    # Brief delay between steps
                    await asyncio.sleep(1)
                    
                except RuntimeError as e:
                    self.logger.warning(f"Step {step_index + 1} failed: {e}")
                    executed_steps.append({
                        'step_index': step_index,
                        'step': step,
                        'success': False,
                        'error': str(e)
                    })
                    # Continue with next step
                    continue
            
            # Determine overall success
            successful_steps = sum(1 for step in executed_steps if step.get('success', False))
            success_rate = (successful_steps / len(executed_steps)) * 100 if executed_steps else 0
            
            return {
                'employee': employee,
                'success': success_rate >= 50,  # Consider success if at least 50% of steps succeeded
                'executed_steps': executed_steps,
                'success_rate': success_rate,
                'timestamp': time.time()
            }
            
        except Exception as e:
            self.logger.error(f"Flow execution failed for {employee_name}: {e}")
            return {
                'employee': employee,
                'success': False,
                'error': str(e),
                'executed_steps': executed_steps,
                'timestamp': time.time()
            }
    
    async def _send_stop_message(self, employee_phone: str, employee_name: str, context: Dict[str, Any]):
        """Send stop message to initiate flow."""
        try:
            text_tool = self.tool_factory.create_tool('send_text')
            payload = text_tool.generate_payload(employee_phone, employee_name, "Stop")
            response = text_tool.send(payload)
            
            if response.status_code == 200:
                # Wait for response and update context
                await asyncio.sleep(2)
                latest_message = await self.response_handler.get_latest_message()
                if latest_message and "message_id" in latest_message:
                    context["last_message_id"] = latest_message["message_id"]
                    
        except Exception as e:
            self.logger.warning(f"Failed to send stop message: {e}")
    
    async def _execute_step(self, step: str, employee: Dict[str, Any], context: Dict[str, Any], step_index: int) -> Dict[str, Any]:
        """
        Execute a single flow step.
        
        Args:
            step: Step description
            employee: Employee data
            context: Execution context
            step_index: Step index
            
        Returns:
            Step execution result
        """
        self.logger.debug(f"Executing step {step_index + 1}: {step}")
        
        try:
            # Analyze step with LLM
            tool_info = await self.llm_analyzer.analyze_step(step, employee)
            
            if tool_info.get("tool") == "unknown":
                self.logger.warning(f"Unknown tool for step: {step}")
                return {
                    'step_index': step_index,
                    'step': step,
                    'success': False,
                    'error': 'Unknown tool type'
                }
            
            # Create and execute tool
            tool = self.tool_factory.create_tool(tool_info["tool"])
            if not tool:
                raise RuntimeError(f"Failed to create tool: {tool_info['tool']}")
            
            # Execute tool based on type
            result = await self._execute_tool(tool, tool_info, employee, context)
            
            # Get response
            response_data = await self._get_step_response(tool_info["tool"])
            
            return {
                'step_index': step_index,
                'step': step,
                'tool': tool_info["tool"],
                'success': True,
                'response': response_data,
                'timestamp': time.time()
            }
            
        except Exception as e:
            self.logger.error(f"Step execution failed: {e}")
            raise RuntimeError(f"Step execution failed: {e}")
    
    async def _execute_tool(self, tool, tool_info: Dict[str, Any], employee: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute specific tool."""
        employee_phone = employee.get('Employee Phone', '')
        employee_name = employee.get('Employee Name', '')
        params = tool_info.get('parameters', {})
        
        if tool_info["tool"] == "send_text":
            payload = tool.generate_payload(
                employee_phone, 
                employee_name, 
                params.get("body", ""),
                context.get("last_message_id")
            )
            response = tool.send(payload)
            
        elif tool_info["tool"] == "send_location":
            payload = tool.generate_payload(
                employee_phone,
                employee_name,
                params.get("latitude"),
                params.get("longitude"),
                context.get("last_message_id")
            )
            response = tool.send(payload)
            
        elif tool_info["tool"] == "send_image":
            image_path = params.get("image_path")
            if not image_path or not Path(image_path).exists():
                raise RuntimeError(f"Image file not found: {image_path}")
            
            # Upload image
            media_id, mime_type, sha256 = tool.upload_to_whatsapp_media_api(
                image_path,
                self.settings.whatsapp_phone_number_id,
                self.settings.whatsapp_access_token
            )
            
            if not media_id:
                raise RuntimeError("Failed to upload image")
            
            payload = tool.generate_payload(
                employee_phone,
                employee_name,
                media_id,
                mime_type,
                sha256,
                params.get("caption", "Image"),
                context.get("last_message_id")
            )
            response = tool.send(payload)
            
        elif tool_info["tool"] == "send_voice":
            voice_path = params.get("voice_path")
            if not voice_path or not Path(voice_path).exists():
                raise RuntimeError(f"Voice file not found: {voice_path}")
            
            # Upload voice
            media_id, mime_type, sha256 = tool.upload_to_fastapi_media(voice_path)
            
            if not media_id:
                raise RuntimeError("Failed to upload voice")
            
            payload = tool.generate_payload(
                employee_phone,
                employee_name,
                media_id,
                mime_type,
                sha256,
                context.get("last_message_id")
            )
            response = tool.send(payload)
            
        else:
            raise RuntimeError(f"Unknown tool type: {tool_info['tool']}")
        
        if response.status_code != 200:
            raise RuntimeError(f"Tool execution failed with status {response.status_code}")
        
        return {'status_code': response.status_code}
    
    async def _get_step_response(self, tool_type: str) -> Optional[Dict[str, Any]]:
        """Get response for step execution."""
        try:
            await asyncio.sleep(2)  # Wait for response
            
            latest_message = await self.response_handler.get_latest_message()
            if not latest_message:
                return None
            
            # Process response based on tool type
            if tool_type in ["send_image", "send_voice"]:
                # Extract processed data for media
                extracted_data = self.response_handler.extract_media_response(latest_message)
                return extracted_data
            
            return latest_message
            
        except Exception as e:
            self.logger.warning(f"Failed to get step response: {e}")
            return None
