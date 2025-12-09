# LLM-Based Robot Control System

A new paradigm for controlling the robot car via LLM instructions with sequential execution and capability-based planning.

## Overview

This system allows the robot to:
1. Receive text instructions (from terminal for testing, or transcribed from microphone in production)
2. Validate requests using an LLM that understands available capabilities
3. Create execution plans using only valid capabilities
4. Execute instructions sequentially with "hand-the-baton" style for mutually exclusive operations
5. Provide spoken responses

## Architecture

### Components

1. **Capabilities Registry** (`capabilities.py`)
   - Defines all innate robot capabilities
   - Tracks which capabilities are mutually exclusive
   - Provides capability descriptions for LLM prompts

2. **LLM Planner** (`llm_planner.py`)
   - Validates user requests against available capabilities
   - Creates execution plans using LLM reasoning
   - Rejects impossible requests with explanations

3. **Instruction Executor** (`instruction_executor.py`)
   - Executes instructions sequentially
   - Handles mutual exclusion (one instruction finishes before another starts)
   - Manages instruction queue and execution thread

4. **Command Interface** (`llm_command_interface.py`)
   - Main interface for processing commands
   - Interactive terminal mode for testing
   - Integrates all components

## Capabilities

### Mechanical Capabilities (Mutually Exclusive)
- **make_step**: Move forward/backward with size [tiny, small, large]
- **make_turn**: Turn left/right while moving with magnitude [tiny, small, large]
- **spin_in_place**: Full in-place spin left/right

### Other Capabilities
- **speak**: Speak text aloud (can run concurrently)
- **take_picture**: Capture image from camera (can run concurrently)
- **track_person**: Track person using face recognition (mutually exclusive with movement)
- **follow_person**: Follow a person holding an ArUco marker. Continues following until instructed to stop. Automatically stops when too close to avoid collisions (mutually exclusive with movement)

## Skills (Higher-Level Behaviors)

The LLM can combine capabilities to create skills:
- **Trust walk/Blindfold maze**: Complete maze via audio directions
- **Dance**: Spin while making steps
- **Drive in box pattern**: Sequential steps and turns
- **Follow ball/object**: Use tracking capabilities

## Usage

### Basic Usage

```python
from actions.llm_command_interface import LLMCommandInterface

interface = LLMCommandInterface(openai_api_key="your-key")
interface.process_command("take a small step forward")
```

### Interactive Terminal Mode

```bash
python actions/llm_control_example.py
```

Or:

```bash
python -m actions.llm_command_interface
```

### Example Commands

- "take a small step forward"
- "turn left a little bit"
- "spin in place to the right"
- "take a picture"
- "say hello"
- "dance for me"
- "drive in a box pattern"

## Execution Model

### Sequential Execution
Instructions execute one at a time. If two instructions are mutually exclusive (e.g., both involve movement), they are queued and executed sequentially.

### Concurrent Execution
Some capabilities (like `speak` and `take_picture`) are not mutually exclusive and could theoretically run concurrently, but currently all instructions are executed sequentially for simplicity and safety.

## Integration with Production

To integrate with the voice pipeline:

```python
from actions.llm_command_interface import LLMCommandInterface

# In main.py or similar
interface = LLMCommandInterface()

# After transcribing audio
text = transcribe("audio.wav")
result = interface.process_command(text)

# Speak the response
speak(result["speech"])
```

## Configuration

Set `OPENAI_API_KEY` environment variable:

```bash
export OPENAI_API_KEY="your-api-key"
```

## System Prompt

The LLM receives a system prompt that includes:
- All available capabilities with parameters
- Rules for creating valid plans
- Examples of valid outputs
- Instructions to reject impossible requests

## Error Handling

- Invalid capabilities are rejected during validation
- JSON parsing errors are caught and handled gracefully
- Execution errors are logged and instruction status is updated
- Failed instructions don't block the queue

## Status Monitoring

Check execution status:

```python
status = interface.get_status()
# Returns: {
#   "is_running": bool,
#   "queue_length": int,
#   "current_instruction": {...} or None
# }
```

## ArUco Marker Following

The `follow_person` capability allows the car to follow a person holding an ArUco marker. 

### Setup

1. Print an ArUco marker (ID 0, DICT_4X4_50) - you can generate one using OpenCV or online tools
2. The marker should be at least 5cm x 5cm for reliable detection
3. Hold the marker so it's visible to the camera

### Usage

Simply say "follow me" or "follow the person" and the car will start following. Say "stop" to stop following.

### Behavior

- The car tracks the ArUco marker in the camera view
- It maintains a target distance (default 0.8m)
- It automatically stops if it gets too close (default 0.3m minimum distance)
- It stops following if the marker is lost for more than 2 seconds
- The following can be interrupted by saying "stop"

### Configuration

The follower can be configured with parameters:
- `marker_id`: ArUco marker ID to track (default: 0)
- `target_distance`: Target following distance in meters (default: 0.8)
- `min_distance`: Minimum safe distance in meters (default: 0.3)

## Future Enhancements

- Add distance/speed tracking capabilities
- Add more complex skills
- Support concurrent execution for non-mutually-exclusive capabilities
- Add instruction cancellation
- Add progress callbacks

