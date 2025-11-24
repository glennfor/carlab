import sys
import threading
import time
from typing import Optional

from actions.controllers.base_controller import BaseController, ControlCommand


class KeyboardController(BaseController):
    """Controller implementation for keyboard input."""
    
    def __init__(self, priority: int = 50):
        """
        Initialize keyboard controller.
        
        :param priority: Priority level (default 50)
        """
        super().__init__(name="Keyboard", priority=priority)
        self.running = False
        self.thread = None
        self.current_command = ControlCommand()
        
        self.speed_step = 0.1
        self.max_speed = 1.0
        
        self.key_bindings = {
            'w': ('vy', 1.0),
            's': ('vy', -1.0),
            'a': ('vx', -1.0),
            'd': ('vx', 1.0),
            'q': ('rotation', -1.0),
            'e': ('rotation', 1.0),
        }
        
        self.pressed_keys = set()
    
    def _read_keyboard_loop(self):
        """Main loop for reading keyboard input (non-blocking)."""
        try:
            import select
            import tty
            import termios
            
            old_settings = termios.tcgetattr(sys.stdin)
            tty.setraw(sys.stdin.fileno())
            
            while self.running:
                if select.select([sys.stdin], [], [], 0.1)[0]:
                    char = sys.stdin.read(1).lower()
                    
                    if char == '\x1b':
                        break
                    elif char in self.key_bindings:
                        self.pressed_keys.add(char)
                    elif char == ' ':
                        self.pressed_keys.clear()
                        self.current_command = ControlCommand()
                
                self._update_command_from_keys()
                time.sleep(0.05)
            
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        except ImportError:
            print("Keyboard controller requires Unix-like system (termios, tty)")
            self.running = False
        except Exception as e:
            print(f"Keyboard controller error: {e}")
            self.running = False
    
    def _update_command_from_keys(self):
        """Update command based on currently pressed keys."""
        cmd = ControlCommand()
        
        for key in self.pressed_keys:
            if key in self.key_bindings:
                axis, direction = self.key_bindings[key]
                if axis == 'vx':
                    cmd.vx = direction * self.max_speed
                elif axis == 'vy':
                    cmd.vy = direction * self.max_speed
                elif axis == 'rotation':
                    cmd.rotation = direction * self.max_speed
        
        self.current_command = cmd
    
    def start(self):
        """Start the keyboard controller."""
        if self.is_available():
            try:
                self.running = True
                self.thread = threading.Thread(target=self._read_keyboard_loop, daemon=True)
                self.thread.start()
                self.is_active = True
            except Exception as e:
                print(f"Failed to start keyboard controller: {e}")
                self.is_active = False
        else:
            self.is_active = False
    
    def stop(self):
        """Stop the keyboard controller."""
        self.running = False
        self.pressed_keys.clear()
        self.current_command = ControlCommand()
        self.is_active = False
    
    def get_command(self) -> Optional[ControlCommand]:
        """Get current control command from keyboard."""
        if not self.is_active:
            return None
        
        return self.current_command if not self.current_command.is_zero() else None
    
    def is_available(self) -> bool:
        """Check if keyboard input is available."""
        return sys.stdin.isatty()

