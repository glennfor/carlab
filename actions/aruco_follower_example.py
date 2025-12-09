"""
Example script for testing ArUco marker following.

This script demonstrates how to use the ArUcoFollower module directly.
For production use, use the LLM command interface: "follow me" or "follow the person"
"""

import signal
import sys
import time

from actions.aruco_follower import ArUcoFollower
from actions.car import Car


def signal_handler(sig, frame, car, follower):
    """Handle shutdown signals."""
    print("\nShutting down...")
    if follower:
        follower.stop()
    car.drive(0, 0, 0)
    car.cleanup()
    sys.exit(0)


def main():
    """Test ArUco following."""
    print("ArUco Follower Test")
    print("=" * 50)
    print("Make sure you have an ArUco marker (ID 0, DICT_4X4_50)")
    print("Hold it in front of the camera to start following")
    print("Press Ctrl+C to stop")
    print("=" * 50)
    
    car = Car()
    follower = ArUcoFollower(
        car=car,
        marker_id=0,
        target_distance=0.8,
        min_distance=0.3
    )
    
    signal.signal(signal.SIGINT, lambda s, f: signal_handler(s, f, car, follower))
    signal.signal(signal.SIGTERM, lambda s, f: signal_handler(s, f, car, follower))
    
    if not follower.is_available():
        print("Error: Camera not available")
        car.cleanup()
        return
    
    try:
        follower.start()
        print("\nFollowing started. Hold the ArUco marker in front of the camera.")
        
        # Keep running until interrupted
        while follower.running:
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        pass
    finally:
        follower.stop()
        car.cleanup()
        print("Stopped")


if __name__ == "__main__":
    main()

