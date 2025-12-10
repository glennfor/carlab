import picamera2


#This class is a wrapper around the picamera2 library.
# and manages the camera from one place.
class Camera:
    def __init__(self):
        self.camera = picamera2.Picamera2()
        self.camera.configure(
            self.camera.create_preview_configuration(
                main={"format": "RGB888", "size": (640, 480)}
            )
        )
        self.camera.start()
        self.running = False
    def start(self):
        if self.running:
            return
        self.running = True
        self.camera.start()

    def stop(self):
        if not self.running:
            return
        self.running = False
        self.camera.stop()

    def is_available(self) -> bool:
        if not self.running:
            return False
        return self.camera.is_available()

    def capture_frame(self):
        if not self.running:
            return None
        return self.camera.capture_array()
    
    def capture_image(self, filename: str = "imgs/captured_image.jpg"):
        if not self.running:
            return
        self.camera.capture_file(filename)

    def close(self):
        if not self.running:
            return
        self.running = False
        self.camera.close()