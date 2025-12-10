"""
Example usage of online TTS using OpenAI TTS API.

This example demonstrates how to use the cloud-based TTS system
with both direct text-to-speech and prompt-to-speech modes.

Prerequisites:
- OpenAI API key (set OPENAI_API_KEY environment variable)
- Internet connection
- PyAudio installed and configured
"""

import os
import sys
import time

# Handle both direct execution and module import
try:
    from .openai_tts import OpenAITTS
except ImportError:
    # If relative import fails, try absolute import
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from tts.openai_tts import OpenAITTS


def example_synchronous_tts():
    """Example of synchronous direct text-to-speech."""
    print("Example 1: Synchronous Direct TTS")
    print("Speaking: 'Hello, this is OpenAI TTS.'")
    
    try:
        tts = OpenAITTS()
        tts.speak("Hello, this is OpenAI TTS.")
        tts.close()
        print("Done!\n")
    except Exception as e:
        print(f"Error: {e}\n")


def example_asynchronous_tts():
    """Example of asynchronous direct text-to-speech."""
    print("Example 2: Asynchronous Direct TTS")
    print("Starting async speech...")
    
    try:
        tts = OpenAITTS()
        # Start speaking in background
        thread = tts.speak_async("This is being spoken asynchronously using OpenAI TTS.")
        
        # Do other work while speaking
        print("Program continues while speech is playing...")
        for i in range(3):
            print(f"  Working... {i+1}")
            time.sleep(0.5)
        
        # Wait for speech to finish
        thread.join()
        tts.close()
        print("Speech finished!\n")
    except Exception as e:
        print(f"Error: {e}\n")


def example_custom_voice():
    """Example of using different voices."""
    print("Example 3: Custom Voice Selection")
    
    voices = ["alloy", "ash", "ballad", "coral", "echo", "fable", "onyx", "nova", "sage", "shimmer"]
    
    try:
        for voice in voices[:4]:  # Test first 4 voices
            print(f"Speaking with voice '{voice}': 'This is the {voice} voice.'")
            tts = OpenAITTS(voice=voice)
            tts.speak(f"This is the {voice} voice.")
            tts.close()
            time.sleep(1)
        print()
    except Exception as e:
        print(f"Error: {e}\n")


def example_prompt_to_speech():
    """Example of prompt-to-speech mode."""
    print("Example 4: Prompt-to-Speech Mode")
    print("Generating content from prompt and speaking it...")
    
    prompts = [
        "Tell me a short joke about robots.",
        "Explain what artificial intelligence is in one sentence.",
        "Give me a motivational quote."
    ]
    
    try:
        tts = OpenAITTS()
        for i, prompt in enumerate(prompts, 1):
            print(f"\nPrompt {i}: {prompt}")
            tts.speak_from_prompt(prompt)
            time.sleep(1)
        tts.close()
        print()
    except Exception as e:
        print(f"Error: {e}\n")


def example_async_prompt_to_speech():
    """Example of asynchronous prompt-to-speech."""
    print("Example 5: Asynchronous Prompt-to-Speech")
    print("Generating and speaking asynchronously...")
    
    try:
        tts = OpenAITTS()
        thread = tts.speak_from_prompt_async(
            "Generate a short story about a robot learning to paint."
        )
        
        print("Waiting for content generation and speech...")
        thread.join()
        tts.close()
        print("Done!\n")
    except Exception as e:
        print(f"Error: {e}\n")


def example_advanced_usage():
    """Example of advanced usage with custom instance."""
    print("Example 6: Advanced Usage with Custom Instance")
    
    try:
        # Create custom TTS instance
        tts = OpenAITTS(
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4o-mini-tts",
            voice="alloy"
        )
        
        print("Using custom TTS instance...")
        tts.speak("This is using a custom TTS instance.")
        
        # Use async methods
        thread = tts.speak_async("This is async with custom instance.")
        thread.join()
        
        # Prompt-to-speech with custom instance
        tts.speak_from_prompt("Tell me a fun fact about space.")
        
        # Clean up
        tts.close()
        print("Custom instance closed.\n")
    except Exception as e:
        print(f"Error: {e}\n")


def example_continuous_interactive():
    """Example of continuous interactive TTS - continuously enter text to be spoken."""
    print("Example 7: Continuous Interactive TTS")
    print("=" * 60)
    print("Enter text to speak it. Type 'quit', 'exit', or 'q' to exit.")
    print("=" * 60)
    print()
    
    try:
        tts = OpenAITTS()
        
        while True:
            text = input("Enter text to speak (or 'quit' to exit): ").strip()
            
            if not text:
                continue
            
            # Check for quit commands
            if text.lower() in ['quit', 'exit', 'q']:
                print("Exiting...")
                break
            
            # Speak the text
            try:
                print(f"Speaking: {text}")
                tts.speak(text)
                print("Done.\n")
            except Exception as e:
                print(f"Error: {e}\n")
        
        tts.close()
    
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
    except Exception as e:
        print(f"\nError: {e}")


def check_api_key():
    """Check if API key is configured."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("WARNING: OPENAI_API_KEY environment variable not set!")
        print("Please set it with: export OPENAI_API_KEY='your-api-key'")
        print()
        return False
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("OpenAI TTS Examples")
    print("=" * 60)
    print()
    
    if not check_api_key():
        print("Cannot run examples without API key.")
        exit(1)
    
    try:
        # Run examples
        example_synchronous_tts()
        time.sleep(1)
        
        example_asynchronous_tts()
        time.sleep(1)
        
        example_custom_voice()
        time.sleep(1)
        
        example_prompt_to_speech()
        time.sleep(1)
        
        example_async_prompt_to_speech()
        time.sleep(1)
        
        example_advanced_usage()
        
        # Uncomment to run interactive example
        # example_continuous_interactive()
        
        print("=" * 60)
        print("All examples completed!")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
    except Exception as e:
        print(f"\nError: {e}")
        print("Make sure:")
        print("  1. OPENAI_API_KEY is set correctly")
        print("  2. Internet connection is available")
        print("  3. PyAudio is installed and configured")

