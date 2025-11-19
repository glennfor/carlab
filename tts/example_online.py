"""
Example usage of online TTS using Google GenAI (Gemini) API.

This example demonstrates how to use the cloud-based TTS system
with both direct text-to-speech and prompt-to-speech modes.

Prerequisites:
- Google GenAI API key (set GEMINI_API_KEY environment variable)
- Internet connection
- PyAudio installed and configured
"""

import os
import time

from .google_tts import (GoogleTTS, speak, speak_async, speak_from_prompt,
                            speak_from_prompt_async)


def example_synchronous_tts():
    """Example of synchronous direct text-to-speech."""
    print("Example 1: Synchronous Direct TTS")
    print("Speaking: 'Hello, this is Google GenAI TTS.'")
    
    try:
        speak("Hello, this is Google GenAI TTS.")
        print("Done!\n")
    except Exception as e:
        print(f"Error: {e}\n")


def example_asynchronous_tts():
    """Example of asynchronous direct text-to-speech."""
    print("Example 2: Asynchronous Direct TTS")
    print("Starting async speech...")
    
    try:
        # Start speaking in background
        thread = speak_async("This is being spoken asynchronously using Google GenAI.")
        
        # Do other work while speaking
        print("Program continues while speech is playing...")
        for i in range(3):
            print(f"  Working... {i+1}")
            time.sleep(0.5)
        
        # Wait for speech to finish
        thread.join()
        print("Speech finished!\n")
    except Exception as e:
        print(f"Error: {e}\n")


def example_custom_voice():
    """Example of using different voices."""
    print("Example 3: Custom Voice Selection")
    
    voices = ["Kore", "Puck", "Zephyr", "Fenrir"]
    
    for voice in voices:
        print(f"Speaking with voice '{voice}': 'This is the {voice} voice.'")
        try:
            speak(f"This is the {voice} voice.", voice_name=voice)
            time.sleep(1)
        except Exception as e:
            print(f"Error with voice {voice}: {e}")
    
    print()


def example_prompt_to_speech():
    """Example of prompt-to-speech mode."""
    print("Example 4: Prompt-to-Speech Mode")
    print("Generating content from prompt and speaking it...")
    
    prompts = [
        "Tell me a short joke about robots.",
        "Explain what artificial intelligence is in one sentence.",
        "Give me a motivational quote."
    ]
    
    for i, prompt in enumerate(prompts, 1):
        print(f"\nPrompt {i}: {prompt}")
        try:
            speak_from_prompt(prompt)
            time.sleep(1)
        except Exception as e:
            print(f"Error: {e}")
    
    print()


def example_async_prompt_to_speech():
    """Example of asynchronous prompt-to-speech."""
    print("Example 5: Asynchronous Prompt-to-Speech")
    print("Generating and speaking asynchronously...")
    
    try:
        thread = speak_from_prompt_async(
            "Generate a short story about a robot learning to paint."
        )
        
        print("Waiting for content generation and speech...")
        thread.join()
        print("Done!\n")
    except Exception as e:
        print(f"Error: {e}\n")


def example_advanced_usage():
    """Example of advanced usage with custom instance."""
    print("Example 6: Advanced Usage with Custom Instance")
    
    text = '''
    At Princeton University, **ECE 302** is a laboratory-based course called **Robotic and Autonomous Systems Lab**. The course is centered around a semester-long design project, typically involving building a computer-controlled vehicle. It integrates concepts from microprocessors, communications, and control systems.

ECE 302 usually requires **ECE 201** and **ECE 203** as prerequisites and is part of the junior-year design requirement for Electrical and Computer Engineering majors. The course is hands-on and project-focused, and many students consider the “Car Lab” projects a highlight, as they get to design, build, and program autonomous vehicles in teams.

If you want, I can summarize what a typical semester looks like in ECE 302, including the kind of assignments and projects students do.

    '''
    try:
        # Create custom TTS instance
        tts = GoogleTTS(
            api_key=os.getenv("GEMINI_API_KEY"),
            model="gemini-2.5-flash-preview-tts",
            voice_name="Kore"
        )
        
        print("Using custom TTS instance...")
        tts.speak(text)
        
        # Use async methods
        # thread = tts.speak_async("This is async with custom instance.")
        # thread.join()
        
        # # Prompt-to-speech with custom instance
        # tts.speak_from_prompt("Tell me a fun fact about space.")
        
        # Clean up
        tts.close()
        print("Custom instance closed.\n")
    except Exception as e:
        print(f"Error: {e}\n")


def example_interactive():
    """Example of interactive TTS with mode selection."""
    print("Example 7: Interactive TTS")
    print("Choose mode:")
    print("  1. Direct TTS (speak text directly)")
    print("  2. Prompt-to-Speech (generate content then speak)")
    print("  Type 'quit' to exit")
    
    while True:
        mode = input("\nSelect mode (1/2/quit): ").strip().lower()
        
        if mode == 'quit':
            break
        
        if mode == '1':
            text = input("Enter text to speak: ")
            if text.strip():
                try:
                    speak(text)
                except Exception as e:
                    print(f"Error: {e}")
        
        elif mode == '2':
            prompt = input("Enter prompt: ")
            if prompt.strip():
                try:
                    speak_from_prompt(prompt)
                except Exception as e:
                    print(f"Error: {e}")
        
        else:
            print("Invalid mode. Choose 1, 2, or 'quit'.")


def check_api_key():
    """Check if API key is configured."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("WARNING: GEMINI_API_KEY environment variable not set!")
        print("Please set it with: export GEMINI_API_KEY='your-api-key'")
        print()
        return False
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("Online TTS (Google GenAI) Examples")
    print("=" * 60)
    print()
    
    if not check_api_key():
        print("Cannot run examples without API key.")
        exit(1)
    
    try:
        # Run examples
        # example_synchronous_tts()
        # time.sleep(1)
        
        # example_asynchronous_tts()
        # time.sleep(1)
        
        # example_custom_voice()
        # time.sleep(1)
        
        # example_prompt_to_speech()
        # time.sleep(1)
        
        # example_async_prompt_to_speech()
        # time.sleep(1)
        
        example_advanced_usage()
        
        # Uncomment to run interactive example
        # example_interactive()
        
        print("=" * 60)
        print("All examples completed!")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
    except Exception as e:
        print(f"\nError: {e}")
        print("Make sure:")
        print("  1. GEMINI_API_KEY is set correctly")
        print("  2. Internet connection is available")
        print("  3. PyAudio is installed and configured")

