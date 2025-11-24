import sys
import time

import pigpio

# --- GPIO Pin Configuration ---
# NOTE: This script uses BCM numbering (the GPIO number, not the physical pin number)
# based on the physical pin mapping you provided.

# M1 (Motor 1): Connected to Pin 32, 38, 36
# M2 (Motor 2): Connected to Pin 12, 8, 10
# M3 (Motor 3): Connected to Pin 33, 29, 31

# Pin Assignments based on the user's "pwm, then forward, then reverse" order
# ----------------------------------------------------------------------------------
# MOTOR 1 (M1) - ASSUMED PINS: 32(PWM), 38(FWD), 36(REV)
M1_PWM_PIN = 12   # Physical Pin 32 -> GPIO12 (User confirmed PWM)
M1_INA_PIN = 20   # Physical Pin 38 -> GPIO20 (Forward)
M1_INB_PIN = 16   # Physical Pin 36 -> GPIO16 (Reverse - ASSUMED)

# MOTOR 2 (M2) - ASSUMED PINS: 12(PWM), 8(FWD), 10(REV)
M2_PWM_PIN = 18   # Physical Pin 12 -> GPIO18 (User confirmed PWM)
M2_INA_PIN = 24   # Physical Pin 8  -> GPIO14 (Forward)
M2_INB_PIN = 23   # Physical Pin 10 -> GPIO15 (Reverse - ASSUMED)

# MOTOR 3 (M3) - ASSUMED PINS: 33(PWM), 29(FWD), 31(REV)
M3_PWM_PIN = 13   # Physical Pin 33 -> GPIO13 ( PWM)
M3_INA_PIN = 5    # Physical Pin 29 -> GPIO5  (Forward)
M3_INB_PIN = 6    # Physical Pin 31 -> GPIO6  (Reverse )
# ----------------------------------------------------------------------------------

# Global pigpio instance
pi = None

# --- Configuration Constants ---
PWM_FREQUENCY = 100 # Lowered from 1000Hz to 100Hz for better stability
TEST_SPEED = 60     # Increased from 30% to 60% duty cycle for initial spin
MOVE_SPEED = 80     # Increased from 40% to 80% duty cycle for movement tests


def setup_gpio():
    """Initializes pigpio connection and sets up pins."""
    print("Connecting to pigpio daemon...")
    global pi
    try:
        pi = pigpio.pi()
        
        if not pi.connected:
            print("ERROR: Could not connect to pigpio daemon.")
            print("Please ensure the daemon is running: 'sudo systemctl start pigpiod'")
            sys.exit(1)
        
        # Define all 9 pins as outputs
        motor_pins = [
            M1_PWM_PIN, M1_INA_PIN, M1_INB_PIN,
            M2_PWM_PIN, M2_INA_PIN, M2_INB_PIN,
            M3_PWM_PIN, M3_INA_PIN, M3_INB_PIN
        ]
        
        for pin in motor_pins:
            pi.set_mode(pin, pigpio.OUTPUT)
            pi.write(pin, 0)
        
        # Set PWM frequency for all PWM pins
        pi.set_PWM_frequency(M1_PWM_PIN, PWM_FREQUENCY)
        pi.set_PWM_frequency(M2_PWM_PIN, PWM_FREQUENCY)
        pi.set_PWM_frequency(M3_PWM_PIN, PWM_FREQUENCY)
        
        # Start PWM at 0% duty cycle (stopped)
        pi.set_PWM_dutycycle(M1_PWM_PIN, 0)
        pi.set_PWM_dutycycle(M2_PWM_PIN, 0)
        pi.set_PWM_dutycycle(M3_PWM_PIN, 0)
        
        print(f"Setup complete. PWM Frequency set to {PWM_FREQUENCY}Hz. Ready to run tests.")

    except Exception as e:
        print(f"Error during GPIO setup: {e}")
        cleanup()
        sys.exit(1)


def set_motor_speed(motor_index, speed_percent):
    """
    Sets the speed and direction of a single motor.
    :param motor_index: 1, 2, or 3
    :param speed_percent: -100 (full reverse) to 100 (full forward)
    """
    
    if motor_index == 1:
        pwm_pin, inA, inB = M1_PWM_PIN, M1_INA_PIN, M1_INB_PIN
    elif motor_index == 2:
        pwm_pin, inA, inB = M2_PWM_PIN, M2_INA_PIN, M2_INB_PIN
    elif motor_index == 3:
        pwm_pin, inA, inB = M3_PWM_PIN, M3_INA_PIN, M3_INB_PIN
    else:
        print(f"Invalid motor index: {motor_index}")
        return

    # Ensure speed is within bounds
    speed = max(-100, min(100, speed_percent))
    duty_cycle_255 = int(abs(speed) * 2.55)

    # Set direction pins
    if speed > 0:
        # Forward
        pi.write(inA, 1)
        pi.write(inB, 0)
    elif speed < 0:
        # Reverse
        pi.write(inA, 0)
        pi.write(inB, 1)
    else:
        # Stop (or brake)
        pi.write(inA, 0)
        pi.write(inB, 0)
        
    # Apply speed via PWM duty cycle (0-255 range)
    pi.set_PWM_dutycycle(pwm_pin, duty_cycle_255)


def stop_all_motors():
    """Immediately stops all three motors."""
    print("Stopping all motors...")
    set_motor_speed(1, 0)
    set_motor_speed(2, 0)
    set_motor_speed(3, 0)


def test_individual_motors(test_duration=1.5, speed=TEST_SPEED):
    """Runs each motor individually for a short time."""
    print(f"\n--- Starting Individual Motor Test (Speed: {speed}%) ---")
    print("If motors are still not spinning, consider changing to the pigpio library")
    print("for hardware PWM, or check if your motor shield requires a higher minimum voltage.")
    
    for i in range(1, 4):
    # for i in range(3, 4):
        print(f"Testing Motor {i} FORWARD...")
        set_motor_speed(i, speed)
        time.sleep(test_duration)
        stop_all_motors()
        time.sleep(0.5)
        
        print(f"Testing Motor {i} REVERSE...")
        set_motor_speed(i, -speed)
        time.sleep(test_duration)
        stop_all_motors()
        time.sleep(0.5)

    print("Individual Motor Test complete.")


def move_test(direction_name, m1_speed, m2_speed, m3_speed, test_duration=2.0):
    """Executes an omni movement using calculated motor speeds."""
    print(f"\n--- Testing Movement: {direction_name} ---")
    
    # Set the speeds for all three motors
    set_motor_speed(1, m1_speed)
    set_motor_speed(2, m2_speed)
    set_motor_speed(3, m3_speed)
    
    time.sleep(test_duration)
    stop_all_motors()
    time.sleep(0.5)


def run_all_tests():
    """Runs the sequence of motor and movement tests."""
    print("Starting Omni Car Test Sequence...")
    
    # 1. Individual Motor Test (Essential for initial wiring verification)
    test_individual_motors(test_duration=1.5)
    
    # 2. Rotation Test (Simplified Kinematics: All motors spin the same way)
    # This should make the robot spin in place.
    # move_test("ROTATE CLOCKWISE", MOVE_SPEED, MOVE_SPEED, MOVE_SPEED, 2.0)
    # move_test("ROTATE COUNTER-CLOCKWISE", -MOVE_SPEED, -MOVE_SPEED, -MOVE_SPEED, 2.0)
    
    # # 3. Forward/Backward Test (Simplified Kinematics for straight-line movement)
    # # Forward movement uses M1 at full speed, M2/M3 at half speed reverse.
    # move_test("FORWARD MOVEMENT (M1=80, M2=-40, M3=-40)", MOVE_SPEED, -MOVE_SPEED/2, -MOVE_SPEED/2, 3.0)
    
    # # Backward movement
    # move_test("BACKWARD MOVEMENT (M1=-80, M2=40, M3=40)", -MOVE_SPEED, MOVE_SPEED/2, MOVE_SPEED/2, 3.0)

    print("\n--- ALL TESTS COMPLETE ---")


def cleanup():
    """Cleans up pigpio connection."""
    global pi
    if pi and pi.connected:
        pi.set_PWM_dutycycle(M1_PWM_PIN, 0)
        pi.set_PWM_dutycycle(M2_PWM_PIN, 0)
        pi.set_PWM_dutycycle(M3_PWM_PIN, 0)
        pi.stop()
        print("GPIO cleanup complete.")


if __name__ == "__main__":
    try:
        setup_gpio()
        run_all_tests()
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
    finally:
        cleanup()