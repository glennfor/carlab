from actions.car import Car
from actions.controllers.controller_manager import ControllerManager
from actions.controllers.llm_controller import LLMController

_car_instance = None
_controller_manager = None
_llm_controller = None


def initialize(car: Car = None, controller_manager: ControllerManager = None):
    """
    Initialize the action engine with car and controller manager instances.
    
    :param car: Car instance (creates new one if None)
    :param controller_manager: ControllerManager instance (creates new one if None)
    """
    global _car_instance, _controller_manager, _llm_controller
    
    if car is None:
        _car_instance = Car()
    else:
        _car_instance = car
    
    if controller_manager is None:
        _controller_manager = ControllerManager(_car_instance)
        _llm_controller = LLMController()
        _controller_manager.add_controller(_llm_controller)
    else:
        _controller_manager = controller_manager
        _llm_controller = None
        for controller in _controller_manager.controllers:
            if isinstance(controller, LLMController):
                _llm_controller = controller
                break


def execute(action: str, value=None):
    """
    Execute an action command.
    
    :param action: Action name (e.g., 'drive', 'forward', 'rotate', etc.)
    :param value: Action value (can be dict, number, or None)
    """
    global _car_instance, _llm_controller
    
    if _car_instance is None:
        initialize()
    
    if _llm_controller is None:
        if _controller_manager:
            _llm_controller = LLMController()
            _controller_manager.add_controller(_llm_controller)
        else:
            initialize()
    
    if action == 'drive':
        if isinstance(value, dict):
            vx = value.get('vx', 0.0)
            vy = value.get('vy', 0.0)
            rotation = value.get('rotation', 0.0)
            duration = value.get('duration', 1.0)
            _llm_controller.set_command(vx, vy, rotation, duration)
        else:
            _llm_controller.set_command(0, 0, 0, 0.1)
    
    elif action == 'forward':
        speed = float(value) if value is not None else 0.5
        duration = 1.0
        if isinstance(value, dict):
            speed = value.get('speed', 0.5)
            duration = value.get('duration', 1.0)
        _llm_controller.set_command(0, speed, 0, duration)
    
    elif action == 'backward':
        speed = float(value) if value is not None else 0.5
        duration = 1.0
        if isinstance(value, dict):
            speed = value.get('speed', 0.5)
            duration = value.get('duration', 1.0)
        _llm_controller.set_command(0, -speed, 0, duration)
    
    elif action == 'strafe':
        speed = float(value) if value is not None else 0.5
        direction = 1.0
        duration = 1.0
        if isinstance(value, dict):
            speed = value.get('speed', 0.5)
            direction = value.get('direction', 1.0)
            duration = value.get('duration', 1.0)
        _llm_controller.set_command(speed * direction, 0, 0, duration)
    
    elif action == 'rotate':
        speed = float(value) if value is not None else 0.5
        direction = 1.0
        duration = 1.0
        if isinstance(value, dict):
            speed = value.get('speed', 0.5)
            direction = value.get('direction', 1.0)
            duration = value.get('duration', 1.0)
        _llm_controller.set_command(0, 0, speed * direction, duration)
    
    elif action == 'stop':
        _llm_controller.set_command(0, 0, 0, 0.1)
    
    else:
        print(f"Unknown action: {action}")

