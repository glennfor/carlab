from math import cos, pi, sin

import RPi.GPIO as GPIO

from .motor import Motor


class Car:

    # # MOTOR 1 (M1) - ASSUMED PINS: PWM:13, FWD:5, REV:6
    # M1_PWM_PIN = 13
    # M1_INA_PIN = 5
    # M1_INB_PIN = 6


    # # MOTOR 2 (M2) - ASSUMED PINS: PWM:18, FWD:24, 10(REV)->23
    # M2_PWM_PIN = 22
    # M2_INA_PIN = 17
    # M2_INB_PIN = 27

    # # # MOTOR 3 (M3) - ASSUMED PINS: PWM:16, FWD:21, REV:20
    # # M3_PWM_PIN = 16
    # # M3_INA_PIN = 21
    # # M3_INB_PIN = 20
    
    #  # MOTOR 3 (M3) - ASSUMED PINS: PWM:16, FWD:21, REV:20
    # M3_PWM_PIN = 25
    # M3_INA_PIN = 24
    # M3_INB_PIN = 23


    # Hardware PWM pins

    # M1_PWM_PIN = 19
    # M1_INA_PIN = 17
    # M1_INB_PIN = 27

    # M2_PWM_PIN = 13
    # M2_INA_PIN = 5
    # M2_INB_PIN = 6

    # M3_PWM_PIN = 12
    # M3_INA_PIN = 23
    # M3_INB_PIN = 24

    # --- Motor pin definitions ---
    M1_PWM_PIN = 20#16
    M1_INA_PIN = 5
    M1_INB_PIN = 6

    # M2_PWM_PIN = 22
    M2_PWM_PIN = 26
    M2_INA_PIN = 17
    M2_INB_PIN = 27

    M3_PWM_PIN = 25
    M3_INA_PIN = 24
    M3_INB_PIN = 23

    def __init__(self):
        '''
        For Kiwi Drive, the wheels are mounted at 120 degrees from each other.
        The wheels are mounted at the following angles: 0, 120, 240
        '''
        GPIO.setmode(GPIO.BCM)
        self.wheels = {
            'Left': Motor(self.M1_PWM_PIN, self.M1_INA_PIN, self.M1_INB_PIN), 
            'Right': Motor(self.M2_PWM_PIN, self.M2_INA_PIN, self.M2_INB_PIN), 
            'Front': Motor(self.M3_PWM_PIN, self.M3_INA_PIN, self.M3_INB_PIN)
            }
        self.init()

    def init(self):
        pass
    
    
    def drive(self, vx, vy, rotation):

        '''
        Implements inverse kinematics for a 3-wheel Kiwi Drive.
        
        vx: lateral velocity (left/right)   
        vy: longitudinal velocity (forward/backward)
        rotation: angular velocity (clockwise/counterclockwise)
        '''
    
        # S_i = Vx * cos(theta_i) + Vy * sin(theta_i) + Omega

        S_front =  vx + rotation#0
        S_left  =  -0.5*vx + 0.866*vy + rotation # 2PI/3
        S_right  =  -0.5*vx - 0.866*vy + rotation # -^

        
        # Normalize speeds
        max_speed_abs = max(abs(S_right), abs(S_left), abs(S_front), 1.0)
        
        M_right_velocity = (S_right / max_speed_abs) * 100 
        M_left_velocity = (S_left / max_speed_abs) * 100
        M_front_velocity = (S_front / max_speed_abs) * 100

        self.wheels['Right'].set_velocity(M_right_velocity)
        self.wheels['Left'].set_velocity(M_left_velocity)
        self.wheels['Front'].set_velocity(M_front_velocity)
    
    def strafe(self, vx):
        '''
        Perform a strafe movement.
        :param vx: lateral velocity (left/right)
        '''
        self.drive(vx, 0, 0)

    def forward(self, vy):
        '''
        Perform a forward movement.
        :param vy: longitudinal velocity (forward/backward)
        '''
        self.drive(0, vy, 0)

    def backward(self, vy):
        '''
        Perform a backward movement.
        :param vy: longitudinal velocity (forward/backward)
        '''
        self.drive(0, -vy, 0)
    
    def translate(self, vx, vy):
        '''
        Perform a translation movement.
        :param vx: lateral velocity (left/right)
        :param vy: longitudinal velocity (forward/backward)
        '''
        self.drive(vx, vy, 0)

    def rotate(self, rotation):
        '''
        Perform a rotation around the center of the car.
        :param rotation: angular velocity (clockwise/counterclockwise)
        '''
        self.drive(0, 0, rotation)

    def cleanup(self):
        for wheel in self.wheels.values():
            wheel.cleanup()
        GPIO.cleanup()
