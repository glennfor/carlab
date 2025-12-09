import signal
import sys
from typing import Optional, Dict, Any

from actions.car import Car
from actions.capabilities import CapabilitiesRegistry
from actions.llm_planner import LLMPlanner
from actions.instruction_executor import InstructionExecutor


class LLMCommandInterface:
    """Main interface for LLM-based robot control."""
    
    def __init__(self, car: Optional[Car] = None, openai_api_key: Optional[str] = None):
        self.car = car or Car()
        self.capabilities = CapabilitiesRegistry()
        self.planner = LLMPlanner(self.capabilities, api_key=openai_api_key)
        self.executor = InstructionExecutor(self.car, self.capabilities)
        
        self.executor.start()
    
    def process_command(self, text: str) -> Dict[str, Any]:
        """
        Process a text command from the user.
        
        :param text: User's text instruction
        :return: Response dict with status and message
        """
        print(f"\nProcessing command: {text}")
        
        # Get plan from LLM
        plan = self.planner.plan(text)
        
        if not plan.get("can_do"):
            speech = plan.get("speech", "I cannot do that")
            print(f"Response: {speech}")
            return {
                "success": False,
                "speech": speech,
                "reason": "request_not_feasible"
            }
        
        # Execute the plan
        instructions = plan.get("instructions", [])
        if instructions:
            self.executor.add_instructions(instructions)
            print(f"Added {len(instructions)} instruction(s) to queue")
        
        speech = plan.get("speech", "I'll do that")
        print(f"Response: {speech}")
        
        return {
            "success": True,
            "speech": speech,
            "instructions_count": len(instructions)
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current system status."""
        return self.executor.get_status()
    
    def cleanup(self):
        """Clean up resources."""
        self.executor.stop()
        self.car.cleanup()
    
    def run_interactive(self):
        """Run interactive terminal interface for testing."""
        print("LLM Robot Control Interface")
        print("Enter commands (or 'quit' to exit):")
        print("-" * 50)
        
        def signal_handler(sig, frame):
            print("\nShutting down...")
            self.cleanup()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            while True:
                try:
                    command = input("\n> ").strip()
                    
                    if not command:
                        continue
                    
                    if command.lower() in ['quit', 'exit', 'q']:
                        break
                    
                    if command.lower() == 'status':
                        status = self.get_status()
                        print(f"Status: {status}")
                        continue
                    
                    self.process_command(command)
                    
                    # Wait a bit for execution to start
                    import time
                    time.sleep(0.5)
                    
                except EOFError:
                    break
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"Error: {e}")
        
        finally:
            self.cleanup()
            print("Goodbye!")


if __name__ == "__main__":
    import os
    
    api_key = os.getenv("OPENAI_API_KEY")
    interface = LLMCommandInterface(openai_api_key=api_key)
    interface.run_interactive()

