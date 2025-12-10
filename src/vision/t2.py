# import cv2
# from picamera2 import Picamera2

# picam2 = Picamera2()
# # picam2.preview_configuration.main.size = (1280, 720)
# # picam2.preview_configuration.main.format = "RGB888"
# # picam2.preview_configuration.align()
# # picam2.configure("preview")
# picam2.start()

# print('Waiting Now')
# try:
#     while True:
#         im = picam2.capture_array()
#         # cv2.imshow("Camera", im)

#         # Save an image when a key is pressed (e.g., 's')
#         key = cv2.waitKey(1)
#         if key == ord('s'):
#             # Save the image using OpenCV
#             cv2.imwrite("captured_image.jpg", im)
#             print("Image saved!")

#         # Exit the loop when 'q' is pressed
#         elif key == ord('q'):
#             break

# finally:
#     # Release resources
#     cv2.destroyAllWindows()
#     picam2.stop()
#     picam2.close()



import cv2
from picamera2 import Picamera2

# Initialize camera
picam2 = Picamera2()
picam2.start()

try:
    # Capture one image
    image = picam2.capture_array()

    # Example processing: convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Example processing: apply a Gaussian blur
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Save original and processed images
    cv2.imwrite("captured_image2.jpg", image)
    cv2.imwrite("gray_image.jpg", gray)
    cv2.imwrite("blurred_image.jpg", blurred)

    print("Images saved! Original, grayscale, and blurred versions.")
finally:
    picam2.stop()
    picam2.close()
