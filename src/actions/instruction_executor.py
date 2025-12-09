import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from actions.capabilities import (CapabilitiesRegistry, Direction, StepSize,
                                  TurnMagnitude)
from actions.car import Car


class InstructionStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Instruction:
    capability: str
    parameters: Dict[str, Any]
    status: InstructionStatus = InstructionStatus.PENDING
    error: Optional[str] = None


class InstructionExecutor:
    """Executes instructions sequentially with hand-the-baton style for mutually exclusive operations."""
    
    def __init__(self, car: Car, capabilities_registry: CapabilitiesRegistry):
        self.car = car
        self.capabilities = capabilities_registry
        self.current_instruction: Optional[Instruction] = None
        self.instruction_queue: List[Instruction] = []
        self.execution_lock = threading.Lock()
        self.is_running = False
        self.execution_thread: Optional[threading.Thread] = None
        self.active_follower = None
        
        # Speed mappings
        self.step_speeds = {
            StepSize.TINY: 0.2,
            StepSize.SMALL: 0.4,
            StepSize.LARGE: 0.6
        }
        self.step_durations = {
            StepSize.TINY: 0.3,
            StepSize.SMALL: 0.5,
            StepSize.LARGE: 0.8
        }
        self.turn_speeds = {
            TurnMagnitude.TINY: 0.2,
            TurnMagnitude.SMALL: 0.4,
            TurnMagnitude.LARGE: 0.6
        }
        self.turn_durations = {
            TurnMagnitude.TINY: 0.3,
            TurnMagnitude.SMALL: 0.5,
            TurnMagnitude.LARGE: 0.8
        }
        self.spin_speed = 0.5
        self.spin_duration = 0.5
    
    def add_instruction(self, capability: str, parameters: Dict[str, Any]) -> Instruction:
        """Add an instruction to the queue."""
        instruction = Instruction(capability=capability, parameters=parameters)
        with self.execution_lock:
            self.instruction_queue.append(instruction)
        return instruction
    
    def add_instructions(self, instructions: List[Dict[str, Any]]):
        """Add multiple instructions to the queue."""
        for inst in instructions:
            self.add_instruction(inst["capability"], inst.get("parameters", {}))
    
    def start(self):
        """Start the execution thread."""
        if not self.is_running:
            self.is_running = True
            self.execution_thread = threading.Thread(target=self._execution_loop, daemon=True)
            self.execution_thread.start()
    
    def stop(self):
        """Stop execution and clear queue."""
        self.is_running = False
        with self.execution_lock:
            self.instruction_queue.clear()
            self.current_instruction = None
            # Stop active follower if running
            if self.active_follower:
                self.active_follower.stop()
                self.active_follower = None
        self.car.drive(0, 0, 0)
    
    def _execution_loop(self):
        """Main execution loop that processes instructions sequentially."""
        while self.is_running:
            with self.execution_lock:
                if not self.instruction_queue:
                    time.sleep(0.1)
                    continue
                
                instruction = self.instruction_queue.pop(0)
                self.current_instruction = instruction
                instruction.status = InstructionStatus.RUNNING
            
            try:
                self._execute_instruction(instruction)
                instruction.status = InstructionStatus.COMPLETED
            except Exception as e:
                instruction.status = InstructionStatus.FAILED
                instruction.error = str(e)
                print(f"Instruction failed: {e}")
            finally:
                with self.execution_lock:
                    self.current_instruction = None
    
    def _execute_instruction(self, instruction: Instruction):
        """Execute a single instruction."""
        capability = instruction.capability
        params = instruction.parameters
        
        if capability == "make_step":
            self._execute_step(params)
        elif capability == "make_turn":
            self._execute_turn(params)
        elif capability == "spin_in_place":
            self._execute_spin(params)
        elif capability == "speak":
            self._execute_speak(params)
        elif capability == "take_picture":
            self._execute_take_picture(params)
        elif capability == "track_person":
            self._execute_track_person(params)
        elif capability == "follow_person":
            self._execute_follow_person(params)
        else:
            raise ValueError(f"Unknown capability: {capability}")
    
    def _execute_step(self, params: Dict[str, Any]):
        """Execute a step movement."""
        size = StepSize(params.get("size", "small"))
        direction = params.get("direction", "forward")
        
        speed = self.step_speeds[size]
        duration = self.step_durations[size]
        
        vy = speed if direction == "forward" else -speed
        
        self.car.drive(0, vy, 0)
        time.sleep(duration)
        self.car.drive(0, 0, 0)
    
    def _execute_turn(self, params: Dict[str, Any]):
        """Execute a turn movement."""
        direction = params.get("direction", "left")
        magnitude = TurnMagnitude(params.get("magnitude", "small"))
        
        rotation_speed = self.turn_speeds[magnitude]
        duration = self.turn_durations[magnitude]
        
        rotation = -rotation_speed if direction == "left" else rotation_speed
        
        # Turn while moving forward slightly
        self.car.drive(0, 0.3, rotation)
        time.sleep(duration)
        self.car.drive(0, 0, 0)
    
    def _execute_spin(self, params: Dict[str, Any]):
        """Execute an in-place spin."""
        direction = params.get("direction", "left")
        
        rotation = -self.spin_speed if direction == "left" else self.spin_speed
        
        self.car.drive(0, 0, rotation)
        time.sleep(self.spin_duration)
        self.car.drive(0, 0, 0)
    
    def _execute_speak(self, params: Dict[str, Any]):
        """Execute speak capability."""
        text = params.get("text", "")
        if text:
            from tts.speak import speak
            speak(text)
    
    def _execute_take_picture(self, params: Dict[str, Any]):
        """Execute take picture capability."""
        try:
            from datetime import datetime

            import cv2

            from actions.controllers.opencv_controller import OpenCVController
            
            camera = cv2.VideoCapture(0)
            if camera.isOpened():
                ret, frame = camera.read()
                if ret:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"picture_{timestamp}.jpg"
                    cv2.imwrite(filename, frame)
                    print(f"Picture saved: {filename}")
                camera.release()
            else:
                raise Exception("Camera not available")
        except Exception as e:
            print(f"Failed to take picture: {e}")
            raise
    
    def _execute_track_person(self, params: Dict[str, Any]):
        """Execute track person capability."""
        raise NotImplementedError("Person tracking not yet implemented")
    
    def _execute_follow_person(self, params: Dict[str, Any]):
        """Execute follow person capability using ArUco marker tracking."""
        from actions.aruco_follower import ArUcoFollower
        
        marker_id = params.get("marker_id", 0)
        target_distance = params.get("target_distance", 0.8)
        min_distance = params.get("min_distance", 0.3)
        
        follower = ArUcoFollower(
            car=self.car,
            marker_id=marker_id,
            target_distance=target_distance,
            min_distance=min_distance
        )
        
        if not follower.is_available():
            raise Exception("Camera not available for following")
        
        # Store follower reference for cancellation
        with self.execution_lock:
            self.active_follower = follower
        
        try:
            follower.start()
            print("Started following person. Say 'stop' to stop following.")
            
            # Keep following until stopped
            # The follower runs in its own thread, so we wait here
            # It will be stopped when the instruction is cancelled or a new instruction arrives
            while follower.running and self.is_running:
                # Check if we should stop (instruction cancelled or new instruction queued)
                with self.execution_lock:
                    if not self.is_running:
                        break
                    # Check if there's a new instruction that's not follow_person
                    if self.instruction_queue:
                        next_inst = self.instruction_queue[0]
                        if next_inst.capability != "follow_person":
                            break
                
                time.sleep(0.1)
            
        finally:
            follower.stop()
            with self.execution_lock:
                self.active_follower = None
            self.car.drive(0, 0, 0)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current execution status."""
        with self.execution_lock:
            return {
                "is_running": self.is_running,
                "queue_length": len(self.instruction_queue),
                "current_instruction": {
                    "capability": self.current_instruction.capability,
                    "status": self.current_instruction.status.value,
                    "error": self.current_instruction.error
                } if self.current_instruction else None
            }

