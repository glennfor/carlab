import os
import random
import sys
import threading
import time
from typing import Optional, Tuple

from picamera2 import Picamera2
import cv2
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from actions.car import Car


class ArUcoFollower:
    """
    Follows a person holding an ArUco marker using **3D pose estimation**.
    Uses tx, tz from OpenCV to control forward motion and rotation.
    """

    def __init__(
        self,
        car: Car,
        marker_id: int = 0,
        marker_size: float = 0.05,  # meters
        min_distance: float = 0.15,
        max_distance: float = 2.0,
        target_distance: float = 0.8,
        max_forward_speed: float = 0.4,
        max_rotation_speed: float = 0.5,
    ):
        self.car = car
        self.marker_id = marker_id
        self.marker_size = marker_size
        self.min_distance = min_distance
        self.max_distance = max_distance
        self.target_distance = target_distance
        self.max_forward_speed = max_forward_speed
        self.max_rotation_speed = max_rotation_speed

        self.picam2: Optional[Picamera2] = None
        self.running = False
        self.should_stop = False
        self.follow_thread: Optional[threading.Thread] = None

        # ArUco detector
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_50)
        self.aruco_params = cv2.aruco.DetectorParameters()

        # Better detection under glare
        self.aruco_params.adaptiveThreshWinSizeMin = 3
        self.aruco_params.adaptiveThreshWinSizeMax = 50
        self.aruco_params.adaptiveThreshWinSizeStep = 5
        self.aruco_params.errorCorrectionRate = 0.8

        try:
            self.detector = cv2.aruco.ArucoDetector(self.aruco_dict, self.aruco_params)
            self.use_new_api = True
        except AttributeError:
            self.detector = None
            self.use_new_api = False

        # Camera calibration (approx)
        focal_length = 640.0
        self.camera_matrix = np.array([
            [focal_length, 0, 320],
            [0, focal_length, 240],
            [0, 0, 1]
        ], dtype=np.float32)
        self.dist_coeffs = np.zeros((4, 1), dtype=np.float32)

    # -------------------------------------------------------
    # Start/Stop
    # -------------------------------------------------------

    def start(self):
        if self.running:
            return

        try:
            self.picam2 = Picamera2()
            self.picam2.configure(
                self.picam2.create_preview_configuration(
                    main={"format": "RGB888", "size": (640, 480)}
                )
            )
            self.picam2.start()

            self.running = True
            self.should_stop = False
            self.follow_thread = threading.Thread(target=self._follow_loop, daemon=True)
            self.follow_thread.start()

        except Exception as e:
            print(f"Failed to start ArUco follower: {e}")
            if self.picam2:
                self.picam2.close()
            self.picam2 = None
            self.running = False

        print('[1] Starting Eye')

    def stop(self):
        self.should_stop = True
        self.running = False

        if self.follow_thread and self.follow_thread.is_alive():
            self.follow_thread.join(timeout=2.0)

        if self.picam2:
            self.picam2.close()
            self.picam2 = None

        self.car.drive(0, 0, 0)

    # -------------------------------------------------------
    # FOLLOW LOOP
    # -------------------------------------------------------

    def _follow_loop(self):
        print('[2] Starting following loop')
        last_seen = time.time()
        lost_timeout = 2.0

        while self.running and not self.should_stop:
            frame = self.picam2.capture_array()
            if frame is None:
                print("Camera returned NULL frame.")
                break

            found, tvec = self._detect_marker_pose(frame)

            if found:
                last_seen = time.time()

                tx, ty, tz = tvec.flatten()

                # --- Ensure valid forward distance ---
                if tz < self.min_distance:
                    self.car.drive(0, 0, 0)
                    continue

                # ---- Forward speed using real 3D tz ----
                distance_error = tz - self.target_distance
                vy = np.clip(distance_error * 0.8, 
                             -self.max_forward_speed, 
                             self.max_forward_speed)

                # ---- Rotation using lateral offset ----
                angle_error = np.arctan2(tx, tz)
                rotation = np.clip(angle_error * 2.0,
                                   -self.max_rotation_speed,
                                   self.max_rotation_speed)

                # Debug print sometimes
                if random.random() > 0.92:
                    print(f"tz={tz:.2f}m  tx={tx:.2f}m  vy={vy:.2f}  rot={rotation:.2f}")

                # Drive robot
                self.car.drive(0, vy, rotation)

            else:
                # If lost for a while, stop safely
                if time.time() - last_seen > lost_timeout:
                    self.car.drive(0, 0, 0)
                time.sleep(0.1)

            time.sleep(0.03)

    # -------------------------------------------------------
    # POSE DETECTION
    # -------------------------------------------------------

    def _detect_marker_pose(self, frame) -> Tuple[bool, Optional[np.ndarray]]:
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)

        # ArUco detection
        if self.use_new_api:
            corners, ids, _ = self.detector.detectMarkers(gray)
        else:
            corners, ids, _ = cv2.aruco.detectMarkers(gray, self.aruco_dict, self.aruco_params)

        if ids is None or len(ids) == 0:
            return False, None

        # Find correct marker
        for i, mid in enumerate(ids.flatten()):
            if mid == self.marker_id:
                marker_corners = corners[i]
                break
        else:
            return False, None

        # ---- 3D pose estimation ----
        rvec, tvec, _ = cv2.aruco.estimatePoseSingleMarkers(
            marker_corners,
            self.marker_size,
            self.camera_matrix,
            self.dist_coeffs
        )

        return True, tvec[0][0]  # return (tx,ty,tz)

    # -------------------------------------------------------

    def is_available(self) -> bool:
        try:
            c = Picamera2()
            c.start()
            c.close()
            return True
        except:
            return False
