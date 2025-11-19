"""
Example usage of offline TTS using Piper.

This example demonstrates how to use the local, offline TTS system
that doesn't require an internet connection.

Prerequisites:
- Piper TTS installed and available in PATH
- Audio model files available (e.g., en_US-amy-medium.onnx)
- ALSA audio system configured (aplay command)
"""

from tts.speak import speak, speak_async
import time


def example_synchronous():
    """Example of synchronous text-to-speech."""
    print("Example 1: Synchronous TTS")
    print("Speaking: 'Hello, this is a test of the offline TTS system.'")
    speak("Hello, this is a test of the offline TTS system.")
    print("Done!\n")


def example_asynchronous():
    """Example of asynchronous text-to-speech."""
    print("Example 2: Asynchronous TTS")
    print("Starting async speech...")
    
    # Start speaking in background
    thread = speak_async("This is being spoken asynchronously, so the program can continue running.")
    
    # Do other work while speaking
    print("Program continues while speech is playing...")
    for i in range(3):
        print(f"  Working... {i+1}")
        time.sleep(0.5)
    
    # Wait for speech to finish
    thread.join()
    print("Speech finished!\n")


def example_multiple_phrases():
    """Example of speaking multiple phrases."""
    print("Example 3: Multiple phrases")
    
    phrases = [
        "First phrase.",
        "Second phrase.",
        "Third phrase."
    ]
    
    for i, phrase in enumerate(phrases, 1):
        print(f"Speaking phrase {i}: {phrase}")
        speak(phrase)
        time.sleep(0.5)  # Small pause between phrases
    
    print("All phrases spoken!\n")


def example_interactive():
    """Example of interactive TTS."""
    print("Example 4: Interactive TTS")
    print("Enter text to speak (or 'quit' to exit):")
    
    while True:
        text = input("> ")
        if text.lower() in ['quit', 'exit', 'q']:
            break
        
        if text.strip():
            print(f"Speaking: {text}")
            speak(text)
        else:
            print("Please enter some text.")


if __name__ == "__main__":
    print("=" * 60)
    print("Offline TTS (Piper) Examples")
    print("=" * 60)
    print()
    
    try:
        # Run examples
        example_synchronous()
        time.sleep(1)
        
        example_asynchronous()
        time.sleep(1)
        
        example_multiple_phrases()
        
        # Uncomment to run interactive example
        # example_interactive()
        
        print("=" * 60)
        print("All examples completed!")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
    except Exception as e:
        print(f"\nError: {e}")
        print("Make sure Piper TTS is installed and audio is configured.")

