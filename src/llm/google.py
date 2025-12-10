

import os
import time
from typing import Any, Callable, List

from google import genai
from google.genai import types


class GoogleLLM:
    def __init__(self, api_key=None, model="gemini-2.5-flash", functions:List[Any] = []):
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

        tools = [
            types.Tool(function_declarations=functions) 
        ]
        config = types.GenerateContentConfig(
            tools=tools,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(
                disable=True
            ),
            system_instruction=[
                types.Part(text="You are the brain of a pet robot."),
                types.Part(text="Always be creative in your responses."),
                types.Part(text="You are able to call functions to perform actions."),
            ]
            # generation_config=types.GenerationConfig(
            #     temperature=0.8,
            #     top_p=0.9,
            #     top_k=40,
            # )
            # # Force the model to call 'any' function, instead of chatting.
            # tool_config=types.ToolConfig(
            #     function_calling_config=types.FunctionCallingConfig(mode='ANY')
            # ),
        )

        self.chat = self.client.chats.create(model=model, config=config,)
        
    
    def respond(self, text):
        response = self.chat.send_message(text)
        function_calls = response.function_calls
        speech = response.text
        return speech, function_calls
    

if __name__ == "__main__":
    def get_weather(city: str) -> str:
        return f"The weather in {city} is sunny."
        # Wrap it as a FunctionDeclaration for the LLM
    weather_function = {
        "name": "get_weather",
        "description": "Get the current weather for a specified city.",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "The city to get the weather for"
                }
            },
            "required": ["city"]
        }
    }


    print('Starting LLM')
    llm = GoogleLLM(functions = [weather_function])
    print('Asking')
    then = time.time()
    speech, function_calls = llm.respond("Hey pi")

    print(speech)
    print(function_calls)
    print('Took: ', time.time() - then)