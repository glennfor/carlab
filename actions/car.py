import RPi.GPIO as GPIO
from .motor import Motor


class Car:
    # # MOTOR 1 (M1) - ASSUMED PINS: PWM:12, FWD:20, REV:16
    # M1_PWM_PIN = 12
    # M1_IN1_PIN = 20
    # M1_IN2_PIN = 16

    # MOTOR 1 (M1) - ASSUMED PINS: PWM:12, FWD:20, REV:16
    M1_PWM_PIN = 16
    M1_IN1_PIN = 21
    M1_IN2_PIN = 20


    # MOTOR 2 (M2) - ASSUMED PINS: PWM:18, FWD:14, 10(REV)->15
    M2_PWM_PIN = 18
    M2_IN1_PIN = 23
    M2_IN2_PIN = 24

    # MOTOR 3 (M3) - ASSUMED PINS: PWM:13, FWD:5, 31(REV)->6
    M3_PWM_PIN = 13
    M3_IN1_PIN = 5
    M3_IN2_PIN = 6
    

    def __init__(self):
        '''
        For Kiwi Drive, the wheels are mounted at 120 degrees from each other.
        The wheels are mounted at the following angles:
        - M1: 0 degrees
        - M2: 120 degrees
        - M3: 240 degrees

                    Wheel 1
                    (Front)
                       ↑

            Wheel 2         Wheel 3
            (Back-Left)     (Back-Right)
        '''
        GPIO.setmode(GPIO.BCM)
        self.wheels = {
            'Front': Motor(self.M1_PWM_PIN, self.M1_IN1_PIN, self.M1_IN2_PIN), 
            'Left': Motor(self.M2_PWM_PIN, self.M2_IN1_PIN, self.M2_IN2_PIN), 
            'Right': Motor(self.M3_PWM_PIN, self.M3_IN1_PIN, self.M3_IN2_PIN)
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
        
        # Motor 1 (Front/Top)
        S1 = 0 * vx + 1 * vy + rotation
        
        # Motor 2 (Left-Rear)
        S2 = -0.866 * vx - 0.5 * vy + rotation 
        
        # Motor 3 (Right-Rear)
        S3 = 0.866 * vx - 0.5 * vy + rotation
        
        # Normalize speeds
        max_speed_abs = max(abs(S1), abs(S2), abs(S3), 1.0)
        
        M1_speed = (S1 / max_speed_abs) * 100 
        M2_speed = (S2 / max_speed_abs) * 100
        M3_speed = (S3 / max_speed_abs) * 100
        
        self.wheels['Front'].set_velocity(M1_speed)
        self.wheels['Left'].set_velocity(M2_speed)
        self.wheels['Right'].set_velocity(M3_speed)
    
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
