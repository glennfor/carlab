from collections import namedtuple
from enum import Enum

import pigpio


class Direction(Enum):
    STOP = 0
    FORWARD = 1
    BACKWARD = -1

class Motor:
    PWM_FREQUENCY = 1000
    def __init__(self, pi, pwm_pin, ina_pin, inb_pin, name = None):
        '''
        Initialize the motor.
        :param pi: pigpio instance
        :param pwm_pin: the pin number of the PWM pin
        :param ina_pin: the pin number of the ina pin
        :param inb_pin: the pin number of the inb pin
        '''
        self.name = name if name else f"Motor {self.pwm_pin}"
        self.pi = pi
        self.pwm_pin = pwm_pin
        self.ina_pin = ina_pin
        self.inb_pin = inb_pin

        self.direction = Direction.STOP
        self.velocity = 0
        self.speed = 0

        self.init()

    def init(self):
        self.pi.set_mode(self.pwm_pin, pigpio.OUTPUT)
        self.pi.hardware_PWM(self.pwm_pin, self.PWM_FREQUENCY, 0)
        self.pi.set_mode(self.ina_pin, pigpio.OUTPUT)
        self.pi.set_mode(self.inb_pin, pigpio.OUTPUT)
        self.pi.write(self.ina_pin, 0)
        self.pi.write(self.inb_pin, 0)

    def cleanup(self):
        self.pi.hardware_PWM(self.pwm_pin, self.PWM_FREQUENCY, 0)
        self.pi.write(self.ina_pin, 0)
        self.pi.write(self.inb_pin, 0)

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
        print(f"{self.name} set to {abs(velocity)}% in direction {direction}")

        
    def _speed_to_pwm_duty_cycle_exponential(self, speed):
        """
        Exponential mapping with deadzone removal.

        speed: 0-100 input
        min_duty: minimum duty fraction (0.0-1.0) needed for motor to start
        exponent: curve steepness (>1 = smoother low-speed control)

        Returns duty: 0-1,000,000
        """
        speed = max(0, min(100, speed))

        if speed == 0:
            return 0

        MIN_DUTY = 0.25
        EXPONENT = 2.2

        MAX_PWM = 1_000_000

        x = speed / 100.0
        y = MIN_DUTY + (1 - MIN_DUTY) * (x ** EXPONENT)

        return int(y * 1_000_000)
    
    def _speed_to_pwm_duty_cycle_linear(self, speed):
        """
        Linear mapping: speed 0–100% → PWM 0–1,000,000.
        """
        speed = max(0, min(100, speed))
        return int((speed / 100.0) * 1_000_000)

    def set_speed(self, speed):
        '''
        Set the speed of the motor.
        :param speed: 0 to 100
        '''
        speed = max(0, min(100, speed))
        self.speed = speed
        duty_cycle = self._speed_to_pwm_duty_cycle_exponential(speed)
        print(self.name, duty_cycle)
        self.pi.hardware_PWM(self.pwm_pin, self.PWM_FREQUENCY, duty_cycle)
    
    def set_direction(self, direction):
        self.direction = direction
        if direction == Direction.FORWARD:
            self.pi.write(self.ina_pin, 1)
            self.pi.write(self.inb_pin, 0)
        elif direction == Direction.BACKWARD:
            self.pi.write(self.ina_pin, 0)
            self.pi.write(self.inb_pin, 1)
        else:
            self.pi.write(self.ina_pin, 0)
            self.pi.write(self.inb_pin, 0)
    
    def brake(self):
        self.set_direction(Direction.STOP)
        self.pi.write(self.ina_pin, 0)
        self.pi.write(self.inb_pin, 0)
        self.set_speed(0)
    
    def coast(self):
        self.set_direction(Direction.STOP)
        self.pi.write(self.ina_pin, 1)
        self.pi.write(self.inb_pin, 1)
        self.set_speed(0)

    def get_velocity(self):
        return self.velocity

    def get_speed(self):
        return self.speed

    def get_direction(self):
        return self.direction
