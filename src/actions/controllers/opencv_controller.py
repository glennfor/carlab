from typing import Optional

import cv2

from actions.controllers.base_controller import BaseController, ControlCommand


class OpenCVController(BaseController):
    """Controller implementation for OpenCV-based vision control."""
    
    def __init__(self, camera_index: int = 0, priority: int = 30):
        """
        Initialize OpenCV vision controller.
        
        :param camera_index: Camera device index
        :param priority: Priority level (default 30, lower than gamepad/keyboard)
        """
        super().__init__(name="OpenCV Vision", priority=priority)
        self.camera_index = camera_index
        self.camera = None
        self.running = False
        
        self.target_center_x = 320
        self.target_center_y = 240
        self.max_speed = 0.5
        self.rotation_gain = 0.001
        self.translation_gain = 0.001
    
    def _process_frame(self, frame) -> Optional[ControlCommand]:
        """
        Process a camera frame and generate control command.
        
        This is a placeholder implementation. Override or extend for specific vision tasks.
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None
        
        largest_contour = max(contours, key=cv2.contourArea)
        M = cv2.moments(largest_contour)
        
        if M["m00"] == 0:
            return None
        
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])
        
        frame_center_x = frame.shape[1] // 2
        frame_center_y = frame.shape[0] // 2
        
        error_x = cx - frame_center_x
        error_y = cy - frame_center_y
        
        cmd = ControlCommand(
            vx=error_x * self.translation_gain,
            vy=error_y * self.translation_gain,
            rotation=error_x * self.rotation_gain
        )
        
        cmd.vx = max(-self.max_speed, min(self.max_speed, cmd.vx))
        cmd.vy = max(-self.max_speed, min(self.max_speed, cmd.vy))
        cmd.rotation = max(-self.max_speed, min(self.max_speed, cmd.rotation))
        
        return cmd
    
    def start(self):
        """Start the OpenCV controller."""
        if self.is_available():
            try:
                self.camera = cv2.VideoCapture(self.camera_index)
                if not self.camera.isOpened():
                    self.is_active = False
                    return
                self.running = True
                self.is_active = True
            except Exception as e:
                print(f"Failed to start OpenCV controller: {e}")
                self.is_active = False
        else:
            self.is_active = False
    
    def stop(self):
        """Stop the OpenCV controller."""
        self.running = False
        if self.camera:
            self.camera.release()
            self.camera = None
        self.is_active = False
    
    def get_command(self) -> Optional[ControlCommand]:
        """Get current control command from vision processing."""
        if not self.is_active or not self.camera:
            return None
        
        ret, frame = self.camera.read()
        if not ret:
            return None
        
        return self._process_frame(frame)
    
    def capture_frame(self):
        """Capture a single frame from the camera."""
        if self.camera and self.camera.isOpened():
            ret, frame = self.camera.read()
            if ret:
                return frame
        return None
    
    def is_available(self) -> bool:
        """Check if camera is available."""
        try:
            cap = cv2.VideoCapture(self.camera_index)
            available = cap.isOpened()
            cap.release()
            return available
        except:
            return False

