import os
import sys
import threading
import time
from typing import Optional, Tuple
import random

from picamera2 import Picamera2, Preview
import cv2
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
        marker_id: int = 0,
        marker_size: float = 0.05,
        min_distance: float = 0.15,# m
        max_distance: float = 2.0, #
        target_distance: float = 0.8,
        max_forward_speed: float = 0.4,
        max_rotation_speed: float = 0.5,
        center_tolerance: int = 30
    ):
        """
        Initialize the ArUco follower.
        """
        self.car = car
        self.marker_id = marker_id
        self.marker_size = marker_size
        self.min_distance = min_distance
        self.max_distance = max_distance
        self.target_distance = target_distance
        self.max_forward_speed = max_forward_speed
        self.max_rotation_speed = max_rotation_speed
        self.center_tolerance = center_tolerance
        
        self.picam2: Optional[Picamera2] = None
        self.running = False
        self.should_stop = False
        self.follow_thread: Optional[threading.Thread] = None
        
        # ArUco detector
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_50)
        self.aruco_params = cv2.aruco.DetectorParameters()

        # 1. Adaptive Thresholding: 
        # Look at a wider range of window sizes. This helps if the glare dominates small windows.
        self.aruco_params.adaptiveThreshWinSizeMin = 3
        self.aruco_params.adaptiveThreshWinSizeMax = 50  # Increase max window size
        self.aruco_params.adaptiveThreshWinSizeStep = 5 

        # 2. Error Correction:
        # Increase the error correction rate. ArUco has redundancy; this tells it 
        # to "guess" more aggressively if a few bits (like the ones under glare) are wrong.
        self.aruco_params.errorCorrectionRate = 0.8  # Default is usually around 0.6

        # Sometimes the bits are read wrong because the corner detection was slightly off due to the glare edge.
        # This tells OpenCV to spend more time aligning the grid perfectly before reading the bits.
        # self.aruco_params.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX

        try:
            self.detector = cv2.aruco.ArucoDetector(self.aruco_dict, self.aruco_params)
            self.use_new_api = True
        except AttributeError:
            self.detector = None
            self.use_new_api = False
        
        # Camera calibration
        self.camera_matrix = None
        self.dist_coeffs = None
        self._init_camera_calibration()
    
    def _init_camera_calibration(self):
        focal_length = 640.0
        self.camera_matrix = np.array([
            [focal_length, 0, 320],
            [0, focal_length, 240],
            [0, 0, 1]
        ], dtype=np.float32)
        self.dist_coeffs = np.zeros((4, 1), dtype=np.float32)
    
    def start(self):
        """Start the follower using Picamera2."""
        if self.running:
            return

        try:
            self.picam2 = Picamera2()
            self.picam2.configure(self.picam2.create_preview_configuration(main={"format": "RGB888", "size": (640, 480)}))
            self.picam2.start()
            
            self.running = True
            self.should_stop = False
            self.follow_thread = threading.Thread(target=self._follow_loop, daemon=True)
            self.follow_thread.start()
            
        except Exception as e:
            print(f"Failed to start ArUco follower: {e}")
            self.running = False
            if self.picam2:
                self.picam2.close()
                self.picam2 = None
        print('[1] Starting Eye')
    
    def stop(self):
        """Stop the follower."""
        self.should_stop = True
        self.running = False
        
        if self.follow_thread and self.follow_thread.is_alive():
            self.follow_thread.join(timeout=2.0)
        
        if self.picam2:
            self.picam2.close()
            self.picam2 = None
        
        self.car.drive(0, 0, 0)
    
    def _follow_loop(self):
        """Main following loop."""
        print('[2] Starting following loop')
        last_seen_time = time.time()
        marker_lost_timeout = 2.0
        last_print_time = time.time()
        print_interval = 1.0
        
        while self.running and not self.should_stop:
            frame = self.picam2.capture_array()
            if frame is None:
                print("Camera returned NULL frame. Stopping safely.")
                break
            
            marker_found, distance, center_x, center_y = self._detect_marker(frame)
            
            if marker_found:
                print('Marker Seen')
                last_seen_time = time.time()
                
                if distance < self.min_distance:
                    self.car.drive(0, 0, 0)
                    time.sleep(0.1)
                    continue
                
                if distance > self.max_distance:
                    # self.car.drive(0, 0, 0)
                    # print(f"Marker too far: {distance:.2f}m")
                    # time.sleep(0.1)
                    # continue
                    pass
                
                frame_center_x = frame.shape[1] // 2
                error_x = center_x - frame_center_x
                
                rotation = -np.clip(error_x * 0.002, -self.max_rotation_speed, self.max_rotation_speed) if abs(error_x) > self.center_tolerance else 0
                distance_error = distance - self.target_distance
                if abs(distance_error) > 0.1:
                    vy = np.clip(distance_error * 0.3, 0, self.max_forward_speed) if distance_error > 0 else np.clip(distance_error * 0.2, -self.max_forward_speed * 0.5, 0)
                else:
                    vy = 0
                
                if random.random() > 0.9:
                    print(f"Distance: {distance:.2f}m, Error: {error_x}px, Rotation: {rotation:.2f}, Forward: {vy:.2f}")
                    last_print_time = time.time()
                
                self.car.drive(0, vy, rotation)
            else:
                if time.time() - last_seen_time > marker_lost_timeout:
                    self.car.drive(0, 0, 0)
                    # print("Marker lost, stopping...")
                time.sleep(0.1)
            
            time.sleep(0.05)
    
    def _detect_marker(self, frame) -> Tuple[bool, float, int, int]:
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        if self.use_new_api:
            corners, ids, _ = self.detector.detectMarkers(gray)
        else:
            corners, ids, _ = cv2.aruco.detectMarkers(gray, self.aruco_dict, parameters=self.aruco_params)
        
        if ids is None or len(ids) == 0:
            return False, 0.0, 0, 0
        
        target_idx = None
        for i, marker_id in enumerate(ids.flatten()):
            if marker_id == self.marker_id:
                target_idx = i
                break
        
        if target_idx is None:
            return False, 0.0, 0, 0
        
        marker_corners = corners[target_idx][0]
        center_x = int(np.mean(marker_corners[:, 0]))
        center_y = int(np.mean(marker_corners[:, 1]))
        
        edge_lengths = [
            np.linalg.norm(marker_corners[0] - marker_corners[1]),
            np.linalg.norm(marker_corners[1] - marker_corners[2]),
            np.linalg.norm(marker_corners[2] - marker_corners[3]),
            np.linalg.norm(marker_corners[3] - marker_corners[0])
        ]
        avg_pixel_size = np.mean(edge_lengths)
        focal_length = self.camera_matrix[0, 0]
        distance = (focal_length * self.marker_size) / avg_pixel_size
        
        return True, distance, center_x, center_y
    
    def is_available(self) -> bool:
        """Check if Picamera2 is available."""
        try:
            test_cam = Picamera2()
            test_cam.start()
            test_cam.close()
            return True
        except:
            return False



# If you use a printed marker, OpenCV can compute exact distance from:

# marker corner locations

# camera calibration matrix

# OpenCV literally gives you a 3D pose:

# rvec, tvec = cv2.aruco.estimatePoseSingleMarkers(...)