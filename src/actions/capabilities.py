from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class StepSize(Enum):
    TINY = "tiny"
    SMALL = "small"
    LARGE = "large"


class Direction(Enum):
    LEFT = "left"
    RIGHT = "right"
    FORWARD = "forward"
    BACKWARD = "backward"


class TurnMagnitude(Enum):
    TINY = "tiny"
    SMALL = "small"
    LARGE = "large"


@dataclass
class Capability:
    name: str
    description: str
    mutually_exclusive_with: List[str]
    parameters: Dict[str, Any]


class CapabilitiesRegistry:
    """Registry of all robot capabilities."""
    
    def __init__(self):
        self.capabilities: Dict[str, Capability] = {}
        self._register_all()
    
    def _register_all(self):
        """Register all available capabilities."""
        
        # Mechanical capabilities (mutually exclusive with each other)
        mechanical_caps = [
            "make_step",
            "make_turn",
            "spin_in_place"
        ]
        
        self.capabilities["make_step"] = Capability(
            name="make_step",
            description="Move the robot forward or backward by a step",
            mutually_exclusive_with=mechanical_caps,
            parameters={
                "size": [s.value for s in StepSize],
                "direction": ["forward", "backward"]
            }
        )
        
        self.capabilities["make_turn"] = Capability(
            name="make_turn",
            description="Turn the robot left or right while moving",
            mutually_exclusive_with=mechanical_caps,
            parameters={
                "direction": ["left", "right"],
                "magnitude": [m.value for m in TurnMagnitude]
            }
        )
        
        self.capabilities["spin_in_place"] = Capability(
            name="spin_in_place",
            description="Spin the robot in place without moving forward/backward",
            mutually_exclusive_with=mechanical_caps,
            parameters={
                "direction": ["left", "right"]
            }
        )
        
        # Non-mechanical capabilities (can run concurrently with each other)
        self.capabilities["speak"] = Capability(
            name="speak",
            description="Speak text aloud",
            mutually_exclusive_with=[],  # Can run with anything
            parameters={
                "text": "string"
            }
        )
        
        self.capabilities["take_picture"] = Capability(
            name="take_picture",
            description="Capture an image from the camera",
            mutually_exclusive_with=[],  # Can run with anything
            parameters={}
        )
        
        self.capabilities["track_person"] = Capability(
            name="track_person",
            description="Track a person using face recognition",
            mutually_exclusive_with=mechanical_caps,  # Can't move while tracking
            parameters={}
        )
        
        self.capabilities["follow_person"] = Capability(
            name="follow_person",
            description="Follow a person holding an ArUco marker. Continues following until instructed to stop. Automatically stops when too close to avoid collisions.",
            mutually_exclusive_with=mechanical_caps,  # Can't do other movements while following
            parameters={}
        )
    
    def get_capability(self, name: str) -> Optional[Capability]:
        """Get a capability by name."""
        return self.capabilities.get(name)
    
    def list_capabilities(self) -> List[str]:
        """List all capability names."""
        return list(self.capabilities.keys())
    
    def are_mutually_exclusive(self, cap1: str, cap2: str) -> bool:
        """Check if two capabilities are mutually exclusive."""
        c1 = self.get_capability(cap1)
        c2 = self.get_capability(cap2)
        
        if not c1 or not c2:
            return False
        
        return cap2 in c1.mutually_exclusive_with or cap1 in c2.mutually_exclusive_with
    
    def get_capabilities_description(self) -> str:
        """Get a formatted description of all capabilities for LLM prompts."""
        lines = ["Available Capabilities:"]
        for cap in self.capabilities.values():
            lines.append(f"\n- {cap.name}: {cap.description}")
            if cap.parameters:
                lines.append(f"  Parameters: {cap.parameters}")
            if cap.mutually_exclusive_with:
                lines.append(f"  Mutually exclusive with: {', '.join(cap.mutually_exclusive_with)}")
        return "\n".join(lines)

