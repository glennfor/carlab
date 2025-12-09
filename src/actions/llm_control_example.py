"""
Example usage of the LLM-based robot control system.

This demonstrates the new paradigm where:
1. User provides text instructions (from terminal for testing, or transcribed from mic in production)
2. LLM validates the request and creates a plan using capabilities
3. Instructions execute sequentially with hand-the-baton style for mutually exclusive operations
"""

import os
from actions.llm_command_interface import LLMCommandInterface


def main():
    """Run example LLM control interface."""
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("Warning: OPENAI_API_KEY not set. Some features may not work.")
        print("Set it with: export OPENAI_API_KEY='your-key-here'")
    
    interface = LLMCommandInterface(openai_api_key=api_key)
    
    print("\n" + "=" * 60)
    print("LLM Robot Control System")
    print("=" * 60)
    print("\nExample commands you can try:")
    print("  - 'take a small step forward'")
    print("  - 'turn left a little bit'")
    print("  - 'spin in place to the right'")
    print("  - 'take a picture'")
    print("  - 'say hello'")
    print("  - 'dance for me'")
    print("  - 'drive in a box pattern'")
    print("  - 'status' (check execution status)")
    print("  - 'quit' (exit)")
    print("\n" + "=" * 60 + "\n")
    
    interface.run_interactive()


if __name__ == "__main__":
    main()

