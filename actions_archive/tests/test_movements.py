#!/usr/bin/env python3
"""
Test script for individual car movement directions.
Allows testing forward, backward, left, right, diagonal movements, and rotation
to verify inverse kinematics calculations are correct.
"""

import sys
import time
from math import cos, pi, sin
from pathlib import Path

# Add parent directory to path to import car module
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from actions_archive.car import Car


class MovementTester:
    """Test harness for car movement directions."""
    
    def __init__(self, default_speed=1, default_duration=.5):
        """
        Initialize the movement tester.
        
        :param default_speed: Default speed for movements (0.0 to 1.0)
        :param default_duration: Default duration for movements in seconds
        """
        print("Initializing car...")
        self.car = Car()
        self.default_speed = default_speed
        self.default_duration = default_duration
        print("Car initialized successfully.\n")
    
    def print_motor_speeds(self, vx, vy, rotation):
        """
        Calculate and print motor speeds for given movement command.
        
        :param vx: Lateral velocity (left/right)
        :param vy: Longitudinal velocity (forward/backward)
        :param rotation: Angular velocity (clockwise/counterclockwise)
        """
        # Calculate motor speeds using the same logic as Car.drive()
        S_right = vx * cos(60*pi/180) + vy * sin(60*pi/180) + rotation
        S_left = vx * cos(180*pi/180 + 120*pi/180) + vy * sin(180*pi/180 + 120*pi/180) + rotation
        S_rear = vx * cos(180*pi/180) + vy * sin(180*pi/180) + rotation
        
        # Normalize speeds
        max_speed_abs = max(abs(S_right), abs(S_left), abs(S_rear), 1.0)
        
        M_right_speed = (S_right / max_speed_abs) * 100
        M_left_speed = (S_left / max_speed_abs) * 100
        M_rear_speed = (S_rear / max_speed_abs) * 100
        
        print(f"  Input: vx={vx:.2f}, vy={vy:.2f}, rotation={rotation:.2f}")
        print(f"  Motor speeds:")
        print(f"    M1 (Right):  {M_right_speed:6.2f}%")
        print(f"    M2 (Left):   {M_left_speed:6.2f}%")
        print(f"    M3 (Rear):  {M_rear_speed:6.2f}%")
        print()
    
    def test_movement(self, name, vx, vy, rotation, speed=None, duration=None):
        """
        Test a specific movement direction.
        
        :param name: Name of the movement (for display)
        :param vx: Lateral velocity component
        :param vy: Longitudinal velocity component
        :param rotation: Angular velocity component
        :param speed: Speed multiplier (uses default if None)
        :param duration: Movement duration in seconds (uses default if None)
        """
        speed = speed if speed is not None else self.default_speed
        duration = duration if duration is not None else self.default_duration
        
        # Scale velocities by speed
        vx_scaled = vx * speed
        vy_scaled = vy * speed
        rotation_scaled = rotation * speed
        
        print(f"\n{'='*60}")
        print(f"Testing: {name}")
        print(f"{'='*60}")
        self.print_motor_speeds(vx_scaled, vy_scaled, rotation_scaled)
        
        print(f"Executing movement for {duration} seconds...")
        self.car.drive(vx_scaled, vy_scaled, rotation_scaled)
        time.sleep(duration)
        
        print("Stopping...")
        self.car.drive(0, 0, 0)
        time.sleep(0.5)
    
    def test_forward(self, speed=None, duration=None):
        """Test forward movement."""
        self.test_movement("FORWARD", 0, 1, 0, speed, duration)
    
    def test_backward(self, speed=None, duration=None):
        """Test backward movement."""
        self.test_movement("BACKWARD", 0, -1, 0, speed, duration)
    
    def test_left(self, speed=None, duration=None):
        """Test left strafe movement."""
        self.test_movement("LEFT STRAFE", -1, 0, 0, speed, duration)
    
    def test_right(self, speed=None, duration=None):
        """Test right strafe movement."""
        self.test_movement("RIGHT STRAFE", 1, 0, 0, speed, duration)
    
    def test_forward_left(self, speed=None, duration=None):
        """Test forward-left diagonal movement."""
        self.test_movement("FORWARD-LEFT DIAGONAL", -1, 1, 0, speed, duration)
    
    def test_forward_right(self, speed=None, duration=None):
        """Test forward-right diagonal movement."""
        self.test_movement("FORWARD-RIGHT DIAGONAL", 1, 1, 0, speed, duration)
    
    def test_backward_left(self, speed=None, duration=None):
        """Test backward-left diagonal movement."""
        self.test_movement("BACKWARD-LEFT DIAGONAL", -1, -1, 0, speed, duration)
    
    def test_backward_right(self, speed=None, duration=None):
        """Test backward-right diagonal movement."""
        self.test_movement("BACKWARD-RIGHT DIAGONAL", 1, -1, 0, speed, duration)
    
    def test_rotate_clockwise(self, speed=None, duration=None):
        """Test clockwise rotation (in place)."""
        self.test_movement("ROTATE CLOCKWISE", 0, 0, 1, speed, duration)
    
    def test_rotate_counterclockwise(self, speed=None, duration=None):
        """Test counter-clockwise rotation (in place)."""
        self.test_movement("ROTATE COUNTER-CLOCKWISE", 0, 0, -1, speed, duration)
    
    def test_forward_while_rotating(self, speed=None, duration=None):
        """Test forward movement while rotating clockwise."""
        self.test_movement("FORWARD + ROTATION", 0, 1, 0.5, speed, duration)
    
    def cleanup(self):
        """Clean up GPIO resources."""
        print("\nCleaning up...")
        self.car.cleanup()
        print("Cleanup complete.")


def print_menu():
    """Print the test menu."""
    print("\n" + "="*60)
    print("CAR MOVEMENT TEST MENU")
    print("="*60)
    print("1.  Forward")
    print("2.  Backward")
    print("3.  Left Strafe")
    print("4.  Right Strafe")
    print("5.  Forward-Left Diagonal")
    print("6.  Forward-Right Diagonal")
    print("7.  Backward-Left Diagonal")
    print("8.  Backward-Right Diagonal")
    print("9.  Rotate Clockwise")
    print("10. Rotate Counter-Clockwise")
    print("11. Forward + Rotation")
    print("12. Run All Tests")
    print("13. Custom Movement (enter vx, vy, rotation)")
    print("0.  Exit")
    print("="*60)


def run_interactive_mode():
    """Run the test script in interactive mode."""
    tester = MovementTester(default_speed=0.5, default_duration=2.0)
    
    try:
        while True:
            print_menu()
            choice = input("\nSelect a test (0-13): ").strip()
            
            if choice == "0":
                break
            elif choice == "1":
                tester.test_forward()
            elif choice == "2":
                tester.test_backward()
            elif choice == "3":
                tester.test_left()
            elif choice == "4":
                tester.test_right()
            elif choice == "5":
                tester.test_forward_left()
            elif choice == "6":
                tester.test_forward_right()
            elif choice == "7":
                tester.test_backward_left()
            elif choice == "8":
                tester.test_backward_right()
            elif choice == "9":
                tester.test_rotate_clockwise()
            elif choice == "10":
                tester.test_rotate_counterclockwise()
            elif choice == "11":
                tester.test_forward_while_rotating()
            elif choice == "12":
                run_all_tests(tester)
            elif choice == "13":
                try:
                    vx = float(input("Enter vx (lateral): "))
                    vy = float(input("Enter vy (longitudinal): "))
                    rotation = float(input("Enter rotation: "))
                    speed = input("Enter speed (0.0-1.0, press Enter for default 0.5): ").strip()
                    speed = float(speed) if speed else 0.5
                    duration = input("Enter duration in seconds (press Enter for default 2.0): ").strip()
                    duration = float(duration) if duration else 2.0
                    tester.test_movement("CUSTOM", vx, vy, rotation, speed, duration)
                except ValueError:
                    print("Invalid input. Please enter numeric values.")
            else:
                print("Invalid choice. Please try again.")
            
            input("\nPress Enter to continue...")
    
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
    finally:
        tester.cleanup()


def run_all_tests(tester):
    """Run all predefined movement tests in sequence."""
    print("\n" + "="*60)
    print("RUNNING ALL TESTS")
    print("="*60)
    
    tests = [
        ("Forward", tester.test_forward),
        ("Backward", tester.test_backward),
        ("Left Strafe", tester.test_left),
        ("Right Strafe", tester.test_right),
        ("Forward-Left Diagonal", tester.test_forward_left),
        ("Forward-Right Diagonal", tester.test_forward_right),
        ("Backward-Left Diagonal", tester.test_backward_left),
        ("Backward-Right Diagonal", tester.test_backward_right),
        ("Rotate Clockwise", tester.test_rotate_clockwise),
        ("Rotate Counter-Clockwise", tester.test_rotate_counterclockwise),
        ("Forward + Rotation", tester.test_forward_while_rotating),
    ]
    
    for name, test_func in tests:
        print(f"\n>>> Running test: {name}")
        test_func()
        time.sleep(1)  # Brief pause between tests
    
    print("\n" + "="*60)
    print("ALL TESTS COMPLETE")
    print("="*60)


def run_command_line_mode(args):
    """Run specific tests from command line arguments."""
    tester = MovementTester(default_speed=0.5, default_duration=2.0)
    
    try:
        if len(args) < 2:
            print("Usage: python test_movements.py <direction> [speed] [duration]")
            print("\nAvailable directions:")
            print("  forward, backward, left, right")
            print("  forward-left, forward-right, backward-left, backward-right")
            print("  rotate-cw, rotate-ccw, forward-rotate")
            print("\nExample: python test_movements.py forward 0.5 2.0")
            return
        
        direction = args[1].lower()
        speed = float(args[2]) if len(args) > 2 else 0.5
        duration = float(args[3]) if len(args) > 3 else 2.0
        
        direction_map = {
            "forward": tester.test_forward,
            "backward": tester.test_backward,
            "left": tester.test_left,
            "right": tester.test_right,
            "forward-left": tester.test_forward_left,
            "forward-right": tester.test_forward_right,
            "backward-left": tester.test_backward_left,
            "backward-right": tester.test_backward_right,
            "rotate-cw": tester.test_rotate_clockwise,
            "rotate-ccw": tester.test_rotate_counterclockwise,
            "forward-rotate": tester.test_forward_while_rotating,
        }
        
        if direction in direction_map:
            direction_map[direction](speed, duration)
        elif direction == "all":
            run_all_tests(tester)
        else:
            print(f"Unknown direction: {direction}")
            print("Available directions:", ", ".join(direction_map.keys()))
    
    except ValueError:
        print("Error: Speed and duration must be numeric values.")
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
    finally:
        tester.cleanup()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Command line mode
        run_command_line_mode(sys.argv)
    else:
        # Interactive mode
        run_interactive_mode()

