import re
from typing import List, Dict

class FlowGenerator:
    """
    Generates user-behavior flow steps JSON from agentic prompt.
    """
    def __init__(self, llm_analyzer):
        self.llm_analyzer = llm_analyzer

    async def prompt_to_flow_json(self, prompt: str) -> Dict:
        # Split prompt into steps (naive split, can be improved)
        steps = re.split(r'\n|(?<=\.)\s*(?=Step\d+:)', prompt)
        steps = [s.strip() for s in steps if s.strip()]
        user_steps = []
        for step in steps:
            # Only keep user-behavior steps (not agent actions)
            if step.lower().startswith("step"):
                # Optionally, filter for user actions
                user_steps.append(step)
        # Optionally, use LLM to rewrite steps to user-behavior format
        # For now, just pass through
        flow_json = {
            "description": "Generated flow from prompt",
            "data_source": "data/employees.csv",
            "flow_steps": user_steps,
            "media_paths": ["media/images"]
        }
        return flow_json
