# Carlabs Architecture

## Overview

Carlabs is a modular voice-controlled robot car system built on a Raspberry Pi 4. The system supports multiple control methods (gamepad, keyboard, OpenCV vision, LLM) with a priority-based override system.

## System Components

### 1. Hardware Layer
- **Car** (`actions/car.py`): 3-wheel omni drive (Kiwi configuration) with inverse kinematics
- **Motor** (`actions/motor.py`): Individual motor control with PWM and direction control

### 2. Controller System (`actions/controllers/`)
Modular controller architecture with abstract base class:

- **BaseController**: Abstract interface for all controllers
- **ControllerManager**: Manages multiple controllers with priority-based selection
- **GamepadController**: Gamepad/joystick input via evdev
- **KeyboardController**: Keyboard input for manual control
- **OpenCVController**: Computer vision-based autonomous control
- **LLMController**: Voice command execution from LLM

### 3. Audio Pipeline
- **Wake Word Detection** (`wakeword/hotword.py`): Listens for activation phrase
- **Speech Recognition** (`asr/transcribe.py`): Converts audio to text
- **Text-to-Speech** (`tts/speak.py`): Converts LLM responses to speech

### 4. LLM Integration (`llm/`)
- **brain.py**: Main LLM interface (likely using LangChain)
- **brain-local.py**: Local LLM using llama.cpp

### 5. Action Engine (`actions/engine.py`)
Executes LLM commands by interfacing with the controller system.

## Control Flow

### Voice Control Flow
1. Wake word detected → System activates
2. Audio recorded → Converted to text via ASR
3. Text sent to LLM → LLM generates response and action
4. Action executed via `engine.execute()` → LLMController receives command
5. ControllerManager selects active controller (priority-based)
6. Car executes movement command

### Multi-Controller Flow
1. ControllerManager polls all active controllers
2. Selects command from highest-priority active controller
3. Applies command to car at fixed update rate (20 Hz default)
4. Lower-priority controllers are overridden when higher-priority ones are active

## Priority System

Controllers are assigned priority levels:
- **Gamepad**: 100 (highest - manual override)
- **Keyboard**: 50 (manual control)
- **OpenCV Vision**: 30 (autonomous navigation)
- **LLM**: 20 (voice commands)

## File Structure

```
carlab/
├── actions/
│   ├── car.py              # Car hardware interface
│   ├── motor.py            # Motor control
│   ├── engine.py           # Action execution engine
│   └── controllers/
│       ├── __init__.py
│       ├── base_controller.py
│       ├── gamepad_controller.py
│       ├── keyboard_controller.py
│       ├── opencv_controller.py
│       ├── llm_controller.py
│       ├── controller_manager.py
│       ├── example_usage.py
│       ├── multi_controller_example.py
│       └── README.md
├── asr/
│   └── transcribe.py
├── tts/
│   └── speak.py
├── llm/
│   ├── brain.py
│   └── brain-local.py
├── wakeword/
│   └── hotword.py
├── main.py                 # Main voice control loop
└── ARCHITECTURE.md         # This file
```

## Usage Examples

### Voice Control Only
```bash
python main.py
```

### Multiple Controllers
```python
from actions.car import Car
from actions.controllers import ControllerManager, GamepadController, OpenCVController

car = Car()
manager = ControllerManager(car)

manager.add_controller(GamepadController(priority=100))
manager.add_controller(OpenCVController(priority=30))

manager.start()
```

### Custom Vision Controller
Extend `OpenCVController` and override `_process_frame()` method for your specific vision tasks.

## Dependencies

- **Hardware Control**: RPi.GPIO
- **Gamepad**: python3-evdev
- **Vision**: opencv-python
- **Audio**: sounddevice, scipy
- **LLM**: langchain (or llama.cpp for local)

## Extension Points

1. **New Controllers**: Inherit from `BaseController` and implement required methods
2. **Vision Algorithms**: Extend `OpenCVController._process_frame()`
3. **LLM Integration**: Modify `llm/brain.py` to use different LLM backends
4. **Action Types**: Extend `actions/engine.py` with new action handlers

## Thread Safety

- Controllers run in separate threads
- ControllerManager coordinates commands in a single control loop
- All controller operations are thread-safe

