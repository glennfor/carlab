import cv2
import cv2.aruco as aruco

def detect_aruco(image_path):
    # Load image
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Could not read image from {image_path}")
        return

    # Convert to grayscale (Aruco detection works on grayscale)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Use 6x6 dictionary (250 possible markers)
    aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_6X6_50)
    parameters = aruco.DetectorParameters()

        # 1. Adaptive Thresholding: 
    # Look at a wider range of window sizes. This helps if the glare dominates small windows.
    parameters.adaptiveThreshWinSizeMin = 3
    parameters.adaptiveThreshWinSizeMax = 50  # Increase max window size
    parameters.adaptiveThreshWinSizeStep = 5 

    # 2. Error Correction:
    # Increase the error correction rate. ArUco has redundancy; this tells it 
    # to "guess" more aggressively if a few bits (like the ones under glare) are wrong.
    parameters.errorCorrectionRate = 0.8  # Default is usually around 0.6

    # Detect markers
    corners, ids, rejected = aruco.detectMarkers(gray, aruco_dict, parameters=parameters)

    if ids is not None:
        print(f"Detected {len(ids)} marker(s) with IDs: {ids.flatten()}")
    else:
        print("No Aruco markers detected.")

# Example usage:
image_path = "captured_image2.jpg"  # Replace with your image path
detect_aruco(image_path)
