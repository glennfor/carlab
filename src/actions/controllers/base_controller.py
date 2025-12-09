from abc import ABC, abstractmethod
from typing import Optional, Tuple


class ControlCommand:
    """Represents a control command with velocity components."""
    def __init__(self, vx: float = 0.0, vy: float = 0.0, rotation: float = 0.0):
        self.vx = vx
        self.vy = vy
        self.rotation = rotation
    
    def is_zero(self) -> bool:
        """Check if all components are effectively zero."""
        return abs(self.vx) < 0.01 and abs(self.vy) < 0.01 and abs(self.rotation) < 0.01
    
    def __repr__(self):
        return f"ControlCommand(vx={self.vx:.2f}, vy={self.vy:.2f}, rotation={self.rotation:.2f})"


class BaseController(ABC):
    """Abstract base class for all car controllers."""
    
    def __init__(self, name: str, priority: int = 0):
        """
        Initialize the controller.
        
        :param name: Human-readable name for this controller
        :param priority: Priority level (higher = more priority, can override lower priority controllers)
        """
        self.name = name
        self.priority = priority
        self.is_active = False
    
    @abstractmethod
    def start(self):
        """Start the controller (e.g., open device, start thread)."""
        pass
    
    @abstractmethod
    def stop(self):
        """Stop the controller (e.g., close device, stop thread)."""
        pass
    
    @abstractmethod
    def get_command(self) -> Optional[ControlCommand]:
        """
        Get the current control command from this controller.
        
        :return: ControlCommand if active, None if no command available
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if this controller is available (e.g., device connected).
        
        :return: True if controller can be used
        """
        pass
    
    def __lt__(self, other):
        """Compare controllers by priority for sorting."""
        return self.priority < other.priority
    
    def __repr__(self):
        return f"{self.__class__.__name__}(name='{self.name}', priority={self.priority})"

