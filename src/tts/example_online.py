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
import sys
import time

# Handle both direct execution and module import
try:
    from .google_tts import GoogleTTS
except ImportError:
    # If relative import fails, try absolute import
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from tts.google_tts import GoogleTTS


# example_asynchronous_tts
# example_custom_voice
# example_prompt_to_speech
# example_async_prompt_to_speech



def example_advanced_usage():
    """Example of advanced usage with custom instance."""
    print("Example 6: Advanced Usage with Custom Instance")
    
    text = '''
        Robotic systems are quickly becoming more capable and adaptable, entering new domains from transportation to healthcare.
     To reliably carry out complex tasks in changing environments and around people, these systems rely on increasingly sophisticated 
     artificial intelligence. This course covers the core concepts and techniques underpinning modern robot autonomy, including planning 
     under uncertainty, imitation and reinforcement learning, multiagent interaction, and safety. The lab component introduces the Robot 
     Operating System (ROS) framework and applies the learned theory to hands-on autonomous driving assignments on 1/16-scale robot trucks.
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
    
    try:
        # Create custom TTS instance
        tts = GoogleTTS(
            api_key=os.getenv("GEMINI_API_KEY"),
            model="gemini-2.5-flash-preview-tts",
            voice_name="Kore"
        )
        
        print("Using custom TTS instance...")

        text = ''
        while text != 'quit':
            text = input('> ') 
            tts.speak(text)       
        
        tts.close()
        print("Custom instance closed.\n")
    except Exception as e:
        print(f"Error: {e}\n")


def example_continuous_interactive():
    """Example of continuous interactive TTS - continuously enter text to be spoken."""
    print("Example 8: Continuous Interactive TTS")
    print("=" * 60)
    print("Enter text to speak it. Type 'quit', 'exit', or 'q' to exit.")
    print("=" * 60)
    print()
    
    try:
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
                speak(text)
                print("Done.\n")
            except Exception as e:
                print(f"Error: {e}\n")
    
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
    except Exception as e:
        print(f"\nError: {e}")


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
        # example_interactive()



        # example_advanced_usage()
        
        # Uncomment to run interactive examples
        # example_interactive()
        # example_continuous_interactive()
        
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

