import threading
import time
from typing import List, Optional

from actions.car import Car
from actions.controllers.base_controller import BaseController, ControlCommand


class ControllerManager:
    """Manages multiple controllers with priority-based command selection."""
    
    def __init__(self, car: Car, update_rate: float = 20.0):
        """
        Initialize the controller manager.
        
        :param car: Car instance to control
        :param update_rate: Control loop update rate in Hz
        """
        self.car = car
        self.update_rate = update_rate
        self.update_interval = 1.0 / update_rate
        
        self.controllers: List[BaseController] = []
        self.running = False
        self.control_thread = None
        
        self.current_command = ControlCommand()
        self.last_update_time = 0
    
    def add_controller(self, controller: BaseController):
        """Add a controller to the manager."""
        if controller not in self.controllers:
            self.controllers.append(controller)
            self.controllers.sort(reverse=True)
    
    def remove_controller(self, controller: BaseController):
        """Remove a controller from the manager."""
        if controller in self.controllers:
            controller.stop()
            self.controllers.remove(controller)
    
    def start_all(self):
        """Start all available controllers."""
        for controller in self.controllers:
            if controller.is_available():
                controller.start()
                print(f"Started controller: {controller.name}")
            else:
                print(f"Controller {controller.name} is not available")
    
    def stop_all(self):
        """Stop all controllers."""
        self.running = False
        for controller in self.controllers:
            controller.stop()
    
    def _select_command(self) -> Optional[ControlCommand]:
        """
        Select the highest priority active command from controllers.
        
        :return: ControlCommand from highest priority active controller, or None
        """
        for controller in self.controllers:
            if controller.is_active:
                cmd = controller.get_command()
                if cmd and not cmd.is_zero():
                    return cmd
        return None
    
    def _control_loop(self):
        """Main control loop that updates car movement."""
        while self.running:
            start_time = time.time()
            
            cmd = self._select_command()
            
            if cmd:
                self.current_command = cmd
                self.car.drive(cmd.vx, cmd.vy, cmd.rotation)
            else:
                self.current_command = ControlCommand()
                self.car.drive(0, 0, 0)
            
            elapsed = time.time() - start_time
            sleep_time = max(0, self.update_interval - elapsed)
            time.sleep(sleep_time)
    
    def start(self):
        """Start the controller manager and control loop."""
        self.start_all()
        self.running = True
        self.control_thread = threading.Thread(target=self._control_loop, daemon=True)
        self.control_thread.start()
        print("Controller manager started")
    
    def stop(self):
        """Stop the controller manager."""
        self.stop_all()
        self.car.drive(0, 0, 0)
        print("Controller manager stopped")
    
    def get_active_controller(self) -> Optional[BaseController]:
        """Get the currently active controller."""
        for controller in self.controllers:
            if controller.is_active:
                cmd = controller.get_command()
                if cmd and not cmd.is_zero():
                    return controller
        return None
    
    def get_status(self) -> dict:
        """Get status of all controllers."""
        return {
            'running': self.running,
            'current_command': str(self.current_command),
            'active_controller': self.get_active_controller().name if self.get_active_controller() else None,
            'controllers': [
                {
                    'name': c.name,
                    'priority': c.priority,
                    'active': c.is_active,
                    'available': c.is_available()
                }
                for c in self.controllers
            ]
        }

