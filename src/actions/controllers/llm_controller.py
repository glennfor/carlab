import time
from typing import Optional

from actions.controllers.base_controller import BaseController, ControlCommand


class LLMController(BaseController):
    """Controller implementation for LLM-based control commands."""
    
    def __init__(self, priority: int = 20):
        """
        Initialize LLM controller.
        
        :param priority: Priority level (default 20, lower than manual controls)
        """
        super().__init__(name="LLM", priority=priority)
        self.current_command = ControlCommand()
        self.command_timeout = 2.0
        self.last_command_time = 0
    
    def set_command(self, vx: float = 0.0, vy: float = 0.0, rotation: float = 0.0, duration: float = 1.0):
        """
        Set a control command from LLM.
        
        :param vx: Lateral velocity
        :param vy: Longitudinal velocity
        :param rotation: Angular velocity
        :param duration: How long this command should be active (seconds)
        """
        self.current_command = ControlCommand(vx=vx, vy=vy, rotation=rotation)
        self.last_command_time = time.time()
        self.command_timeout = duration
        self.is_active = True
    
    def start(self):
        """Start the LLM controller."""
        self.is_active = True
    
    def stop(self):
        """Stop the LLM controller."""
        self.current_command = ControlCommand()
        self.is_active = False
    
    def get_command(self) -> Optional[ControlCommand]:
        """Get current control command from LLM."""
        if not self.is_active:
            return None
        
        if time.time() - self.last_command_time > self.command_timeout:
            self.current_command = ControlCommand()
            return None
        
        return self.current_command if not self.current_command.is_zero() else None
    
    def is_available(self) -> bool:
        """LLM controller is always available."""
        return True

