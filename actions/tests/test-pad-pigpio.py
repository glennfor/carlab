import math
import sys
import threading
import time
from select import select

import pigpio
from evdev import InputDevice, categorize, ecodes, util

# --- 1. CONFIGURATION CONSTANTS ---
GAMEPAD_DEVICE_PATH = '/dev/input/event0' # UPDATE THIS if your path is different (e.g., event3)
MAX_DUTY_CYCLE_PERCENT = 80 # Maximum motor speed (0-100)
PWM_FREQUENCY = 100         # Stable frequency for pigpio
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

# --- 3. GAMEPAD INPUT CODES ---
# These codes are typical for many Bluetooth controllers (PS4, Xbox, generic).
# You may need to adjust these based on your specific controller model.
AXIS_X_CODE = ecodes.ABS_X    # Left Stick X-axis (Strafe)
AXIS_Y_CODE = ecodes.ABS_Y    # Left Stick Y-axis (Forward/Backward)
AXIS_ROT_CODE = ecodes.ABS_RZ # Right Stick X-axis (Rotation)

# --- 4. GLOBAL STATE AND THREADING ---
pi = None
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


# --- 5. MOTOR CONTROL FUNCTIONS (Reusing pigpio logic) ---

def setup_gpio():
    """Initializes the pigpio connection and sets up pins."""
    print("Connecting to pigpio daemon...")
    global pi
    pi = pigpio.pi() 
    
    if not pi.connected:
        print("ERROR: Could not connect to pigpio daemon.")
        print("Please ensure the daemon is running: 'sudo systemctl start pigpiod'")
        sys.exit(1)
        
    print("Connection established. Setting up pins...")
    
    motor_pins = [M1_PWM_PIN, M1_IN1_PIN, M1_IN2_PIN, M2_PWM_PIN, M2_IN1_PIN, M2_IN2_PIN, M3_PWM_PIN, M3_IN1_PIN, M3_IN2_PIN]
    
    for pin in motor_pins:
        pi.set_mode(pin, pigpio.OUTPUT)
        pi.write(pin, 0)
        
    pi.set_PWM_frequency(M1_PWM_PIN, PWM_FREQUENCY)
    pi.set_PWM_frequency(M2_PWM_PIN, PWM_FREQUENCY)
    pi.set_PWM_frequency(M3_PWM_PIN, PWM_FREQUENCY)

    pi.set_PWM_dutycycle(M1_PWM_PIN, 0)
    pi.set_PWM_dutycycle(M2_PWM_PIN, 0)
    pi.set_PWM_dutycycle(M3_PWM_PIN, 0)
    print(f"Setup complete. PWM Frequency set to {PWM_FREQUENCY}Hz.")


def set_motor_speed(pwm_pin, in1, in2, speed_percent):
    """
    Sets the speed and direction of a single motor using pigpio.
    :param speed_percent: -100 (full reverse) to 100 (full forward)
    """
    speed = max(-100, min(100, speed_percent))
    
    # Scale 0-100% duty cycle to pigpio's 0-255 range
    duty_cycle_255 = int(abs(speed) * 2.55)
    duty_cycle_255 = int(min(duty_cycle_255, MAX_DUTY_CYCLE_PERCENT * 2.55))

    # Set direction pins
    if speed > 0:
        # Forward
        pi.write(in1, 1)
        pi.write(in2, 0)
    elif speed < 0:
        # Reverse
        pi.write(in1, 0)
        pi.write(in2, 1)
    else:
        # Stop
        pi.write(in1, 0)
        pi.write(in2, 0)
        
    # Apply speed via PWM duty cycle
    pi.set_PWM_dutycycle(pwm_pin, duty_cycle_255)


def cleanup():
    """Disconnects the pigpio client."""
    global pi
    if pi and pi.connected:
        print("\nCleaning up motor control and disconnecting pigpio...")
        pi.set_PWM_dutycycle(M1_PWM_PIN, 0)
        pi.set_PWM_dutycycle(M2_PWM_PIN, 0)
        pi.set_PWM_dutycycle(M3_PWM_PIN, 0)
        pi.stop() 
        print("Cleanup complete.")


# --- 6. KINEMATICS AND CONTROL LOOP ---

def calculate_motor_speeds(vx, vy, rotation):
    """
    Implements inverse kinematics for a 3-wheel Kiwi Drive.
    
    Motor angles (assuming M1 is forward, M2 120 deg CCW, M3 120 deg CW):
    M1: 90 deg (or pi/2)
    M2: 210 deg (or 7*pi/6)
    M3: 330 deg (or 11*pi/6 or -pi/6)
    """
    
    # Kinematics matrix (simplified by absorbing the radius R and max speed)
    # S_i = Vx * cos(theta_i) + Vy * sin(theta_i) + Omega
    
    # Motor 1 (Front/Top)
    S1 = 0 * vx + 1 * vy + rotation
    
    # Motor 2 (Left-Rear)
    S2 = -0.866 * vx - 0.5 * vy + rotation # cos(210)=-0.866, sin(210)=-0.5
    
    # Motor 3 (Right-Rear)
    S3 = 0.866 * vx - 0.5 * vy + rotation # cos(330)=0.866, sin(330)=-0.5
    
    # Normalize speeds: Find the maximum absolute speed and scale all speeds down
    # so that the highest demanded speed is exactly 1.0 (or -1.0).
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

# --- 7. GAMEPAD INPUT HANDLING ---

def setup_gamepad():
    """Connects to the gamepad device and determines axis min/max values."""
    global dev, axis_info
    try:
        dev = InputDevice(GAMEPAD_DEVICE_PATH)
        print(f"Found gamepad: {dev.name} at {dev.path}")
        
        # Read axis min/max bounds for normalization
        for code, info in dev.capabilities(verbose=True)[ecodes.EV_ABS]:
            if code in [AXIS_X_CODE, AXIS_Y_CODE, AXIS_ROT_CODE]:
                # info is a tuple: (type, code, (min, max, fuzz, flat, range))
                axis_info[code] = {'min': info[2][0], 'max': info[2][1], 'flat': info[2][3]}
                print(f"  Axis {ecodes.by_code[code][0]}: Min={info[2][0]}, Max={info[2][1]}, Flat={info[2][3]}")
                
        if not axis_info:
            print("ERROR: Could not read required axis information. Check AXIS_X_CODE, etc.")
            sys.exit(1)
            
    except FileNotFoundError:
        print(f"ERROR: Gamepad device not found at {GAMEPAD_DEVICE_PATH}.")
        print("1. Ensure your controller is connected via Bluetooth.")
        print("2. Check the correct device path using 'ls /dev/input/by-id/'")
        sys.exit(1)
        

def normalize_axis(code, value):
    """Normalizes a raw axis value to a float between -1.0 and 1.0."""
    info = axis_info.get(code)
    if not info:
        return 0.0

    min_val, max_val, flat = info['min'], info['max'], info['flat']
    
    # Center calculation (typically 0)
    center = (min_val + max_val) / 2
    
    # Scale range (from center to max)
    scale_range = max_val - center
    
    # Normalize to -1.0 to 1.0
    normalized = (value - center) / scale_range
    
    # Deadzone application (using 'flat' value from evdev info)
    if abs(value - center) < flat:
        return 0.0
        
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
                    # Example for a button to stop or exit the script
                    # e.g., if you press the "Select" or "Start" button
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
    control_thread.daemon = True # Allows the script to exit even if the thread is alive
    control_thread.start()
    
    # 4. Run Input Loop in the main thread
    try:
        gamepad_input_loop()
        
    except KeyboardInterrupt:
        print("\nScript interrupted by user.")
    
    finally:
        running_event.clear() # Signal threads to stop
        if control_thread.is_alive():
            control_thread.join(1) # Wait for the control thread to finish
        cleanup()