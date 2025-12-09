import json
from typing import Any, Dict, List, Optional

from openai import OpenAI

from actions.capabilities import CapabilitiesRegistry


class LLMPlanner:
    """Plans robot actions using LLM based on user requests and available capabilities."""
    
    def __init__(self, capabilities_registry: CapabilitiesRegistry, api_key: Optional[str] = None):
        self.capabilities = capabilities_registry
        self.client = OpenAI(api_key=api_key) if api_key else OpenAI()
        self.model = "gpt-4o-mini"
        
        self.system_prompt = self._build_system_prompt()
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for the LLM."""
        capabilities_desc = self.capabilities.get_capabilities_description()
        
        return f"""You are a robot control planner. Your job is to:
1. Understand user requests
2. Check if the request can be satisfied using available capabilities
3. Create a plan of instruction steps if possible
4. Reject requests that cannot be done
5. Provide a short spoken response

{capabilities_desc}

Skills (examples of what can be built from capabilities):
- "trust walk"/"blindfold maze game": Complete a maze via audio directions (combine make_step with speak)
- Dance: Spin while making steps (combine spin_in_place with make_step)
- Drive in a box pattern: Make steps and turns in sequence
- Follow a ball or object: Use track_person or take_picture capabilities

Rules:
- You MUST output ONLY valid JSON, no other text
- If the request can be done, output: {{"can_do": true, "speech": "short response", "instructions": [{{"capability": "name", "parameters": {{...}}}}]}}
- If the request cannot be done, output: {{"can_do": false, "speech": "explanation why not"}}
- Instructions must use only available capabilities listed above
- Instructions that are mutually exclusive must be executed sequentially (they will be queued)
- Keep speech responses short (1-2 sentences max)
- Parameters must match capability definitions exactly (use exact strings from parameter lists)

Example valid outputs:
{{"can_do": true, "speech": "I'll take a small step forward", "instructions": [{{"capability": "make_step", "parameters": {{"size": "small", "direction": "forward"}}}}]}}

{{"can_do": true, "speech": "I'll dance for you", "instructions": [{{"capability": "spin_in_place", "parameters": {{"direction": "left"}}}}, {{"capability": "make_step", "parameters": {{"size": "small", "direction": "forward"}}}}, {{"capability": "spin_in_place", "parameters": {{"direction": "right"}}}}]}}

{{"can_do": false, "speech": "I cannot fly or jump, I can only move on the ground"}}"""
    
    def plan(self, user_request: str) -> Dict[str, Any]:
        """
        Plan actions based on user request.
        
        :param user_request: Text instruction from user
        :return: Dict with 'can_do', 'speech', and optionally 'instructions'
        """
        try:
            # Try with JSON mode first (for models that support it)
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": user_request}
                    ],
                    temperature=0.3,
                    response_format={"type": "json_object"}
                )
            except Exception:
                # Fallback for models that don't support JSON mode
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": user_request}
                    ],
                    temperature=0.3
                )
            
            raw_response = response.choices[0].message.content.strip()
            
            # Try to extract JSON if response contains other text
            if raw_response.startswith("```json"):
                raw_response = raw_response[7:]
            if raw_response.startswith("```"):
                raw_response = raw_response[3:]
            if raw_response.endswith("```"):
                raw_response = raw_response[:-3]
            raw_response = raw_response.strip()
            
            plan = json.loads(raw_response)
            
            # Validate the plan
            if plan.get("can_do") and "instructions" in plan:
                self._validate_instructions(plan["instructions"])
            
            return plan
            
        except json.JSONDecodeError as e:
            print(f"Failed to parse LLM response as JSON: {e}")
            print(f"Raw response: {raw_response[:200]}...")
            return {
                "can_do": False,
                "speech": "I encountered an error processing your request"
            }
        except Exception as e:
            print(f"Error in LLM planning: {e}")
            return {
                "can_do": False,
                "speech": "I encountered an error. Please try again."
            }
    
    def _validate_instructions(self, instructions: List[Dict[str, Any]]):
        """Validate that instructions use valid capabilities and parameters."""
        for inst in instructions:
            capability_name = inst.get("capability")
            if not capability_name:
                raise ValueError("Instruction missing 'capability' field")
            
            capability = self.capabilities.get_capability(capability_name)
            if not capability:
                raise ValueError(f"Unknown capability: {capability_name}")
            
            params = inst.get("parameters", {})
            # Basic validation - could be more thorough
            for param_name, param_value in params.items():
                if param_name in capability.parameters:
                    expected_values = capability.parameters[param_name]
                    if isinstance(expected_values, list) and param_value not in expected_values:
                        raise ValueError(
                            f"Invalid value '{param_value}' for parameter '{param_name}'. "
                            f"Expected one of: {expected_values}"
                        )

