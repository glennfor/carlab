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
    def _speed_to_pwm_duty_cycle_exponential_old(self, speed):
        """
        Exponential mapping with deadzone removal for RPi.GPIO.

        speed: 0-100 input
        Returns duty: 0-100 float
        """
        speed = max(0, min(100, speed))

        if speed == 0:
            return 0

        # CONFIGURATION
        # MIN_DUTY: The floor (0.0 - 1.0) needed to get the motor actually spinning.
        # usually 0.20 to 0.35 for standard yellow TT motors.
        MIN_DUTY = 0.25 
        
        # EXPONENT: Curve steepness. 
        # 1.0 = Linear
        # 2.0 = Quadratic (smoother low speed)
        EXPONENT = 2.2

        # Normalize speed to 0-1
        x = speed / 100.0
        
        # Apply curve: y = min + (1-min) * x^exp
        y = MIN_DUTY + (1 - MIN_DUTY) * (x ** EXPONENT)

        # Scale back to 0-100 for RPi.GPIO
        return y * 100.0


    def _speed_to_pwm_duty_cycle_exponential(self, speed):
        """
        Exponential PWM mapping with deadzone compensation.
        speed: 0–100
        returns: duty cycle (0–100)
        """
        speed = max(0, min(100, speed))

        if speed == 0:
            return 0

        # minimal duty that actually turns the motor
        MIN_DUTY = 25 / 100.0    # 25%
        
        # how curved the acceleration is
        EXPONENT = 2.2          # 1.0 = linear, 2.0–3.0 better for small motors

        # normalize to 0–1
        x = speed / 100.0

        # exponential curve
        y = MIN_DUTY + (1 - MIN_DUTY) * (x ** EXPONENT)

        return y * 100.0

    
    # def _speed_to_pwm_duty_cycle_linear(self, speed):
    #     """
    #     Linear mapping: speed 0–100% → PWM 0–1,000,000.
    #     """
    #     speed = max(0, min(100, speed))
    #     return int((speed / 100.0) * 1_000_000)

    # def set_speed(self, speed):
    #     '''
    #     Set the speed of the motor.
    #     :param speed: 0 to 100
    #     '''
    #     speed = max(0, min(100, speed))
    #     self.speed = speed
    #     duty_cycle = self._speed_to_pwm_duty_cycle_exponential(speed)
    #     print(self.name, duty_cycle)
    #     self.pi.hardware_PWM(self.pwm_pin, self.PWM_FREQUENCY, duty_cycle)

    def set_speed(self, speed):
        '''
        Set the speed of the motor.
        :param speed: 0 to 100
        '''
        speed = max(0, min(100, speed))
        self.speed = speed
        # duty_cycle = speed; #self._speed_to_pwm_duty_cycle_exponential(speed)
        duty_cycle = self._speed_to_pwm_duty_cycle_exponential(speed)
        self.pwm.ChangeDutyCycle(duty_cycle)
    
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
