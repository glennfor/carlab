import sys
import time

import RPi.GPIO as GPIO

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

# Global PWM objects
pwm1 = None
pwm2 = None
pwm3 = None

# --- Configuration Constants ---
PWM_FREQUENCY = 100 # Lowered from 1000Hz to 100Hz for better stability
TEST_SPEED = 60     # Increased from 30% to 60% duty cycle for initial spin
MOVE_SPEED = 80     # Increased from 40% to 80% duty cycle for movement tests


def setup_gpio():
    """Initializes GPIO settings and sets up PWM objects."""
    print("Setting up GPIO pins using BCM mode...")
    try:
        GPIO.setmode(GPIO.BCM)
        
        # Define all 9 pins as outputs
        motor_pins = [
            M1_PWM_PIN, M1_INA_PIN, M1_INB_PIN,
            M2_PWM_PIN, M2_INA_PIN, M2_INB_PIN,
            M3_PWM_PIN, M3_INA_PIN, M3_INB_PIN
        ]
        
        for pin in motor_pins:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW) # Ensure all motors are off initially
            
        global pwm1, pwm2, pwm3
        # Initialize PWM instances (using the configured frequency)
        pwm1 = GPIO.PWM(M1_PWM_PIN, PWM_FREQUENCY)
        pwm2 = GPIO.PWM(M2_PWM_PIN, PWM_FREQUENCY)
        pwm3 = GPIO.PWM(M3_PWM_PIN, PWM_FREQUENCY)
        
        # Start PWM at 0% duty cycle (stopped)
        pwm1.start(0)
        pwm2.start(0)
        pwm3.start(0)
        
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
        pwm_obj, inA, inB = pwm1, M1_INA_PIN, M1_INB_PIN
    elif motor_index == 2:
        pwm_obj, inA, inB = pwm2, M2_INA_PIN, M2_INB_PIN
    elif motor_index == 3:
        pwm_obj, inA, inB = pwm3, M3_INA_PIN, M3_INB_PIN
    else:
        print(f"Invalid motor index: {motor_index}")
        return

    # Ensure speed is within bounds
    speed = max(-100, min(100, speed_percent))
    duty_cycle = abs(speed)

    # Set direction pins
    if speed > 0:
        # Forward
        GPIO.output(inA, GPIO.HIGH)
        GPIO.output(inB, GPIO.LOW)
    elif speed < 0:
        # Reverse
        GPIO.output(inA, GPIO.LOW)
        GPIO.output(inB, GPIO.HIGH)
    else:
        # Stop (or brake)
        GPIO.output(inA, GPIO.LOW)
        GPIO.output(inB, GPIO.LOW)
        
    # Apply speed via PWM duty cycle
    pwm_obj.ChangeDutyCycle(duty_cycle)


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
    """Cleans up GPIO settings."""
    global pwm1, pwm2, pwm3
    if pwm1:
        pwm1.stop()
    if pwm2:
        pwm2.stop()
    if pwm3:
        pwm3.stop()
    GPIO.cleanup()
    print("GPIO cleanup complete.")


if __name__ == "__main__":
    try:
        setup_gpio()
        run_all_tests()
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
    finally:
        cleanup()