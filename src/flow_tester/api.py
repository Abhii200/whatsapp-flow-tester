from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os

from flow_tester.core.llm_analyzer import LLMAnalyzer
from flow_tester.core.llm_analyzer_extensions import LLMAnalyzerExtensions
from flow_tester.core.flow_generation import FlowGenerator
from flow_tester.core.flow_engine import FlowEngine
from flow_tester.config.settings import Settings
from flow_tester.services.employee_loader import EmployeeLoader

app = FastAPI()

class FlowRequest(BaseModel):
    prompt: str

class FlowResponse(BaseModel):
    status: str
    flow_json: dict
    execution: list
    logs: list[str] = []

settings = Settings()
llm_analyzer = LLMAnalyzer(settings)
llm_ext = LLMAnalyzerExtensions(llm_analyzer)
flow_generator = FlowGenerator(llm_analyzer)
flow_engine = FlowEngine(settings)
employee_loader = EmployeeLoader(settings)


@app.post("/api/generate-flow", response_model=FlowResponse)
async def generate_flow(request: FlowRequest):
    # 1. Use LLM extension to generate user-behavior steps from prompt
    try:
        user_steps = await llm_ext.generate_user_steps(request.prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM user step generation failed: {e}")

    # 2. Build flow_json using FlowGenerator
    try:
        flow_json = await flow_generator.prompt_to_flow_json(request.prompt)
        flow_json["flow_steps"] = user_steps  # Overwrite with generated steps
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Flow JSON generation failed: {e}")

    # 3. Load employees
    try:
        employees = await employee_loader.load_employees(flow_json)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Employee loading failed: {e}")

    # 4. Execute flow using your existing logic
    try:
        execution_result = await flow_engine.execute_flow(flow_json, employees)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Flow execution failed: {e}")

    # 5. Return results
    return FlowResponse(
        status="success",
        flow_json=flow_json,
        execution=execution_result,
        logs=user_steps
    )
