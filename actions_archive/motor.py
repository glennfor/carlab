from collections import namedtuple

import RPi.GPIO as GPIO

from enum import Enum

class Direction(Enum):
    STOP = 0
    FORWARD = 1
    BACKWARD = -1

class Motor:
    PWM_FREQUENCY = 100
    def __init__(self, pwm_pin, ina_pin, inb_pin):
        '''
        Initialize the motor.
        :param pwm_pin: the pin number of the PWM pin
        :param ina_pin: the pin number of the ina pin
        :param inb_pin: the pin number of the inb pin
        '''
        self.pwm_pin = pwm_pin
        self.ina_pin = ina_pin
        self.inb_pin = inb_pin

        self.direction = Direction.STOP
        self.velocity = 0
        self.speed = 0

        self.init()

    def init(self):
        GPIO.setup(self.pwm_pin, GPIO.OUT)
        self.pwm = GPIO.PWM(self.pwm_pin, self.PWM_FREQUENCY)
        self.pwm.start(0)
        GPIO.setup(self.ina_pin, GPIO.OUT)
        GPIO.setup(self.inb_pin, GPIO.OUT)
        GPIO.output(self.ina_pin, GPIO.LOW)
        GPIO.output(self.inb_pin, GPIO.LOW)

    def cleanup(self):
        self.pwm.stop()
        GPIO.cleanup(self.ina_pin)
        GPIO.cleanup(self.inb_pin)

    def set_velocity(self, velocity):
        '''
        Set the velocity of the motor.
        :param velocity: -100 to 100
        '''
        velocity = max(-100, min(100, velocity))

        # set direction
        direction = Direction.STOP
        if velocity > 0:
            direction = Direction.FORWARD
        elif velocity < 0:
            direction = Direction.BACKWARD
        self.set_direction(direction)

        # set speed
        self.velocity = velocity
        self.set_speed(abs(velocity))

    def set_speed(self, speed):
        '''
        Set the speed of the motor.
        :param speed: 0 to 100
        '''
        speed = max(0, min(100, speed))
        self.speed = speed
        self.pwm.ChangeDutyCycle(speed)
    
    def set_direction(self, direction):
        self.direction = direction
        if direction == Direction.FORWARD:
            GPIO.output(self.ina_pin, GPIO.HIGH)
            GPIO.output(self.inb_pin, GPIO.LOW)
        elif direction == Direction.BACKWARD:
            GPIO.output(self.ina_pin, GPIO.LOW)
            GPIO.output(self.inb_pin, GPIO.HIGH)
        else:
            GPIO.output(self.ina_pin, GPIO.LOW)
            GPIO.output(self.inb_pin, GPIO.LOW)
    
    def brake(self):
        self.set_direction(Direction.STOP)
        GPIO.output(self.ina_pin, GPIO.LOW)
        GPIO.output(self.inb_pin, GPIO.LOW)
        self.set_speed(0)
    
    def coast(self):
        self.set_direction(Direction.STOP)
        GPIO.output(self.ina_pin, GPIO.HIGH)
        GPIO.output(self.inb_pin, GPIO.HIGH)
        self.set_speed(0)

    def get_velocity(self):
        return self.velocity

    def get_speed(self):
        return self.speed

    def get_direction(self):
        return self.direction
