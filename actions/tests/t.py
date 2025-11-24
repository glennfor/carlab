import time

import pigpio

M1_PWM_PIN = 13
M1_INA_PIN = 5
M1_INB_PIN = 6


# MOTOR 2 (M2) - ASSUMED PINS: PWM:18, FWD:24, 10(REV)->23
M2_PWM_PIN = 22
M2_INA_PIN = 17
M2_INB_PIN = 27


# MOTOR 3 (M3) - ASSUMED PINS: PWM:12, FWD:20, REV:16
M3_PWM_PIN = 12
M3_INA_PIN = 20
M3_INB_PIN = 16

pi = pigpio.pi()
if not pi.connected:
    print("Failed to connect to pigpiod")
    exit(1)

pi.set_mode(M1_PWM_PIN, pigpio.OUTPUT)
pi.set_mode(M2_PWM_PIN, pigpio.OUTPUT)
pi.set_mode(M1_INA_PIN, pigpio.OUTPUT)
pi.set_mode(M1_INB_PIN, pigpio.OUTPUT)
pi.set_mode(M2_INA_PIN, pigpio.OUTPUT)
pi.set_mode(M2_INB_PIN, pigpio.OUTPUT)
pi.set_mode(M3_PWM_PIN, pigpio.OUTPUT)
pi.set_mode(M3_INA_PIN, pigpio.OUTPUT)
pi.set_mode(M3_INB_PIN, pigpio.OUTPUT)

pi.write(M1_INA_PIN, 1)
pi.write(M1_INB_PIN, 0)
pi.write(M2_INA_PIN, 1)
pi.write(M2_INB_PIN, 0)
pi.write(M3_INA_PIN, 1)
pi.write(M3_INB_PIN, 0)

pi.set_PWM_frequency(M1_PWM_PIN, 100)
pi.set_PWM_frequency(M2_PWM_PIN, 100)
pi.set_PWM_frequency(M3_PWM_PIN, 100)

print("Starting M1...")
# pi.set_PWM_dutycycle(M1_PWM_PIN, int(50 * 2.55))
# time.sleep(2)

# print("Starting M2 (M1 should keep running)...")
pi.set_PWM_dutycycle(M3_PWM_PIN, int(50 * 2.55))
time.sleep(5)

print("Stopping...")
pi.set_PWM_dutycycle(M1_PWM_PIN, 0)
pi.set_PWM_dutycycle(M3_PWM_PIN, 0)
pi.stop()