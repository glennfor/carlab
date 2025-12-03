import time
import pigpio

# --- Motor pin definitions ---
M1_PWM_PIN = 16
M1_INA_PIN = 5
M1_INB_PIN = 6

M2_PWM_PIN = 22
M2_INA_PIN = 17
M2_INB_PIN = 27

M3_PWM_PIN = 25
M3_INA_PIN = 24
M3_INB_PIN = 23

# --- Setup pigpio ---
pi = pigpio.pi()
if not pi.connected:
    print("Could not connect to pigpiod. Did you run 'sudo pigpiod'?")
    exit()

motors = [
    {"PWM": M1_PWM_PIN, "INA": M1_INA_PIN, "INB": M1_INB_PIN},
    {"PWM": M2_PWM_PIN, "INA": M2_INA_PIN, "INB": M2_INB_PIN},
    {"PWM": M3_PWM_PIN, "INA": M3_INA_PIN, "INB": M3_INB_PIN}
]

# Initialize pins
for m in motors:
    pi.set_mode(m["PWM"], pigpio.OUTPUT)
    pi.set_mode(m["INA"], pigpio.OUTPUT)
    pi.set_mode(m["INB"], pigpio.OUTPUT)
    
    pi.write(m["INA"], 1)  # Forward direction
    pi.write(m["INB"], 0)
    pi.set_PWM_frequency(m["PWM"], 1000) # Set 100Hz
    pi.set_PWM_dutycycle(m["PWM"], 0)   # Start at 0 (Range is 0-255)

# --- Helper function ---
def run_motors(motor_indices, duty=230, duration=5): # Duty 230 is approx 90% of 255
    print(f"Running motors {motor_indices}")
    for idx in motor_indices:
        pi.set_PWM_dutycycle(motors[idx]["PWM"], duty)
    
    time.sleep(duration)
    
    for idx in motor_indices:
        pi.set_PWM_dutycycle(motors[idx]["PWM"], 0)

try:
    # 3. Test all wheels together
    run_motors([0, 1, 2], duty=230, duration=5)

except KeyboardInterrupt:
    pass

# --- Cleanup ---
for m in motors:
    pi.set_PWM_dutycycle(m["PWM"], 0)
    pi.write(m["INA"], 0)
    pi.write(m["INB"], 0)

pi.stop()
print("Test complete.")