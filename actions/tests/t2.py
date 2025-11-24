import pigpio
pi = pigpio.pi()
if not pi.connected:
    print("Failed to connect to pigpiod")
else:
    print("Pigpio is working!")
pi.stop()
