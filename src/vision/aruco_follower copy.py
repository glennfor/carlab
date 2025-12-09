import os
import sys
import threading
import time
from typing import Optional, Tuple
from picamera2 import Picamera2

import cv2
import numpy as np

# Add src directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# from actions.car import Car

from actions.car import Car


class ArUcoFollower:
    """
    Follows a person using ArUco marker detection.
    
    The person holds an ArUco marker, and the car tracks and follows them.
    Stops when close enough or when instructed to stop.
    """
    
    def __init__(
        self,
        car: Car,
        camera_index: int = 0,
        marker_id: int = 0,
        marker_size: float = 0.05,
        min_distance: float = 0.3,
        max_distance: float = 2.0,
        target_distance: float = 0.8,
        max_forward_speed: float = 0.4,
        max_rotation_speed: float = 0.5,
        center_tolerance: int = 30
    ):
        """
        Initialize the ArUco follower.
        
        :param car: Car instance to control
        :param camera_index: Camera device index
        :param marker_id: ArUco marker ID to track (0-249)
        :param marker_size: Physical size of marker in meters (for distance estimation)
        :param min_distance: Minimum safe distance in meters (stops if closer)
        :param max_distance: Maximum tracking distance in meters
        :param target_distance: Target following distance in meters
        :param max_forward_speed: Maximum forward/backward speed
        :param max_rotation_speed: Maximum rotation speed
        :param center_tolerance: Pixel tolerance for centering (stops rotating if within)
        """
        self.car = car
        self.camera_index = camera_index
        self.marker_id = marker_id
        self.marker_size = marker_size
        self.min_distance = min_distance
        self.max_distance = max_distance
        self.target_distance = target_distance
        self.max_forward_speed = max_forward_speed
        self.max_rotation_speed = max_rotation_speed
        self.center_tolerance = center_tolerance
        
        self.camera: Optional[cv2.VideoCapture] = None
        self.running = False
        self.should_stop = False
        self.follow_thread: Optional[threading.Thread] = None
        
        # ArUco detector
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        self.aruco_params = cv2.aruco.DetectorParameters()
        
        # Try to use newer API (OpenCV 4.7+), fallback to older API
        try:
            self.detector = cv2.aruco.ArucoDetector(self.aruco_dict, self.aruco_params)
            self.use_new_api = True
        except AttributeError:
            # Older OpenCV version
            self.detector = None
            self.use_new_api = False
        
        # Camera calibration (simplified - assumes standard webcam)
        # In production, you should calibrate your camera
        self.camera_matrix = None
        self.dist_coeffs = None
        self._init_camera_calibration()
    
    def _init_camera_calibration(self):
        """
        Initialize camera calibration parameters.
        
        For a real implementation, you should calibrate your specific camera.
        This uses a simplified model assuming a standard webcam.
        """
        # Simplified calibration - assumes 640x480 camera
        # In production, use cv2.calibrateCamera() with checkerboard images
        focal_length = 640.0
        self.camera_matrix = np.array([
            [focal_length, 0, 320],
            [0, focal_length, 240],
            [0, 0, 1]
        ], dtype=np.float32)
        self.dist_coeffs = np.zeros((4, 1), dtype=np.float32)
    
    def start(self):
        """Start the follower."""
        if self.running:
            return
        
        try:
            self.camera = cv2.VideoCapture(self.camera_index)
            self.camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'BGR3'))
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

            # self.camera = cv2.VideoCapture(self.camera_index)
            # self.camera = cv2.VideoCapture(self.camera_index, cv2.CAP_V4L2)
            # self.camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))

            if not self.camera.isOpened():
                raise Exception("Camera not available")

            
            # self.camera.set(cv2.CAP_PROP_FPS, 15)

            
            # # Set camera resolution
            # self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            # self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            self.running = True
            self.should_stop = False
            self.follow_thread = threading.Thread(target=self._follow_loop, daemon=True)
            self.follow_thread.start()
            
        except Exception as e:
            print(f"Failed to start ArUco follower: {e}")
            self.running = False
            if self.camera:
                self.camera.release()
                self.camera = None
        print('[1] Starting Eye')
    def stop(self):
        """Stop the follower."""
        self.should_stop = True
        self.running = False
        
        if self.follow_thread and self.follow_thread.is_alive():
            self.follow_thread.join(timeout=2.0)
        
        if self.camera:
            self.camera.release()
            self.camera = None
        
        # Stop the car
        self.car.drive(0, 0, 0)
    
    def _follow_loop(self):
        """Main following loop."""
        print('[2] Starting following loop')
        last_seen_time = time.time()

        marker_lost_timeout = 2.0

        # debug
        last_print_time = time.time()
        print_interval = 1.0
        
        while self.running and not self.should_stop:
            ret, frame = self.camera.read()
            if not ret:
                print("Could not capture for some reason")
                time.sleep(0.1)
                continue
            
            if not ret or frame is None:
                print("Camera returned NULL frame. Stopping safely.")
                break
            
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_YUV2BGR_YUYV)

            # Detect ArUco markers
            marker_found, distance, center_x, center_y = self._detect_marker(frame)
            
            if marker_found:
                last_seen_time = time.time()
                
                # Check if too close (collision avoidance)
                if distance < self.min_distance:
                    self.car.drive(0, 0, 0)
                    print(f"Too close! Distance: {distance:.2f}m (min: {self.min_distance:.2f}m)")
                    time.sleep(0.1)
                    continue
                
                # Check if too far
                if distance > self.max_distance:
                    print(f"Marker too far: {distance:.2f}m (max: {self.max_distance:.2f}m)")
                    self.car.drive(0, 0, 0)
                    time.sleep(0.1)
                    continue
                
                # Calculate control commands
                frame_center_x = frame.shape[1] // 2
                frame_center_y = frame.shape[0] // 2
                
                error_x = center_x - frame_center_x
                error_y = center_y - frame_center_y
                
                # Rotation control (center horizontally)
                if abs(error_x) > self.center_tolerance:
                    rotation = -np.clip(error_x * 0.002, -self.max_rotation_speed, self.max_rotation_speed)
                else:
                    rotation = 0
                
                # Forward/backward control (maintain target distance)
                distance_error = distance - self.target_distance
                if abs(distance_error) > 0.1:  # 10cm tolerance
                    if distance_error > 0:
                        # Too far, move forward
                        vy = np.clip(distance_error * 0.3, 0, self.max_forward_speed)
                    else:
                        # Too close, move backward slowly
                        vy = np.clip(distance_error * 0.2, -self.max_forward_speed * 0.5, 0)
                else:
                    vy = 0
                
                # debug
                if time.time() - last_print_time > print_interval:
                    print(f"Distance: {distance:.2f}m, Error: {error_x:.2f}px, Rotation: {rotation:.2f}rad, Forward: {vy:.2f}m/s")
                    last_print_time = time.time()
                
                # Apply control
                self.car.drive(0, vy, rotation)
                
            else:
                # Marker not found
                time_since_last_seen = time.time() - last_seen_time
                
                if time_since_last_seen > marker_lost_timeout:
                    # Lost marker for too long, stop
                    self.car.drive(0, 0, 0)
                    print("Marker lost, stopping...")
                
                time.sleep(0.1)
            
            time.sleep(0.05)  # ~20 Hz update rate
    
    def _detect_marker(self, frame) -> Tuple[bool, float, int, int]:
        """
        Detect ArUco marker in frame.
        
        :return: (found, distance, center_x, center_y)
        """

        print('Checking ...')
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect markers
        if self.use_new_api:
            corners, ids, _ = self.detector.detectMarkers(gray)
        else:
            # Older OpenCV API
            corners, ids, _ = cv2.aruco.detectMarkers(
                gray, self.aruco_dict, parameters=self.aruco_params
            )
        
        if ids is None or len(ids) == 0:
            return False, 0.0, 0, 0
        
        # Find the target marker
        target_idx = None
        for i, marker_id in enumerate(ids.flatten()):
            if marker_id == self.marker_id:
                target_idx = i
                break
        
        if target_idx is None:
            return False, 0.0, 0, 0
        
        # Get marker corners
        marker_corners = corners[target_idx][0]
        
        # Calculate center
        center_x = int(np.mean(marker_corners[:, 0]))
        center_y = int(np.mean(marker_corners[:, 1]))
        
        # Estimate distance from marker size
        # Use the average edge length of the marker
        edge_lengths = [
            np.linalg.norm(marker_corners[0] - marker_corners[1]),
            np.linalg.norm(marker_corners[1] - marker_corners[2]),
            np.linalg.norm(marker_corners[2] - marker_corners[3]),
            np.linalg.norm(marker_corners[3] - marker_corners[0])
        ]
        avg_pixel_size = np.mean(edge_lengths)
        
        # Estimate distance: distance = (focal_length * real_size) / pixel_size
        # Simplified: assuming focal_length ~ 640 pixels for 640x480 camera
        focal_length = self.camera_matrix[0, 0]
        distance = (focal_length * self.marker_size) / avg_pixel_size
        
        return True, distance, center_x, center_y
    
    def is_available(self) -> bool:
        """Check if camera is available."""
        try:
            cap = cv2.VideoCapture(self.camera_index)
            available = cap.isOpened()
            cap.release()
            return available
        except:
            return False

