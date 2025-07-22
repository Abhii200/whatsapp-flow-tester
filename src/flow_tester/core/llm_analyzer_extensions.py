from typing import List

class LLMAnalyzerExtensions:
    """
    Extension for LLMAnalyzer to generate user-behavior steps from agentic prompt.
    """
    def __init__(self, llm_analyzer):
        self.llm_analyzer = llm_analyzer

    async def generate_user_steps(self, prompt: str) -> List[str]:
        import re
        import logging
        user_steps = []
        # Always start with 'Stop' message to stop current flow in backend
        user_steps.append("Step1: User sends a message 'Stop' to initiate the flow.")
        step_num = 2

        # Custom LLM prompt for user behavior steps
        llm_prompt = f"""
You are a WhatsApp flow tester. Your job is to convert a flow description into a list of WhatsApp USER actions ONLY.

Instructions:
1. Only include steps that represent explicit actions a real WhatsApp user would perform in the WhatsApp app:
   - Sending a message (e.g., 'odometer', 'expense', 'confirm', 'send', 'cancel', 'right', etc.)
   - Uploading an image (e.g., expense receipt, odometer reading)
   - Sending a location
   - Sending a voice message
2. Do NOT include agent/system/tool instructions, responses, summaries, or confirmations.
3. ALWAYS include ALL user response steps (such as 'confirm', 'send', 'cancel', 'select', 'respond', 'right', etc.), even if the flow description says 'User responds...', 'User confirms...', or similar. If the user has to confirm, cancel, or take any action, make sure it is a separate step.
4. Format each step as: StepN: User sends a message '...'
5. For image uploads, use: StepN: User uploads an image '<dynamic image path from prompt>' as proof of the relevant action (e.g., odometer reading, expense receipt, etc.)
6. Number the steps sequentially, starting from Step{step_num}.
7. Ignore any step that is not a direct user action.

Example input:
Step1: User sends a message containing the word "odometer" to initiate the flow.
Step2: AI agent responds with a message "Please share your odometer reading image."
Step3: User sends an image of the odometer reading.
Step4: AI agent processes the image and sends a summary.
Step5: User responds with confirmation or cancellation.
Step6: AI agent sends final response.

Example output:
Step1: User sends a message 'odometer'
Step2: User uploads an image 'media/images/odometer/4628082811_bd628e4998_b.jpg' as proof of the odometer reading.
Step3: User sends a message 'confirmation'
Step4: User sends a message 'cancel'
Step5: User sends a message 'right'

Now, generate the user behavior steps for the following flow:
{prompt}
"""

        logger = logging.getLogger(__name__)
        raw_content = None
        # Use LLM to generate user steps
        if hasattr(self.llm_analyzer, "client") and self.llm_analyzer.client:
            try:
                response = self.llm_analyzer.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "user", "content": llm_prompt}
                    ],
                    temperature=0.1,
                )
                raw_content = response.choices[0].message.content.strip()
                logger.info(f"LLM raw output: {raw_content}")
                # Extract steps from LLM output
                lines = [l.strip() for l in raw_content.split("\n") if l.strip()]
                for line in lines:
                    # Only keep strict user actions
                    if self._is_user_action_strict(line):
                        user_steps.append(line)
            except Exception as e:
                logger.error(f"LLM step generation failed: {e}")

        # Fallback: If only 'Stop' step is present, try to parse prompt manually
        if len(user_steps) == 1:
            steps = re.split(r'\n|(?<=\.)\s*(?=Step\d+:)', prompt)
            steps = [s.strip() for s in steps if s.strip()]
            for step in steps:
                # Only process steps that describe user actions
                if step.lower().startswith("step") and ("user sends" in step.lower() or "user uploads" in step.lower()):
                    rewritten = await self._rewrite_step_with_llm(step)
                    if rewritten and self._is_user_action_strict(rewritten):
                        # Dynamically extract image path and description from step
                        if "uploads an image" in rewritten:
                            # Use expense image for expense flows, odometer image for odometer flows
                            if "expense" in prompt.lower():
                                img_path = "media/images/expense/WhatsApp Image 2025-06-29 at 11.13.09_dbd66e21.jpg"
                                context = "the expense receipt"
                            else:
                                img_path = "media/images/odometer/4628082811_bd628e4998_b.jpg"
                                context = "the odometer reading"
                            rewritten = f"Step{step_num}: User uploads an image '{img_path}' as proof of {context}."
                        elif "sends a message" in rewritten:
                            msg_match = re.search(r"'([^']+)'", rewritten)
                            msg = msg_match.group(1) if msg_match else ""
                            if msg:
                                rewritten = f"Step{step_num}: User sends a message '{msg}'"
                            else:
                                rewritten = f"Step{step_num}: User sends a message."
                        elif "sends location" in rewritten:
                            rewritten = f"Step{step_num}: User sends location."
                        elif "sends a voice message" in rewritten:
                            rewritten = f"Step{step_num}: User sends a voice message."
                        else:
                            rewritten = f"Step{step_num}: {rewritten}"
                        user_steps.append(rewritten)
                        step_num += 1
        return user_steps

    def _is_user_action_strict(self, step: str) -> bool:
        s = step.lower()
        return (
            s.startswith("user sends a message") or
            s.startswith("user uploads an image") or
            s.startswith("user sends location") or
            s.startswith("user sends a voice message")
        )

    def _is_user_action(self, step: str) -> bool:
        # Only keep steps that start with 'User' and describe a WhatsApp action
        return step.lower().startswith("user sends") or step.lower().startswith("user uploads")

    async def _rewrite_step_with_llm(self, step: str) -> str:
        """
        Use LLMAnalyzer to rewrite a step into a user-behavior step.
        """
        if hasattr(self.llm_analyzer, "analyze_step"):
            try:
                tool_info = await self.llm_analyzer.analyze_step(step)
                # Format as user-behavior step string
                if tool_info["tool"] == "send_text":
                    return f"User sends a message '{tool_info['parameters']['body']}'"
                elif tool_info["tool"] == "send_image":
                    # Always use odometer image path for odometer flows
                    img = 'media/images/odometer/4628082811_bd628e4998_b.jpg'
                    return f"User uploads an image '{img}'"
                elif tool_info["tool"] == "send_location":
                    lat = tool_info['parameters'].get('latitude', '')
                    lon = tool_info['parameters'].get('longitude', '')
                    return f"User sends location (latitude: {lat}, longitude: {lon})"
                elif tool_info["tool"] == "send_voice":
                    voice = tool_info['parameters'].get('voice_path', 'voice.wav')
                    return f"User sends a voice message '{voice}'"
                else:
                    return step  # fallback to original step
            except Exception:
                return step  # fallback to original step
        else:
            return step  # fallback to original step
