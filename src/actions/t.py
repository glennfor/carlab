import json
import os
import queue
import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from actions.car import Car


class StepSize(Enum):
    TINY = "tiny"
    SMALL = "small"
    LARGE = "large"


class Direction(Enum):
    LEFT = "left"
    RIGHT = "right"
    FORWARD = "forward"
    BACKWARD = "backward"


class TurnMagnitude(Enum):
    TINY = "tiny"
    SMALL = "small"
    LARGE = "large"


class InstructionStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Instruction:
    function_name: str
    parameters: Dict[str, Any]
    speech: Optional[str] = None
    status: InstructionStatus = InstructionStatus.PENDING
    error: Optional[str] = None
    subsystem: Optional[str] = None
    is_terminator: bool = False


class FunctionMapper:
    """Maps function names from planner to actual function implementations."""
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        self.function_map: Dict[str, Callable] = {}
    
    def _load_config(self) -> Dict[str, Any]:
        """Load function mappings from config.json."""
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            self.config_path
        )
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: {config_path} not found. Using defaults.")
            return {"function_mappings": {}, "subsystems": {}}
    
    def get_function_info(self, function_name: str) -> Optional[Dict[str, Any]]:
        """Get function information from config."""
        return self.config.get("function_mappings", {}).get(function_name)
    
    def get_subsystem(self, function_name: str) -> str:
        """Get subsystem for a function."""
        info = self.get_function_info(function_name)
        if info:
            return info.get("subsystem", "none")
        return "none"
    
    def is_terminator(self, function_name: str) -> bool:
        """Check if a function is a terminator."""
        info = self.get_function_info(function_name)
        if info:
            return info.get("is_terminator", False)
        return False
    
    def register_function(self, name: str, func: Callable):
        """Register a function implementation."""
        self.function_map[name] = func
    
    def get_function(self, name: str) -> Optional[Callable]:
        """Get a registered function."""
        return self.function_map.get(name)


class InstructionExecutor:
    """
    Executes instructions with separate queues for different subsystems.
    Supports terminator functions that execute immediately.
    """
    
    def __init__(self, car: Car, follower:ArUcoFollower, vocalizer:Vocalizer, llm:GoogleLLM):
        self.car = car
        self.follower = follower
        self.vocalizer = vocalizer
        self.llm = llm
        self.mapper = FunctionMapper()

        # command queue - this is the queue of commands that are received from the user and will
        # be processed by the llm and executed by the robot
        self.command_queue = queue.Queue()
        
        # Receiving queue - all instructions come here first
        # These are the actual instructions that are executed by the robot and are actionable
        self.receiving_queue = queue.Queue()
        
        # Subsystem queues and locks
        self.subsystem_queues: Dict[str, queue.Queue] = {}
        self.subsystem_locks: Dict[str, threading.Lock] = {}
        self.subsystem_threads: Dict[str, threading.Thread] = {}
        
        # Active operations tracking
        self.active_operations: Dict[str, Optional[Instruction]] = {}
        self.active_follower = None
        
        # Execution control
        self.is_running = False
        self.receiving_thread: Optional[threading.Thread] = None
        
        # Load subsystems from config
        self._initialize_subsystems()
        
        # Register all wrapper functions
        self._register_functions()
        
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
        self.default_speed = 0.5
    
    def _initialize_subsystems(self):
        """Initialize queues and locks for each subsystem."""
        subsystems = self.mapper.config.get("subsystems", {})
        
        for subsystem_name, subsystem_info in subsystems.items():
            queue_name = subsystem_info.get("queue_name", f"{subsystem_name}_queue")
            lock_name = subsystem_info.get("lock_name", f"{subsystem_name}_lock")
            
            self.subsystem_queues[subsystem_name] = queue.Queue()
            self.subsystem_locks[subsystem_name] = threading.Lock()
            self.active_operations[subsystem_name] = None
    
    def _register_functions(self):
        """Register all wrapper functions."""
        # Car control functions
        self.mapper.register_function("make_step", self._make_step)
        self.mapper.register_function("make_turn", self._make_turn)
        self.mapper.register_function("spin_in_place", self._spin_in_place)
        self.mapper.register_function("strafe", self._strafe)
        self.mapper.register_function("drive_forward", self._drive_forward)
        self.mapper.register_function("drive_backward", self._drive_backward)
        self.mapper.register_function("rotate", self._rotate)
        self.mapper.register_function("stop", self._stop)
        self.mapper.register_function("start_aruco_following", self._start_aruco_following)
        self.mapper.register_function("stop_aruco_following", self._stop_aruco_following)
        self.mapper.register_function("set_speed", self._set_speed)
        self.mapper.register_function("move_to_position", self._move_to_position)
        self.mapper.register_function("face_direction", self._face_direction)
        self.mapper.register_function("dance", self._dance)
        self.mapper.register_function("calibrate", self._calibrate)
        
        # Camera functions
        self.mapper.register_function("take_picture", self._take_picture)
        
        # Speech functions
        self.mapper.register_function("speak", self._speak)
        self.mapper.register_function("play_sound", self._play_sound)
        
        # General functions
        self.mapper.register_function("wait", self._wait)
        self.mapper.register_function("get_status", self._get_status)
    
    def add_instruction(self, function_name: str, parameters: Dict[str, Any], speech: Optional[str] = None) -> Instruction:
        """Add an instruction to the receiving queue."""
        subsystem = self.mapper.get_subsystem(function_name)
        is_terminator = self.mapper.is_terminator(function_name)
        
        instruction = Instruction(
            function_name=function_name,
            parameters=parameters,
            speech=speech,
            subsystem=subsystem,
            is_terminator=is_terminator
        )
        
        self.receiving_queue.put(instruction)
        return instruction
    
    def add_instructions(self, instructions: List[Dict[str, Any]], speech: Optional[str] = None):
        """Add multiple instructions to the receiving queue."""
        for inst in instructions:
            function_name = inst.get("function_name")
            params = inst.get("parameters", {})
            self.add_instruction(function_name, params, speech)
    
    def start(self):
        """Start the execution threads."""
        if not self.is_running:
            self.is_running = True
            
            # Start receiving thread
            self.receiving_thread = threading.Thread(target=self._receiving_loop, daemon=True)
            self.receiving_thread.start()
            
            # Start subsystem threads
            for subsystem_name in self.subsystem_queues.keys():
                thread = threading.Thread(
                    target=self._subsystem_loop,
                    args=(subsystem_name,),
                    daemon=True
                )
                self.subsystem_threads[subsystem_name] = thread
                thread.start()
    
    def stop(self):
        """Stop execution and clear all queues."""
        self.is_running = False
        
        # Stop active follower
        if self.active_follower:
            self.active_follower.stop()
            self.active_follower = None
        
        # Clear all queues
        while not self.receiving_queue.empty():
            try:
                self.receiving_queue.get_nowait()
            except queue.Empty:
                break
        
        for q in self.subsystem_queues.values():
            while not q.empty():
                try:
                    q.get_nowait()
                except queue.Empty:
                    break
        
        # Stop car
        self.car.drive(0, 0, 0)
    
    def add_command(self, command: str):
        """Add a command to the command queue."""
        self.command_queue.put(command)

    def _command_loop(self):
        """Main recives text commands from the user and adds them to the command queue for processing by the llm."""
        while self.is_running:
            try:
                command = self.command_queue.get(timeout=0.1)
                speech, function_calls = self.llm.respond(command)
                self.add_instructions(function_calls)
                # might need to remove this
                if speech:
                    self.vocalizer.queue(speech)
                self.command_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error in command loop: {e}")
    
    def _receiving_loop(self):
        """Main receiving loop that routes instructions to appropriate queues or executes terminators immediately."""
        while self.is_running:
            try:
                instruction = self.receiving_queue.get(timeout=0.1)
                
                # Check if it's a terminator - execute immediately
                if instruction.is_terminator:
                    self._execute_terminator(instruction)
                else:
                    # Route to appropriate subsystem queue
                    subsystem = instruction.subsystem or "none"
                    if subsystem in self.subsystem_queues:
                        self.subsystem_queues[subsystem].put(instruction)
                    else:
                        # Default to general queue
                        self.subsystem_queues.get("none", self.subsystem_queues["car_control"]).put(instruction)
                
                self.receiving_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error in receiving loop: {e}")
    
    def _execute_terminator(self, instruction: Instruction):
        """Execute a terminator function immediately, interrupting any active operations."""
        subsystem = instruction.subsystem or "none"
        
        # Acquire lock and interrupt active operation
        if subsystem in self.subsystem_locks:
            with self.subsystem_locks[subsystem]:
                # Stop active operation if any
                if subsystem == "car_control" and self.active_follower:
                    self.active_follower.stop()
                    self.active_follower = None
                
                # Execute terminator
                try:
                    instruction.status = InstructionStatus.RUNNING
                    func = self.mapper.get_function(instruction.function_name)
                    if func:
                        func(instruction.parameters)
                    instruction.status = InstructionStatus.COMPLETED
                except Exception as e:
                    instruction.status = InstructionStatus.FAILED
                    instruction.error = str(e)
                    print(f"Terminator failed: {e}")
    
    def _subsystem_loop(self, subsystem_name: str):
        """Process instructions for a specific subsystem."""
        subsystem_queue = self.subsystem_queues[subsystem_name]
        subsystem_lock = self.subsystem_locks[subsystem_name]
        
        while self.is_running:
            try:
                instruction = subsystem_queue.get(timeout=0.1)
                
                with subsystem_lock:
                    self.active_operations[subsystem_name] = instruction
                    instruction.status = InstructionStatus.RUNNING
                
                try:
                    # Execute the function
                    func = self.mapper.get_function(instruction.function_name)
                    if func:
                        func(instruction.parameters)
                    else:
                        raise ValueError(f"Function {instruction.function_name} not registered")
                    
                    instruction.status = InstructionStatus.COMPLETED
                    
                    # Handle speech if provided (speech can run concurrently)
                    if instruction.speech:
                        # Speech can run in parallel, so we add it to speech queue
                        speech_instruction = Instruction(
                            function_name="speak",
                            parameters={"text": instruction.speech},
                            subsystem="speech",
                            is_terminator=False
                        )
                        if "speech" in self.subsystem_queues:
                            self.subsystem_queues["speech"].put(speech_instruction)
                    
                except Exception as e:
                    instruction.status = InstructionStatus.FAILED
                    instruction.error = str(e)
                    print(f"Instruction failed: {e}")
                finally:
                    with subsystem_lock:
                        self.active_operations[subsystem_name] = None
                
                subsystem_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error in subsystem loop ({subsystem_name}): {e}")
    
    # ==================== WRAPPER FUNCTIONS ====================
    
    def _make_step(self, params: Dict[str, Any]):
        """Wrapper: Drive the car for a step at specified size."""
        size_str = params.get("size", "small")
        direction = params.get("direction", "forward")
        
        try:
            size = StepSize(size_str)
        except ValueError:
            size = StepSize.SMALL
        
        speed = self.step_speeds[size]
        duration = self.step_durations[size]
        
        vy = speed if direction == "forward" else -speed
        self.car.drive(0, vy, 0)
        time.sleep(duration)
        self.car.drive(0, 0, 0)
    
    def _make_turn(self, params: Dict[str, Any]):
        """Wrapper: Turn while moving forward."""
        direction = params.get("direction", "left")
        magnitude_str = params.get("magnitude", "small")
        
        try:
            magnitude = TurnMagnitude(magnitude_str)
        except ValueError:
            magnitude = TurnMagnitude.SMALL
        
        rotation_speed = self.turn_speeds[magnitude]
        duration = self.turn_durations[magnitude]
        rotation = -rotation_speed if direction == "left" else rotation_speed
        
        self.car.drive(0, 0.3, rotation)
        time.sleep(duration)
        self.car.drive(0, 0, 0)
    
    def _spin_in_place(self, params: Dict[str, Any]):
        """Wrapper: Spin in place."""
        direction = params.get("direction", "left")
        rotation = -self.spin_speed if direction == "left" else self.spin_speed
        
        self.car.drive(0, 0, rotation)
        time.sleep(self.spin_duration)
        self.car.drive(0, 0, 0)
    
    def _strafe(self, params: Dict[str, Any]):
        """Wrapper: Move sideways."""
        direction = params.get("direction", "left")
        duration = params.get("duration", 0.5)
        speed = params.get("speed", self.default_speed)
        
        vx = -speed if direction == "left" else speed
        self.car.drive(vx, 0, 0)
        time.sleep(duration)
        self.car.drive(0, 0, 0)
    
    def _drive_forward(self, params: Dict[str, Any]):
        """Wrapper: Drive forward at specified speed for duration."""
        speed_pct = params.get("speed", 50)
        duration = params.get("duration", 1.0)
        speed = (speed_pct / 100.0) * 0.6  # Convert to 0-0.6 range
        
        self.car.drive(0, speed, 0)
        time.sleep(duration)
        self.car.drive(0, 0, 0)
    
    def _drive_backward(self, params: Dict[str, Any]):
        """Wrapper: Drive backward at specified speed for duration."""
        speed_pct = params.get("speed", 50)
        duration = params.get("duration", 1.0)
        speed = (speed_pct / 100.0) * 0.6
        
        self.car.drive(0, -speed, 0)
        time.sleep(duration)
        self.car.drive(0, 0, 0)
    
    def _rotate(self, params: Dict[str, Any]):
        """Wrapper: Rotate in place."""
        direction = params.get("direction", "left")
        speed_pct = params.get("speed", 50)
        duration = params.get("duration", 1.0)
        rotation_speed = (speed_pct / 100.0) * 0.6
        
        rotation = -rotation_speed if direction == "left" else rotation_speed
        self.car.drive(0, 0, rotation)
        time.sleep(duration)
        self.car.drive(0, 0, 0)
    
    def _stop(self, params: Dict[str, Any]):
        """Terminator: Stop all movement immediately."""
        self.car.drive(0, 0, 0)
        if self.active_follower:
            self.active_follower.stop()
            self.active_follower = None
    
    def _start_aruco_following(self, params: Dict[str, Any]):
        """Wrapper: Start ArUco following."""
        import os
        import sys
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
        from vision.aruco_follower import ArUcoFollower
        
        marker_id = params.get("marker_id", 0)
        target_distance = params.get("target_distance", 0.15)
        
        follower = ArUcoFollower(
            car=self.car,
            marker_id=marker_id,
            target_distance=target_distance
        )
        
        if not follower.is_available():
            raise Exception("Camera not available for following")
        
        self.active_follower = follower
        follower.start()
        
        # Keep following until stopped
        while follower.running and self.is_running:
            time.sleep(0.1)
        
        follower.stop()
        self.active_follower = None
        self.car.drive(0, 0, 0)
    
    def _stop_aruco_following(self, params: Dict[str, Any]):
        """Terminator: Stop ArUco following immediately."""
        if self.active_follower:
            self.active_follower.stop()
            self.active_follower = None
        self.car.drive(0, 0, 0)
    
    def _set_speed(self, params: Dict[str, Any]):
        """Wrapper: Set default speed."""
        speed_pct = params.get("speed", 50)
        self.default_speed = (speed_pct / 100.0) * 0.6
    
    def _move_to_position(self, params: Dict[str, Any]):
        """Wrapper: Move to relative position (simplified - moves in steps)."""
        x = params.get("x", 0.0)
        y = params.get("y", 0.0)
        
        # Simplified: move in X then Y
        if abs(x) > 0.1:
            direction = "right" if x > 0 else "left"
            duration = min(abs(x) / 0.3, 2.0)  # Cap at 2 seconds
            self._strafe({"direction": direction, "duration": duration})
        
        if abs(y) > 0.1:
            direction = "forward" if y > 0 else "backward"
            duration = min(abs(y) / 0.3, 2.0)
            speed = self.default_speed
            if direction == "forward":
                self._drive_forward({"speed": speed * 100 / 0.6, "duration": duration})
            else:
                self._drive_backward({"speed": speed * 100 / 0.6, "duration": duration})
    
    def _face_direction(self, params: Dict[str, Any]):
        """Wrapper: Face a specific direction (simplified - just rotates)."""
        direction = params.get("direction", "forward")
        
        # Map directions to rotation
        if direction in ["left", "west"]:
            self._rotate({"direction": "left", "duration": 0.5})
        elif direction in ["right", "east"]:
            self._rotate({"direction": "right", "duration": 0.5})
        elif direction in ["backward", "south"]:
            self._rotate({"direction": "left", "duration": 1.0})
        # forward/north - no rotation needed
    
    def _dance(self, params: Dict[str, Any]):
        """Wrapper: Perform a dance sequence."""
        style = params.get("style", "spin")
        
        if style == "spin":
            for _ in range(3):
                self._spin_in_place({"direction": "left"})
                time.sleep(0.2)
                self._spin_in_place({"direction": "right"})
                time.sleep(0.2)
        elif style == "wiggle":
            for _ in range(4):
                self._strafe({"direction": "left", "duration": 0.2})
                self._strafe({"direction": "right", "duration": 0.2})
        elif style == "circle":
            for _ in range(2):
                self._drive_forward({"speed": 30, "duration": 0.5})
                self._rotate({"direction": "right", "duration": 0.5})
    
    def _calibrate(self, params: Dict[str, Any]):
        """Wrapper: Calibrate components."""
        component = params.get("component", "motors")
        # Placeholder - actual calibration would go here
        print(f"Calibrating {component}...")
        time.sleep(0.5)
    
    def _take_picture(self, params: Dict[str, Any]):
        """Wrapper: Take a picture using camera."""
        import os
        import sys
        from datetime import datetime
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
        from vision.camera import Camera
        
        filename = params.get("filename")
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"picture_{timestamp}.jpg"
        
        camera = Camera()
        try:
            camera.start()
            camera.capture_image(filename)
            print(f"Picture saved: {filename}")
        finally:
            camera.stop()
            camera.close()
    
    def _speak(self, text_or_params):
        if isinstance(text_or_params, dict):
            text = text_or_params.get("text", "")
        else:
            text = text_or_params
        
        if text:
            from tts.vocalizer import Vocalizer
            vocalizer = Vocalizer()
            vocalizer.speak(text)
    
    def _play_sound(self, params: Dict[str, Any]):
        """Wrapper: Play a sound (placeholder)."""
        sound = params.get("sound", "")
        print(f"Playing sound: {sound}")
        # Actual sound playback would go here
    
    def _wait(self, params: Dict[str, Any]):
        """Wrapper: Wait for duration."""
        duration = params.get("duration", 1.0)
        time.sleep(duration)
    
    def _get_status(self, params: Dict[str, Any]):
        """Wrapper: Get robot status."""
        return {
            "is_running": self.is_running,
            "active_operations": {
                k: v.function_name if v else None
                for k, v in self.active_operations.items()
            },
            "queue_sizes": {
                k: q.qsize() for k, q in self.subsystem_queues.items()
            },
            "receiving_queue_size": self.receiving_queue.qsize()
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current execution status."""
        return {
            "is_running": self.is_running,
            "active_operations": {
                k: {
                    "function": v.function_name,
                    "status": v.status.value,
                    "error": v.error
                } if v else None
                for k, v in self.active_operations.items()
            },
            "queue_sizes": {
                k: q.qsize() for k, q in self.subsystem_queues.items()
            },
            "receiving_queue_size": self.receiving_queue.qsize()
        }
