

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
        print('Called LLM with: ', text)
        try:
            print('Sending message to LLM...')
            start_time = time.time()
            response = self.chat.send_message(text)
            elapsed = time.time() - start_time
            print(f'LLM response received after {elapsed:.2f} seconds')
            
            # Debug: print response object type and attributes
            print(f'Response type: {type(response)}')
            print(f'Response dir: {[attr for attr in dir(response) if not attr.startswith("_")]}')
            
            # Safely access response attributes
            function_calls = getattr(response, 'function_calls', None)
            speech = getattr(response, 'text', None)
            
            # If text is not directly available, try to extract from candidates
            if speech is None:
                if hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                        text_parts = []
                        for part in candidate.content.parts:
                            if hasattr(part, 'text'):
                                text_parts.append(part.text)
                        speech = ' '.join(text_parts) if text_parts else None
            
            print('Got---- speech: ', speech)
            print('Got---- function_calls: ', function_calls)
            
            return speech or "", function_calls or []
        except Exception as e:
            print(f'ERROR in LLM respond: {type(e).__name__}: {e}')
            import traceback
            traceback.print_exc()
            return "", []
    

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