
import base64
import io
import os
import subprocess
import tempfile
import threading
import wave

import pyaudio
from google import genai
from google.genai import types


class GoogleLLM:
    def __init__(self, api_key=None, model="gemini-2.5-flash", functions:list[Function] = []):
        """
        Initialize Google GenAI TTS client.
        
        Args:
            api_key: Google GenAI API key. If None, uses GEMINI_API_KEY env var.
            model: TTS model name (default: "gemini-2.5-flash-preview-tts")
            voice_name: Voice name from available options (default: "Kore")
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key required. Set GEMINI_API_KEY environment variable "
                "or pass api_key parameter."
            )

        self.client = genai.Client(api_key=self.api_key)

        house_tools = [
            types.Tool(function_declarations=functions) 
        ]
        config = types.GenerateContentConfig(
            tools=house_tools,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(
                disable=True
            ),
            # Force the model to call 'any' function, instead of chatting.
            tool_config=types.ToolConfig(
                function_calling_config=types.FunctionCallingConfig(mode='ANY')
            ),
        )

        self.chat = self.client.chat(model=model, config=config)
        
    
    def ask(self, text):
        response = self.chat.send_message(text)
        function_calls = response.function_calls
        speech = response.text
        return speech, function_calls
    

if __name__ == "__main__":
    def get_weather(city: str) -> str:
        return f"The weather in {city} is sunny."
    
    llm = GoogleLLM()
    speech, function_calls = llm.ask("What is the weather in Tokyo?")
    print(speech)
    print(function_calls)