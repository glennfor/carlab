import time
import RPi.GPIO as GPIO

# --- Motor pin definitions ---
M1_PWM_PIN = 16
M1_INA_PIN = 5
M1_INB_PIN = 6

# M2_PWM_PIN = 22
M2_PWM_PIN = 26
M2_INA_PIN = 17
M2_INB_PIN = 27

M3_PWM_PIN = 25
M3_INA_PIN = 24
M3_INB_PIN = 23

# --- Setup GPIO ---
GPIO.setmode(GPIO.BCM)

motors = [
    {"PWM": M1_PWM_PIN, "INA": M1_INA_PIN, "INB": M1_INB_PIN},
    {"PWM": M2_PWM_PIN, "INA": M2_INA_PIN, "INB": M2_INB_PIN},
    {"PWM": M3_PWM_PIN, "INA": M3_INA_PIN, "INB": M3_INB_PIN}
]

# Initialize pins
for m in motors:
    GPIO.setup(m["PWM"], GPIO.OUT)
    GPIO.setup(m["INA"], GPIO.OUT)
    GPIO.setup(m["INB"], GPIO.OUT)
    GPIO.output(m["INA"], GPIO.HIGH)  # Forward direction
    GPIO.output(m["INB"], GPIO.LOW)

# Initialize PWM at 100 Hz
for m in motors:
    m["pwm"] = GPIO.PWM(m["PWM"], 100)
    m["pwm"].start(0)  # Start with 0% duty cycle

# --- Helper function ---
def run_motors(motor_indices, duty=90, duration=5):
    for idx in motor_indices:
        motors[idx]["pwm"].ChangeDutyCycle(duty)
    print(f"Running motors {motor_indices} at {duty}% PWM for {duration} s")
    time.sleep(duration)
    for idx in motor_indices:
        motors[idx]["pwm"].ChangeDutyCycle(0)

# --- Test sequence ---

# run_motors([1], duty=90, duration=5)
# 1. Test wheels individually
# for i in range(3):
#     run_motors([i], duty=90, duration=5)

# # 2. Test wheels in pairs
run_motors([0, 1], duty=40, duration=5)
run_motors([0, 2], duty=40, duration=5)
run_motors([1, 2], duty=40, duration=5)

# 3. Test all wheels together
# run_motors([0, 1, 2], duty=50, duration=5)

# --- Cleanup ---
for m in motors:
    m["pwm"].stop()
GPIO.cleanup()
print("Test complete.")
