# Controller Architecture

This directory contains a modular controller system for the Carlabs project, allowing multiple control methods to be used simultaneously with priority-based override.

## Architecture Overview

The controller system is built around an abstract base class (`BaseController`) that defines a common interface for all control methods. Controllers can be combined and managed by the `ControllerManager`, which selects commands based on priority.

### Core Components

- **`BaseController`**: Abstract base class defining the controller interface
- **`ControlCommand`**: Data class representing movement commands (vx, vy, rotation)
- **`ControllerManager`**: Manages multiple controllers and selects active commands
- **Controller Implementations**: Gamepad, Keyboard, OpenCV Vision, LLM

## Controller Priority System

Controllers are assigned priority levels (higher number = higher priority). The `ControllerManager` selects commands from the highest-priority active controller:

- **Gamepad**: Priority 100 (highest - manual override)
- **Keyboard**: Priority 50 (manual control)
- **OpenCV Vision**: Priority 30 (autonomous navigation)
- **LLM**: Priority 20 (voice commands)

When a higher-priority controller is active, it overrides lower-priority controllers. For example, if you're using a gamepad, it will override OpenCV vision control.

## Available Controllers

### GamepadController

Uses `evdev` to read gamepad/joystick input.

```python
from actions.controllers import GamepadController

gamepad = GamepadController(
    device_path='/dev/input/event0',  # Path to gamepad device
    priority=100
)
```

**Controls:**
- Left Stick X: Strafe (left/right)
- Left Stick Y: Forward/Backward
- Right Stick X: Rotation

### KeyboardController

Reads keyboard input for manual control.

```python
from actions.controllers import KeyboardController

keyboard = KeyboardController(priority=50)
```

**Controls:**
- `W`: Forward
- `S`: Backward
- `A`: Strafe Left
- `D`: Strafe Right
- `Q`: Rotate Counter-clockwise
- `E`: Rotate Clockwise
- `Space`: Stop

### OpenCVController

Uses computer vision to control the car autonomously.

```python
from actions.controllers import OpenCVController

opencv = OpenCVController(
    camera_index=0,  # Camera device index
    priority=30
)
```

**Note:** The default implementation is a placeholder. Extend `_process_frame()` for your specific vision tasks (line following, object tracking, etc.).

### LLMController

Receives commands from the LLM/brain system.

```python
from actions.controllers import LLMController

llm = LLMController(priority=20)
llm.set_command(vx=0.5, vy=0.0, rotation=0.0, duration=2.0)
```

## Usage Examples

### Basic Setup

```python
from actions.car import Car
from actions.controllers import ControllerManager, GamepadController

car = Car()
manager = ControllerManager(car, update_rate=20.0)

gamepad = GamepadController(device_path='/dev/input/event0', priority=100)
manager.add_controller(gamepad)

manager.start()
# Car is now controlled by gamepad
```

### Multiple Controllers

```python
from actions.car import Car
from actions.controllers import (
    ControllerManager,
    GamepadController,
    KeyboardController,
    OpenCVController,
    LLMController,
)

car = Car()
manager = ControllerManager(car)

# Add controllers in priority order
manager.add_controller(GamepadController(priority=100))
manager.add_controller(KeyboardController(priority=50))
manager.add_controller(OpenCVController(priority=30))
manager.add_controller(LLMController(priority=20))

manager.start()
```

### Custom Vision Controller

Extend `OpenCVController` for specific vision tasks:

```python
from actions.controllers import OpenCVController

class LineFollowerController(OpenCVController):
    def _process_frame(self, frame):
        # Your line following logic here
        # Return ControlCommand(vx, vy, rotation)
        pass
```

## Integration with Main System

The controller system integrates with the main voice control system through `actions.engine`:

```python
from actions.engine import initialize, execute

# Initialize with car and controller manager
car = Car()
manager = ControllerManager(car)
llm_controller = LLMController()
manager.add_controller(llm_controller)

initialize(car=car, controller_manager=manager)
manager.start()

# LLM can now control car via execute()
execute("forward", {"speed": 0.5, "duration": 2.0})
```

## Thread Safety

All controllers run in separate threads and are thread-safe. The `ControllerManager` coordinates commands from all controllers in a single control loop running at the specified update rate (default 20 Hz).

## Extending the System

To create a new controller:

1. Inherit from `BaseController`
2. Implement required methods:
   - `start()`: Initialize and start the controller
   - `stop()`: Clean up and stop the controller
   - `get_command()`: Return current `ControlCommand` or `None`
   - `is_available()`: Check if controller can be used
3. Add to `ControllerManager` with appropriate priority

Example:

```python
from actions.controllers import BaseController, ControlCommand

class MyCustomController(BaseController):
    def __init__(self, priority=25):
        super().__init__(name="My Controller", priority=priority)
    
    def start(self):
        # Initialize your controller
        self.is_active = True
    
    def stop(self):
        # Clean up
        self.is_active = False
    
    def get_command(self):
        # Return ControlCommand or None
        return ControlCommand(vx=0.5, vy=0.0, rotation=0.0)
    
    def is_available(self):
        # Check if available
        return True
```

