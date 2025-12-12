import os
import random
import signal
import sys
import threading
import time
import math
import cv2
import numpy as np
from picamera2 import Picamera2
from typing import Optional, Tuple

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from actions.car import Car


class PIDController:
    """Simple PID controller for distance and angle control."""
    
    def __init__(self, kp: float, ki: float, kd: float, max_output: float = float('inf')):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.max_output = max_output
        
        self.integral = 0.0
        self.last_error = 0.0
        self.last_time = None
    
    def update(self, error: float, dt: float) -> float:
        """Update PID controller and return output."""
        if self.last_time is None:
            self.last_time = time.time()
            self.last_error = error
            return 0.0
        
        # Proportional term
        p_term = self.kp * error
        
        # Integral term
        self.integral += error * dt
        i_term = self.ki * self.integral
        
        # Derivative term
        d_term = self.kd * (error - self.last_error) / dt if dt > 0 else 0.0
        
        # Compute output
        output = p_term + i_term + d_term
        
        # Clamp output
        output = np.clip(output, -self.max_output, self.max_output)
        
        # Update state
        self.last_error = error
        
        return output
    
    def reset(self):
        """Reset PID controller state."""
        self.integral = 0.0
        self.last_error = 0.0
        self.last_time = None



def estimate_pose_single_markers(corners, marker_length, camera_matrix, dist_coeffs):
    """
    Custom re-implementation of cv2.aruco.estimatePoseSingleMarkers
    """
    # 3D points of marker corners in marker coordinate frame
    half = marker_length / 2.0
    obj_points = np.array([
        [-half,  half, 0],  # top-left
        [ half,  half, 0],  # top-right
        [ half, -half, 0],  # bottom-right
        [-half, -half, 0]   # bottom-left
    ], dtype=np.float32)

    rvecs = []
    tvecs = []

    for c in corners:
        # c shape: (1, 4, 2) → we need (4, 2)
        img_points = c.reshape(4, 2)

        success, rvec, tvec = cv2.solvePnP(
            obj_points,
            img_points,
            camera_matrix,
            dist_coeffs,
            flags=cv2.SOLVEPNP_IPPE_SQUARE  # best for planar square markers
        )

        if not success:
            raise RuntimeError("solvePnP failed for a marker")

        rvecs.append(rvec)
        tvecs.append(tvec)

    return np.array(rvecs), np.array(tvecs)

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
        target_distance: float = 0.15,
        max_forward_speed: float = 0.4,
        max_rotation_speed: float = 0.5,
        # PID gains for distance control
        distance_kp: float = 1.0,
        distance_ki: float = 0.1,
        distance_kd: float = 0.05,
        # PID gains for angle control
        angle_kp: float = 1.0,
        angle_ki: float = 0.05,
        angle_kd: float = 0.1,
    ):
        self.car = car
        self.marker_id = marker_id
        self.marker_size = marker_size
        self.target_distance = target_distance
        self.max_forward_speed = max_forward_speed
        self.max_rotation_speed = max_rotation_speed

        # Initialize PID controllers
        self.distance_pid = PIDController(
            kp=distance_kp,
            ki=distance_ki,
            kd=distance_kd,
            max_output=max_forward_speed
        )
        self.angle_pid = PIDController(
            kp=angle_kp,
            ki=angle_ki,
            kd=angle_kd,
            max_output=max_rotation_speed
        )

        self.picam2: Optional[Picamera2] = None
        self.running = False
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
        width  = 640 # frame width
        height = 480 # frame height

        HFOV = math.radians(66)  # horizontal FOV
        VFOV = math.radians(41)  # vertical FOV
        # focal length
        fx = width  / (2 * math.tan(HFOV / 2))
        fy = height / (2 * math.tan(VFOV / 2))

        # principal point
        cx = width  / 2
        cy = height / 2

        # camera matrix
        self.camera_matrix = np.array([
            [fx,  0, cx],
            [ 0, fy, cy],
            [ 0,  0,  1]
        ], dtype=np.float32)

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

    def run(self):
        self.running = True

        try:
            self.picam2 = Picamera2()
            self.picam2.configure(
                self.picam2.create_preview_configuration(
                    main={"format": "RGB888", "size": (640, 480)}
                )
            )
            self.picam2.start()

            # Start the follow loop 
            self._follow_loop()

        except Exception as e:
            print(f"Failed to start ArUco follower: {e}")
            if self.picam2:
                self.picam2.close()
            self.picam2 = None
            self.running = False

    def stop(self):
        self.running = False
        if self.picam2:
            self.picam2.close()
            self.picam2 = None
        self.car.drive(0, 0, 0)

    # -------------------------------------------------------
    # FOLLOW LOOP
    # -------------------------------------------------------

    def _follow_loop(self):
        last_seen = time.time()
        lost_timeout = 1.0
        last_update_time = time.time()

        while self.running:
            current_time = time.time()
            dt = current_time - last_update_time
            last_update_time = current_time

            frame = self.picam2.capture_array()
            if frame is None:
                print("Camera returned NULL frame.")
                break

            found, tvec = self._detect_marker_pose(frame)

            if found:
                last_seen = time.time()

                tx, ty, tz = tvec.flatten()

                # --- Ensure valid forward distance ---
                if tz < self.target_distance:
                    self.car.drive(0, 0, 0)
                    # self.distance_pid.reset()
                    self.angle_pid.reset()
                    continue

                # ---- Forward speed using PID control on distance ----
                distance_error = tz - self.target_distance
                vy = self.distance_pid.update(distance_error, dt)

                # ---- Rotation using PID control on angle ----
                angle_error = tx#np.arctan2(tx, tz)
                rotation = self.angle_pid.update(angle_error, dt)

                # Debug print sometimes
                if random.random() > 0.75:
                    print(f"tz={tz:.2f}m  ty={ty:.2f}m  tx={tx:.2f}m  vy={vy:.2f}  rot={rotation:.2f}  "
                          f"dist_err={distance_error:.3f}  angle_err={angle_error:.3f}")

                # Drive robot
                self.car.drive(0, vy, rotation)

            else:
                # If lost for a while, stop safely and reset PID controllers
                if time.time() - last_seen > lost_timeout:
                    self.car.drive(0, 0, 0)
                    self.distance_pid.reset()
                    self.angle_pid.reset()
                time.sleep(0.1)

            time.sleep(0.01)

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
        # rvec, tvec, _ = cv2.aruco.estimatePoseSingleMarkers(
        #     marker_corners,
        #     self.marker_size,
        #     self.camera_matrix,
        #     self.dist_coeffs
        # )

        # return True, tvec[0][0]  # return (tx,ty,tz)
        

        # rvecs, tvecs, _ = cv2.aruco.estimatePoseSingleMarkers(
        #     [marker_corners],
        #     self.marker_size,
        #     self.camera_matrix,
        #     self.dist_coeffs
        # )
        rvecs, tvecs = estimate_pose_single_markers(
            [marker_corners],
            self.marker_size,
            self.camera_matrix,
            self.dist_coeffs
        )
        # Return (tx, ty, tz)
        return True, tvecs[0].flatten()
        # return True, tvecs[0]  # return (tx, ty, tz)
        # return True, tvecs[0][0]  # return (tx, ty, tz)

    # -------------------------------------------------------

    def is_available(self) -> bool:
        try:
            c = Picamera2()
            c.start()
            c.close()
            return True
        except:
            return False



def signal_handler(sig, frame, car, follower):
    """Handle shutdown signals."""
    print("\nShutting down...")
    if follower:
        follower.stop()
    car.drive(0, 0, 0)
    car.cleanup()
    sys.exit(0)

if __name__ == "__main__":
    
    """Test ArUco following."""
    print("ArUco Follower Test")
    print("=" * 50)
    print("Make sure you have an ArUco marker (ID 0, DICT_6X6_50)")
    print("Hold it in front of the camera to start following")
    print("Press Ctrl+C to stop")
    print("=" * 50, cv2.__version__)
    
    car = Car()
    follower = ArUcoFollower(
        car=car,
        marker_id=0,
        target_distance=0.05,
        # distance control
        distance_kp=0.8,
        distance_ki=0.00,
        distance_kd=0.00,
        # angle control
        angle_kp=0.08,#0.08,
        angle_ki=0.00,
        angle_kd=0.00,
    )
    signal.signal(signal.SIGINT, lambda s, f: signal_handler(s, f, car, follower))
    signal.signal(signal.SIGTERM, lambda s, f: signal_handler(s, f, car, follower))
    print(' Starting Follow')
    try:
        follower.run()
        while follower.running:
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        follower.stop()
        car.cleanup()
        sys.exit(0)
    print('Stopping Follow')