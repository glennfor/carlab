import signal
import sys
import sounddevice as sd
from scipy.io.wavfile import write

from actions.car import Car
from actions.controllers import ControllerManager, LLMController
from actions.engine import initialize
from asr.transcribe import transcribe
from llm.brain import ask_brain
from tts.speak import speak
from wakeword.hotword import listen_for_wakeword


def record_command():
    print("Listening...")
    fs = 16000
    duration = 4
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()
    write("audio.wav", fs, audio)


def setup_controllers():
    """Initialize car and controller system."""
    car = Car()
    manager = ControllerManager(car, update_rate=20.0)
    
    llm_controller = LLMController(priority=20)
    manager.add_controller(llm_controller)
    
    initialize(car=car, controller_manager=manager)
    
    return car, manager


def cleanup_controllers(car, manager):
    """Clean up controllers and car."""
    manager.stop()
    car.cleanup()


def signal_handler(sig, frame, car, manager):
    """Handle shutdown signals."""
    print("\nShutting down...")
    cleanup_controllers(car, manager)
    sys.exit(0)


def main():
    """Main loop for voice-controlled car."""
    car, manager = setup_controllers()
    
    signal.signal(signal.SIGINT, lambda s, f: signal_handler(s, f, car, manager))
    signal.signal(signal.SIGTERM, lambda s, f: signal_handler(s, f, car, manager))
    
    try:
        manager.start()
        print("Voice control system started. Waiting for wake word...")
        
        while True:
            listen_for_wakeword()
            speak("Yes?")
            record_command()

            text = transcribe("audio.wav")
            print("You said:", text)

            resp = ask_brain(text)
            speak(resp["speech"])

            if "action" in resp:
                from actions.engine import execute
                execute(resp["action"], resp["value"])
    
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cleanup_controllers(car, manager)


if __name__ == '__main__':
    main()
