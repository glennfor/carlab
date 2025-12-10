import threading
import time
from typing import Optional

from evdev import InputDevice, ecodes, util

from actions.controllers.base_controller import BaseController, ControlCommand


class GamepadController(BaseController):
    """Controller implementation for gamepad/joystick input using evdev."""
    
    def __init__(self, device_path: str = '/dev/input/event0', priority: int = 100):
        """
        Initialize gamepad controller.
        
        :param device_path: Path to the gamepad input device
        :param priority: Priority level (default 100 for high priority override)
        """
        super().__init__(name="Gamepad", priority=priority)
        self.device_path = device_path
        self.device = None
        self.running = False
        self.thread = None
        
        self.axis_x_code = ecodes.ABS_X
        self.axis_y_code = ecodes.ABS_Y
        self.axis_rot_code = ecodes.ABS_RX
        self.axis_rot_left_code = ecodes.ABS_Z
        self.axis_rot_right_code = ecodes.ABS_RZ
        

        FALLBACK_AXES_INFO = {
            self.axis_x_code:   {'min': 0, 'max': 65535, 'flat': 2000}, # 2000 is a standard deadzone
            self.axis_y_code:   {'min': 0, 'max': 65535, 'flat': 2000},
            self.axis_rot_code: {'min': 0, 'max': 65535, 'flat': 2000},
        }
        
        self.controller_state = {
            'vx': 0.0,
            'vy': 0.0,
            'rotation': 0.0
        }
        
        self.axis_info = FALLBACK_AXES_INFO
        self.deadzone = 0.1
        self.max_speed = 1.0
    
    def _normalize_axis(self, value: int, axis_code: int) -> float:
        """Normalize axis value to -1.0 to 1.0 range."""
        if axis_code not in self.axis_info:
            return 0.0
        
        axis_min = self.axis_info[axis_code]['min']
        axis_max = self.axis_info[axis_code]['max']
        axis_center = (axis_max + axis_min) / 2
        axis_deadzone = self.axis_info[axis_code]['flat']

        true_value = value - axis_center
        
        if abs(true_value) < axis_deadzone:
            return 0.0
        
        normalized = true_value / ((axis_max - axis_min) / 2.0)
        normalized = max(-1.0, min(1.0, normalized))
        
        print(f"Normalizing axis: axis_code: {axis_code}", f"value: {value}", f"normalized: {normalized}")
        
        return normalized * self.max_speed
        # normalized = (value - axis_min) / axis_range * 2.0 - 1.0
        # normalized = max(-1.0, min(1.0, normalized))
        
        # print(f"Normalizing axis: axis_code: {axis_code}", f"value: {value}", f"normalized: {normalized}")

        # if abs(normalized) < self.deadzone:
        #     return 0.0
        
        # return normalized * self.max_speed
    
    def _read_gamepad_loop(self):
        """Main loop for reading gamepad events."""

        while self.running:
            try:
                for event in self.device.read_loop():
                    if event.type == ecodes.EV_ABS:
                        print(f"event.code: {event.code}", f"event.value: {event.value}", f"self.axis_x_code: {self.axis_x_code}", f"self.axis_y_code: {self.axis_y_code}", f"self.axis_rot_code: {self.axis_rot_code}")
                        if event.code == self.axis_x_code:
                            self.controller_state['vx'] = self._normalize_axis(event.value, event.code)
                        elif event.code == self.axis_y_code:
                            self.controller_state['vy'] = -self._normalize_axis(event.value, event.code)
                        elif event.code == self.axis_rot_code:
                            self.controller_state['rotation'] = 0 #self._normalize_axis(event.value, event.code)
                        # elif event.code == self.axis_rot_left_code:
                        #     self.controller_state['rotation'] = -self._normalize_axis(event.value, event.code)
                        # elif event.code == self.axis_rot_right_code:
                        #     self.controller_state['rotation'] = self._normalize_axis(event.value, event.code)
                        else:
                            print(f"Unknown event: {event}")
            except OSError:
                pass
    
    def start(self):
        """Start the gamepad controller."""
        if self.is_available():
            try:
                self.device = InputDevice(self.device_path)
                for code, info in self.device.capabilities(verbose=True).get(ecodes.EV_ABS, []):
                    _, code_value = code
                    # axis_info[code_value] = {'min': min_value, 'max': max_value, 'flat': flat}
                    # (min_value, max_value, fuzz, flat, range) = info
                # self.axis_info = self.device.absinfo()
                
                # if self.axis_x_code not in self.axis_info:
                #     self.axis_x_code = ecodes.ABS_X
                # if self.axis_y_code not in self.axis_info:
                #     self.axis_y_code = ecodes.ABS_Y
                # if self.axis_rot_code not in self.axis_info:
                #     self.axis_rot_code = ecodes.ABS_RX
                
                self.running = True
                self.thread = threading.Thread(target=self._read_gamepad_loop, daemon=True)
                self.thread.start()
                self.is_active = True
            except Exception as e:
                print(f"Failed to start gamepad controller: {e}")
                self.is_active = False
        else:
            self.is_active = False
    
    def stop(self):
        """Stop the gamepad controller."""
        self.running = False
        if self.device:
            try:
                self.device.close()
            except:
                pass
            self.device = None
        self.is_active = False
    
    def get_command(self) -> Optional[ControlCommand]:
        """Get current control command from gamepad."""
        if not self.is_active:
            return None
        
        cmd = ControlCommand(
            vx=self.controller_state['vx'],
            vy=self.controller_state['vy'],
            rotation=self.controller_state['rotation']
        )
        return cmd if not cmd.is_zero() else None
    
    def is_available(self) -> bool:
        """Check if gamepad device is available."""
        try:
            device = InputDevice(self.device_path)
            device.close()
            return True
        except:
            return False

