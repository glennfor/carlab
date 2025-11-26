import time

import RPi.GPIO as GPIO

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

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

GPIO.setup(M1_PWM_PIN, GPIO.OUT)
GPIO.setup(M2_PWM_PIN, GPIO.OUT)
GPIO.setup(M1_INA_PIN, GPIO.OUT)
GPIO.setup(M1_INB_PIN, GPIO.OUT)
GPIO.setup(M2_INA_PIN, GPIO.OUT)
GPIO.setup(M2_INB_PIN, GPIO.OUT)
GPIO.setup(M3_PWM_PIN, GPIO.OUT)
GPIO.setup(M3_INA_PIN, GPIO.OUT)
GPIO.setup(M3_INB_PIN, GPIO.OUT)

GPIO.output(M1_INA_PIN, GPIO.HIGH)
GPIO.output(M1_INB_PIN, GPIO.LOW)
GPIO.output(M2_INA_PIN, GPIO.HIGH)
GPIO.output(M2_INB_PIN, GPIO.LOW)
GPIO.output(M3_INA_PIN, GPIO.HIGH)
GPIO.output(M3_INB_PIN, GPIO.LOW)

m1_pwm = GPIO.PWM(M1_PWM_PIN, 100)
m2_pwm = GPIO.PWM(M2_PWM_PIN, 100)
m3_pwm = GPIO.PWM(M3_PWM_PIN, 100)

m1_pwm.start(0)
m2_pwm.start(0)
m3_pwm.start(0)

print("Starting M1...")
# m1_pwm.ChangeDutyCycle(50)
# time.sleep(2)

# print("Starting M2 (M1 should keep running)...")
m3_pwm.ChangeDutyCycle(50)
time.sleep(5)

print("Stopping...")
m1_pwm.ChangeDutyCycle(0)
m3_pwm.ChangeDutyCycle(0)
m1_pwm.stop()
m2_pwm.stop()
m3_pwm.stop()
GPIO.cleanup()

