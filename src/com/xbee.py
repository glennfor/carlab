import serial




class XBeeCommunicator:
    def __init__(self, ):
        self.serial = None #serial.Serial('/dev/ttyAMA0', 115200, timeout=1)
        pass
    
    def start(self):
        pass

    def _listen_loop(self, ):
        if self.serial is None:
            return
        while True:
            if self.serial.in_waiting:
                data = ser.readline().decode(errors='ignore').strip()
                print("Received:", data)

# pip install pyserial
# listen to uart input on rpi