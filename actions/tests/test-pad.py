import math
import sys
import threading
import time
from select import select

import RPi.GPIO as GPIO
from evdev import InputDevice, KeyEvent, categorize, ecodes, util

# --- 1. CONFIGURATION CONSTANTS ---
GAMEPAD_DEVICE_PATH = '/dev/input/event8' # UPDATED to match your traceback
MAX_DUTY_CYCLE_PERCENT = 80 # Maximum motor speed (0-100)
PWM_FREQUENCY = 100         # Lower frequency for better stability with software PWM
POLL_DELAY = 0.05           # Delay for the main control loop (20 times per second)

# --- 2. GPIO PIN CONFIGURATION (BCM Numbering) ---
# NOTE: The BCM pin assignments from the previous script are reused here.
# Please double-check these pins match your physical wiring.

# MOTOR 1 (M1) - ASSUMED PINS: PWM:12, FWD:20, REV:16
M1_PWM_PIN = 12
M1_IN1_PIN = 20
M1_IN2_PIN = 16

# MOTOR 2 (M2) - ASSUMED PINS: PWM:18, FWD:14, 10(REV)->15
M2_PWM_PIN = 18
M2_IN1_PIN = 14
M2_IN2_PIN = 15

# MOTOR 3 (M3) - ASSUMED PINS: PWM:13, FWD:5, 31(REV)->6
M3_PWM_PIN = 13
M3_IN1_PIN = 5
M3_IN2_PIN = 6

# --- 3. GAMEPAD INPUT CODES & FALLBACK (Amazon Luna Controller) ---
AXIS_X_CODE = ecodes.ABS_X    # Left Stick X-axis (Strafe)
AXIS_Y_CODE = ecodes.ABS_Y    # Left Stick Y-axis (Forward/Backward)
AXIS_ROT_CODE = ecodes.ABS_RX # Right Stick X-axis (Rotation) - CORRECTED for Luna Stick

# Define fallback axis details for Luna controller if autodetection fails (16-bit range)
FALLBACK_AXES_INFO = {
    AXIS_X_CODE:   {'min': -32768, 'max': 32767, 'flat': 2000}, # 2000 is a standard deadzone
    AXIS_Y_CODE:   {'min': -32768, 'max': 32767, 'flat': 2000},
    AXIS_ROT_CODE: {'min': -32768, 'max': 32767, 'flat': 2000},
}

# --- 4. GLOBAL STATE AND THREADING ---
# Global PWM objects for RPi.GPIO
pwm1 = None
pwm2 = None
pwm3 = None

dev = None
# Stores normalized joystick values (-1.0 to 1.0)
controller_state = {
    'Vx': 0.0,  # Lateral velocity (Strafe)
    'Vy': 0.0,  # Longitudinal velocity (Forward/Backward)
    'Rot': 0.0  # Angular velocity (Rotation)
}
# Stores the raw min/max values found during setup
axis_info = {}
running_event = threading.Event()


# --- 5. MOTOR CONTROL FUNCTIONS (Using RPi.GPIO logic) ---

def setup_gpio():
    """Initializes RPi.GPIO settings and sets up PWM objects."""
    print("Setting up GPIO pins using BCM mode (RPi.GPIO)...")
    try:
        GPIO.setmode(GPIO.BCM)
        
        motor_pins = [M1_PWM_PIN, M1_IN1_PIN, M1_IN2_PIN, M2_PWM_PIN, M2_IN1_PIN, M2_IN2_PIN, M3_PWM_PIN, M3_IN1_PIN, M3_IN2_PIN]
        
        for pin in motor_pins:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW) # Ensure all motors are off initially
            
        global pwm1, pwm2, pwm3
        
        # Initialize PWM instances
        pwm1 = GPIO.PWM(M1_PWM_PIN, PWM_FREQUENCY)
        pwm2 = GPIO.PWM(M2_PWM_PIN, PWM_FREQUENCY)
        pwm3 = GPIO.PWM(M3_PWM_PIN, PWM_FREQUENCY)
        
        # Start PWM at 0% duty cycle (stopped)
        pwm1.start(0)
        pwm2.start(0)
        pwm3.start(0)
        
        print(f"Setup complete. PWM Frequency set to {PWM_FREQUENCY}Hz.")
        
        # WARNING about RPi.GPIO instability
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("!! WARNING: Using RPi.GPIO (Software PWM). Motor movement may be   !!")
        print("!! unstable or fail due to high CPU load or system jitter.         !!")
        print("!! If motors stutter, please switch to the 'pigpio' library.       !!")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

    except Exception as e:
        print(f"Error during GPIO setup: {e}")
        cleanup()
        sys.exit(1)


def set_motor_speed(pwm_pin, in1, in2, speed_percent):
    """
    Sets the speed and direction of a single motor using RPi.GPIO.
    :param speed_percent: -100 (full reverse) to 100 (full forward)
    """
    # Determine the correct PWM object based on the pin
    global pwm1, pwm2, pwm3
    if pwm_pin == M1_PWM_PIN:
        pwm_obj = pwm1
    elif pwm_pin == M2_PWM_PIN:
        pwm_obj = pwm2
    elif pwm_pin == M3_PWM_PIN:
        pwm_obj = pwm3
    else:
        return

    speed = max(-100, min(100, speed_percent))
    
    # Duty cycle is 0-100 directly
    duty_cycle = min(abs(speed), MAX_DUTY_CYCLE_PERCENT)

    # Set direction pins
    if speed > 0:
        # Forward
        GPIO.output(in1, GPIO.HIGH)
        GPIO.output(in2, GPIO.LOW)
    elif speed < 0:
        # Reverse
        GPIO.output(in1, GPIO.LOW)
        GPIO.output(in2, GPIO.HIGH)
    else:
        # Stop
        GPIO.output(in1, GPIO.LOW)
        GPIO.output(in2, GPIO.LOW)
        
    # Apply speed via PWM duty cycle
    pwm_obj.ChangeDutyCycle(duty_cycle)


def cleanup():
    """Stops PWM and cleans up RPi.GPIO."""
    global pwm1, pwm2, pwm3
    
    if pwm1:
        pwm1.stop()
    if pwm2:
        pwm2.stop()
    if pwm3:
        pwm3.stop()
        
    GPIO.cleanup() 
    print("RPi.GPIO cleanup complete.")


# --- 6. KINEMATICS AND CONTROL LOOP (NO CHANGES) ---

def calculate_motor_speeds(vx, vy, rotation):
    """
    Implements inverse kinematics for a 3-wheel Kiwi Drive.
    """
    
    # S_i = Vx * cos(theta_i) + Vy * sin(theta_i) + Omega
    
    # Motor 1 (Front/Top)
    S1 = 0 * vx + 1 * vy + rotation
    
    # Motor 2 (Left-Rear)
    S2 = -0.866 * vx - 0.5 * vy + rotation 
    
    # Motor 3 (Right-Rear)
    S3 = 0.866 * vx - 0.5 * vy + rotation
    
    # Normalize speeds
    max_speed_abs = max(abs(S1), abs(S2), abs(S3), 1.0)
    
    M1_speed = (S1 / max_speed_abs) * 100 
    M2_speed = (S2 / max_speed_abs) * 100
    M3_speed = (S3 / max_speed_abs) * 100
    
    return M1_speed, M2_speed, M3_speed


def control_loop():
    """Continuously reads controller state and applies motor commands."""
    print("Starting motor control loop...")
    
    while running_event.is_set():
        vx = controller_state['Vx']
        vy = controller_state['Vy']
        rot = controller_state['Rot']
        
        # Calculate motor commands based on current joystick inputs
        m1_cmd, m2_cmd, m3_cmd = calculate_motor_speeds(vx, vy, rot)
        
        # Apply commands to motors
        set_motor_speed(M1_PWM_PIN, M1_IN1_PIN, M1_IN2_PIN, m1_cmd)
        set_motor_speed(M2_PWM_PIN, M2_IN1_PIN, M2_IN2_PIN, m2_cmd)
        set_motor_speed(M3_PWM_PIN, M3_IN1_PIN, M3_IN2_PIN, m3_cmd)
        
        time.sleep(POLL_DELAY)
        
    # Stop motors upon exit
    set_motor_speed(M1_PWM_PIN, M1_IN1_PIN, M1_IN2_PIN, 0)
    set_motor_speed(M2_PWM_PIN, M2_IN1_PIN, M2_IN2_PIN, 0)
    set_motor_speed(M3_PWM_PIN, M3_IN1_PIN, M3_IN2_PIN, 0)
    print("Motor control loop terminated.")

# --- 7. GAMEPAD INPUT HANDLING (FIXED EV_ABS ISSUE AND ADDED FALLBACK) ---

def setup_gamepad():
    """Connects to the gamepad device and determines axis min/max values."""
    global dev, axis_info
    try:
        dev = InputDevice(GAMEPAD_DEVICE_PATH)
        print(f"Found gamepad: {dev.name} at {dev.path}")
        
        # Safely retrieve EV_ABS capabilities using .get()
        abs_capabilities = dev.capabilities(verbose=True).get(ecodes.EV_ABS, [])

        # Read axis min/max bounds and flat (deadzone) from the device
        required_axes_found = 0
        for code, info in abs_capabilities:
            if code in [AXIS_X_CODE, AXIS_Y_CODE, AXIS_ROT_CODE]:
                # info is a tuple: (type, code, (min, max, fuzz, flat, range))
                axis_info[code] = {'min': info[2][0], 'max': info[2][1], 'flat': info[2][3]}
                print(f"  Axis {ecodes.by_code[code][0]}: Min={info[2][0]}, Max={info[2][1]}, Flat={info[2][3]}")
                required_axes_found += 1
                
        if required_axes_found < 3:
            # Fallback logic if any required axis info is missing
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            print("!! WARNING: Missing axis info. Default Luna config is being used.  !!")
            print("!! Deadzone is set to 2000 (out of 32767).                         !!")
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            
            # Use the predefined fallback configuration for the required axes
            for code, info in FALLBACK_AXES_INFO.items():
                if code not in axis_info:
                    axis_info[code] = info
        
    except FileNotFoundError:
        print(f"ERROR: Gamepad device not found at {GAMEPAD_DEVICE_PATH}.")
        print("1. Ensure your controller is connected via Bluetooth.")
        print("2. Check the correct device path using 'ls /dev/input/by-id/'")
        sys.exit(1)
        

def normalize_axis(code, value):
    """
    Normalizes a raw axis value to a float between -1.0 and 1.0.
    This includes the deadzone check, ensuring 0.0 is returned if the stick is central.
    """
    info = axis_info.get(code)
    if not info:
        return 0.0

    min_val, max_val, flat = info['min'], info['max'], info['flat']
    
    # Center calculation (typically 0)
    center = (min_val + max_val) / 2
    
    # Deadzone check: If value is within the 'flat' region of the center, return 0.0
    # This is critical to ensure the car stops when the stick is released.
    if abs(value - center) < flat:
        return 0.0
        
    # Scale range (from center to max)
    scale_range = max_val - center
    
    # Normalize to -1.0 to 1.0
    normalized = (value - center) / scale_range
        
    return normalized


def gamepad_input_loop():
    """Listens for gamepad events and updates the global state."""
    print("Starting gamepad input listener...")
    while running_event.is_set():
        # Use select for non-blocking read
        r, w, x = select([dev], [], [], 0.05)
        if r:
            for event in dev.read():
                if event.type == ecodes.EV_ABS:
                    # Handle Axis changes (Movement)
                    normalized_value = normalize_axis(event.code, event.value)
                    
                    if event.code == AXIS_X_CODE:
                        controller_state['Vx'] = normalized_value
                    elif event.code == AXIS_Y_CODE:
                        # Y axis is usually reversed: -1 is Forward, 1 is Backward.
                        # We flip it so 1.0 is Forward (Vy).
                        controller_state['Vy'] = -normalized_value 
                    elif event.code == AXIS_ROT_CODE:
                        controller_state['Rot'] = normalized_value * 1.2 # Boost rotation sensitivity
                        
                elif event.type == ecodes.EV_KEY:
                    key_event = categorize(event)
                    if key_event.keystate == KeyEvent.key_down:
                        if key_event.code == 'BTN_START': 
                             print("\nStart button pressed. Exiting...")
                             running_event.clear()
                             return


if __name__ == "__main__":
    
    # 1. Setup Motor Control
    setup_gpio()
    
    # 2. Setup Gamepad Input
    setup_gamepad()
    
    # Signal that threads should run
    running_event.set()
    
    # 3. Start Control Loop in a separate thread
    control_thread = threading.Thread(target=control_loop)
    control_thread.daemon = True 
    control_thread.start()
    
    # 4. Run Input Loop in the main thread
    try:
        gamepad_input_loop()
        
    except KeyboardInterrupt:
        print("\nScript interrupted by user.")
    
    finally:
        running_event.clear() 
        if control_thread.is_alive():
            control_thread.join(1) 
        cleanup()