import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
print("RPi.GPIO is working!")
GPIO.cleanup()

