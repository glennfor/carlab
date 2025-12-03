import pigpio

from .motor import Motor

from math import cos, sin, pi

class Car:


    # Software PWM pins

    # MOTOR 1 (M1) - ASSUMED PINS: PWM:13, FWD:5, REV:6
    M1_PWM_PIN = 13
    M1_INA_PIN = 5
    M1_INB_PIN = 6


    # MOTOR 2 (M2) - ASSUMED PINS: PWM:18, FWD:24, 10(REV)->23
    M2_PWM_PIN = 18
    M2_INA_PIN = 24
    M2_INB_PIN = 23

    # MOTOR 3 (M3) - ASSUMED PINS: PWM:16, FWD:21, REV:20
    M3_PWM_PIN = 16
    M3_INA_PIN = 21
    M3_INB_PIN = 20
    

    # Hardware PWM pins
# did not work
    # M1_PWM_PIN = 19
    # M1_INA_PIN = 17
    # M1_INB_PIN = 27

    # M2_PWM_PIN = 13
    # M2_INA_PIN = 5
    # M2_INB_PIN = 6

    # M3_PWM_PIN = 12
    # M3_INA_PIN = 23
    # M3_INB_PIN = 24
    
    def __init__(self):
        '''
        For Kiwi Drive, the wheels are mounted at 120 degrees from each other.
        The wheels are mounted at the following angles:
        - M1: 0 degrees
        - M2: 120 degrees
        - M3: 240 degrees

                          Front
                            ^
                           / \
                Left(W2)  /   \  Right(W1)
                          \   /
                           \ /
                           Rear(W3)

        '''
        self.pi = pigpio.pi()
        if not self.pi.connected:
            raise RuntimeError("Failed to connect to pigpio daemon. Please ensure it's running: 'sudo systemctl start pigpiod'")
        
        self.wheels = {
            'Right': Motor(self.pi, self.M1_PWM_PIN, self.M1_INA_PIN, self.M1_INB_PIN, name='Right Motor'), 
            'Left': Motor(self.pi, self.M2_PWM_PIN, self.M2_INA_PIN, self.M2_INB_PIN, name='Left Motor'), 
            'Rear': Motor(self.pi, self.M3_PWM_PIN, self.M3_INA_PIN, self.M3_INB_PIN, name='Rear Motor')
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

        # Motor 1: Front Right 
        # Pushes Forward (+Vy) and Left (-Vx)
        S_right = -0.5 * vx + 0.866 * vy + rotation
        
        # # Motor 2: Front Left
        # # Pushes Forward (+Vy) and Right (+Vx)
        S_left = 0.5 * vx + 0.866 * vy + rotation 

        # # Motor 3: Rear
        # # Pushes strictly sideways. Usually -Vx.
        # # (If Rear is at the bottom, it handles the X-axis strafing)
        S_rear = -1.0 * vx + 0 * vy + rotation

        # S_left = vx * cos(60*pi/180) + vy * sin(60*pi/180) + rotation   # anle is 60
        # S_right = vx * cos(180*pi/180 + 120*pi/180) + vy * sin(180*pi/180 + 120*pi/180) + rotation # angle 180 + 120
        # S_rear = vx * cos(180*pi/180) + vy * sin(180*pi/180) + rotation 

        # Normalize speeds
        max_speed_abs = max(abs(S_right), abs(S_left), abs(S_rear), 1.0)
        
        M_right_velocity = (S_right / max_speed_abs) * 100 
        M_left_velocity = (S_left / max_speed_abs) * 100
        M_rear_velocity = (S_rear / max_speed_abs) * 100

        self.wheels['Right'].set_velocity(M_right_velocity)
        self.wheels['Left'].set_velocity(M_left_velocity)
        self.wheels['Rear'].set_velocity(M_rear_velocity)
    
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
        if self.pi and self.pi.connected:
            self.pi.stop()
