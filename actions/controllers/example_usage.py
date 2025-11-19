"""
Example usage of the controller system.

This demonstrates how to set up and use multiple controllers with the ControllerManager.
"""

from ..car import Car
from . import (ControllerManager, GamepadController,
              )


def main():
    """Example: Set up car with multiple controllers."""
    car = Car()
    
    manager = ControllerManager(car, update_rate=20.0)
    
    gamepad = GamepadController(device_path='/dev/input/event8', priority=100)
    # keyboard = KeyboardController(priority=50)
    # opencv = OpenCVController(camera_index=0, priority=30)
    # llm = LLMController(priority=20)
    
    manager.add_controller(gamepad)
    # manager.add_controller(keyboard)
    # manager.add_controller(opencv)
    # manager.add_controller(llm)
    
    try:
        manager.start()
        print("Controllers started. Press Ctrl+C to stop.")
        
        while True:
            status = manager.get_status()
            # print(f"\rActive: {status['active_controller']}, Command: {status['current_command']}", end='')
            import time
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        manager.stop()
        car.cleanup()


if __name__ == '__main__':
    main()

