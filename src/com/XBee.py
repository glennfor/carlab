import serial

ser = serial.Serial('/dev/ttyAMA0', 115200, timeout=1)

while True:
    if ser.in_waiting:
        data = ser.readline().decode(errors='ignore').strip()
        print("Received:", data)

class XBeeCommunicator:
    pass
# pip install pyserial
# listen to uart input on rpi