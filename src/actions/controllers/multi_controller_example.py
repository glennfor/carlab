"""
Example: Using multiple controllers with priority-based override.

This demonstrates how gamepad can override OpenCV vision control,
and how keyboard can override LLM commands.
"""

import signal
import sys
import time

from actions.car import Car
from actions.controllers import (
    ControllerManager,
    GamepadController,
    KeyboardController,
    OpenCVController,
    LLMController,
)


def signal_handler(sig, frame, car, manager):
    """Handle shutdown signals."""
    print("\nShutting down...")
    manager.stop()
    car.cleanup()
    sys.exit(0)


def main():
    """Example with multiple controllers."""
    print("Initializing car and controllers...")
    
    car = Car()
    manager = ControllerManager(car, update_rate=20.0)
    
    gamepad = GamepadController(device_path='/dev/input/event0', priority=100)
    keyboard = KeyboardController(priority=50)
    opencv = OpenCVController(camera_index=0, priority=30)
    llm = LLMController(priority=20)
    
    manager.add_controller(gamepad)
    manager.add_controller(keyboard)
    manager.add_controller(opencv)
    manager.add_controller(llm)
    
    signal.signal(signal.SIGINT, lambda s, f: signal_handler(s, f, car, manager))
    signal.signal(signal.SIGTERM, lambda s, f: signal_handler(s, f, car, manager))
    
    try:
        manager.start()
        print("\n" + "="*60)
        print("Multi-Controller System Started")
        print("="*60)
        print("\nController Priority:")
        print("  1. Gamepad (Priority 100) - Manual override")
        print("  2. Keyboard (Priority 50) - Manual control")
        print("  3. OpenCV Vision (Priority 30) - Autonomous")
        print("  4. LLM (Priority 20) - Voice commands")
        print("\nPress Ctrl+C to stop")
        print("="*60 + "\n")
        
        while True:
            status = manager.get_status()
            active = status['active_controller']
            cmd = status['current_command']
            
            if active:
                print(f"\rActive: {active:20s} | Command: {cmd}", end='', flush=True)
            else:
                print(f"\rActive: None{'':15s} | Command: {cmd}", end='', flush=True)
            
            time.sleep(0.1)
    
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        manager.stop()
        car.cleanup()


if __name__ == '__main__':
    main()

