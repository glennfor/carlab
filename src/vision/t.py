from picamera2 import Picamera2
import time

# Initialize camera
picam2 = Picamera2()
picam2.start_preview()  # Optional, opens a preview window
time.sleep(2)  # Allow camera to adjust

# Capture image
image = picam2.capture_array()  # Returns a numpy array
# Save image using OpenCV or PIL
import cv2
cv2.imwrite("image.jpg", image)

# Stop preview
picam2.stop_preview()
