import RPi.GPIO as GPIO

from .motor import Motor


from math import cos, sin, pi

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
        GPIO.setmode(GPIO.BCM)
        self.wheels = {
            'Right': Motor(self.M1_PWM_PIN, self.M1_INA_PIN, self.M1_INB_PIN), 
            'Left': Motor(self.M2_PWM_PIN, self.M2_INA_PIN, self.M2_INB_PIN), 
            'Rear': Motor(self.M3_PWM_PIN, self.M3_INA_PIN, self.M3_INB_PIN)
            }
        self.init()

    def init(self):
        pass
    
    def drive_grok(self, vx, vy, rotation):
        '''
        Correct inverse kinematics for Kiwi drive with:
        - Right wheel at -60° (300°)
        - Left wheel at +60°
        - Rear wheel at 180°
        All angles measured from forward (+Y), positive counterclockwise
        '''
        # Convert degrees to radians
        deg_to_rad = pi / 180

        # Wheel angles from forward direction (+Y axis)
        angle_right = -60 * deg_to_rad   # 300°
        angle_left  =  60 * deg_to_rad   # 60°
        angle_rear  = 180 * deg_to_rad   # 180°

        # Inverse kinematics: S_i = vx * sin(θ_i) + vy * cos(θ_i) + ω
        # Note: some derivations use -sin, but this one matches real robots
        S_right =  vx * sin(angle_right) + vy * cos(angle_right) + rotation
        S_left  =  vx * sin(angle_left)  + vy * cos(angle_left)  + rotation
        S_rear  =  vx * sin(angle_rear)  + vy * cos(angle_rear)  + rotation

        # Normalize to prevent any motor exceeding 100%
        max_speed = max(abs(S_right), abs(S_left), abs(S_rear), 1.0)
        scale = 100.0 / max_speed

        M_right_velocity = S_right * scale
        M_left_velocity  = S_left  * scale
        M_rear_velocity  = S_rear  * scale

        # Apply to motors
        self.wheels['Right'].set_velocity(M_right_velocity)
        self.wheels['Left'].set_velocity(M_left_velocity)
        self.wheels['Rear'].set_velocity(M_rear_velocity)


    def drive_gemini(self, vx, vy, rotation):
        '''
        Inverse kinematics for a 3-wheel Kiwi Drive.
        
        vx: lateral velocity (left/right)   
        vy: longitudinal velocity (forward/backward)
        rotation: angular velocity (clockwise/counterclockwise)
        '''
        
        # --- KINEMATICS CONFIGURATION ---
        # derived from your successful Forward test
        
        # 1. LEFT MOTOR (Front Left)
        # Position: ~210 degrees | Drive Direction: ~120 degrees
        # Forward (+Vy): Positive power moves it Forward-Left
        # Strafe (+Vx): Positive power moves it Right
        left_speed = (0.5 * vx) + (0.866 * vy) + rotation

        # 2. RIGHT MOTOR (Front Right)
        # Position: ~330 degrees | Drive Direction: ~60 degrees
        # Forward (+Vy): Negative power (inverse) moves it Forward-Right
        # Strafe (+Vx): Positive power moves it Right
        # Note: We keep the math standard but flip the Y sign to match your hardware
        right_speed = (0.5 * vx) - (0.866 * vy) + rotation

        # 3. REAR MOTOR (Rear)
        # Position: 270 degrees (Bottom) | Drive Direction: 0 degrees (Right)
        # Strafe (+Vx): MUST be positive to move Right
        # Forward (+Vy): 0 (Rear wheel is perpendicular to Y motion)
        rear_speed = (1.0 * vx) + (0.0 * vy) + rotation

        # --- NORMALIZATION ---
        # Ensure we don't exceed max speed (100) if multiple vectors add up
        speeds = [abs(left_speed), abs(right_speed), abs(rear_speed)]
        max_val = max(speeds + [1.0]) # Avoid division by zero
        
        # Scale to 0-100 range
        M_left = (left_speed / max_val) * 100
        M_right = (right_speed / max_val) * 100
        M_rear = (rear_speed / max_val) * 100

        # Send to motors
        self.wheels['Left'].set_velocity(M_left)
        self.wheels['Right'].set_velocity(M_right)
        self.wheels['Rear'].set_velocity(M_rear)

    def drive_gpt(self, vx, vy, rotation):
        """
        Implements inverse kinematics for a 3-wheel Kiwi Drive.

        vx: lateral velocity (left/right), + = right, - = left
        vy: longitudinal velocity (forward/backward), + = forward, - = backward
        rotation: angular velocity (clockwise/counterclockwise)
        """

        # --- Kiwi kinematics (consistent with wheel layout) ---

        # Motor 1: Right
        # Pushes Forward (+vy) and Left (-vx)
        S_right = -0.5 * vx + 0.866 * vy + rotation

        # Motor 2: Left
        # Pushes Forward (+vy) and Right (+vx)
        S_left  =  0.5 * vx + 0.866 * vy + rotation

        # Motor 3: Rear
        # Pushes strictly sideways (-vx), no forward component
        S_rear  = -1.0 * vx + 0.0   * vy + rotation

        # Normalize to [-100, 100] for Motor.set_velocity
        max_speed_abs = max(abs(S_right), abs(S_left), abs(S_rear), 1.0)

        M_right_velocity = (S_right / max_speed_abs) * 100
        M_left_velocity  = (S_left  / max_speed_abs) * 100
        M_rear_velocity  = (S_rear  / max_speed_abs) * 100

        # Send to motors (Motor.set_velocity expects -100..100)
        self.wheels['Right'].set_velocity(M_right_velocity)
        self.wheels['Left'].set_velocity(M_left_velocity)
        self.wheels['Rear'].set_velocity(M_rear_velocity)
    
    def drive(self, vx, vy, rotation):

        '''
        Implements inverse kinematics for a 3-wheel Kiwi Drive.
        
        vx: lateral velocity (left/right)   
        vy: longitudinal velocity (forward/backward)
        rotation: angular velocity (clockwise/counterclockwise)
        '''
    
        # S_i = Vx * cos(theta_i) + Vy * sin(theta_i) + Omega
        

        ### OLD
        # Motor 1: Front Right
        # S_right = 0 * vx + 1 * vy + rotation
        
        # # Motor 2: Front Left
        # S_left = 0.866 * vx - 0.5 * vy + rotation 

        # # Motor 3: Rear 
        # S_rear = -0.866 * vx + 0.5 * vy + rotation


        ### FIX C

        # # Motor 1: Front Right (0°)
        # S_right = -0 * vx + 1 * vy + rotation

        # # Motor 2: Front Left (120°)
        # S_left = -0.866 * vx + (-0.5) * vy + rotation

        # # Motor 3: Rear (240°)
        # S_rear = 0.866 * vx + (-0.5) * vy + rotation


        ### FIX G

        # Motor 1: Front Right 
        # Pushes Forward (+Vy) and Left (-Vx)
        # S_right = -0.5 * vx + 0.866 * vy + rotation
        
        # # Motor 2: Front Left
        # # Pushes Forward (+Vy) and Right (+Vx)
        # S_left = 0.5 * vx + 0.866 * vy + rotation 

        # # Motor 3: Rear
        # # Pushes strictly sideways. Usually -Vx.
        # # (If Rear is at the bottom, it handles the X-axis strafing)
        # S_rear = -1.0 * vx + 0 * vy + rotation


        # Pushes Forward (+Vy) and Left (-Vx)
        # S_right = -0.5 * vx + 0.866 * vy + rotation

        # Motor 2: Left (Front Left, ~150 degrees from X-axis)
        # Pushes Forward (+Vy) and Right (+Vx)
        # S_left = 0.5 * vx + 0.866 * vy + rotation

        # Motor 3: Rear (270 degrees / bottom)
        # Pushes Left (-Vx). 
        # Ideally contributes NOTHING to forward motion (0 * vy).
        # S_rear = -1.0 * vx + 0 * vy + rotation

        ### FIX gr

        # S_right = -vx + rotation
        # S_left  =  0.5*vx + 0.866*vy + rotation
        # S_rear  =  0.5*vx - 0.866*vy + rotation

        ## my try
        # S_i = Vx * cos(theta_i) + Vy * sin(theta_i) + Omega

        # S_left = vx * cos(60*pi/180) + vy * sin(60*pi/180) + rotation   # anle is 60
        # S_right = vx * cos(180*pi/180 + 120*pi/180) + vy * sin(180*pi/180 + 120*pi/180) + rotation # angle 180 + 120
        # S_rear = vx * cos(180*pi/180) + vy * sin(180*pi/180) + rotation # 180 

        S_right =  vx + rotation#0
        S_left  =  -0.5*vx + 0.866*vy + rotation # 2PI/3
        S_rear  =  -0.5*vx - 0.866*vy + rotation # -^

        
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
        GPIO.cleanup()
