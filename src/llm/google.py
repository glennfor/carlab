
import subprocess
import tempfile
import os
import base64
import base64
import os
import threading
import io
import wave
import pyaudio
from google import genai
from google.genai import types


class GoogleLLM:
    def __init__(self, api_key=None, model="gemini-2.5-flash-preview-tts", voice_name="Kore"):
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
        self.model = model
        
    
    def ask(self, text):
        """
        Synthesize speech from text using Gemini TTS API.
        
        Args:
            text: Text to convert to speech
            
        Returns:
            bytes: Raw PCM audio data
        """
        response = self.client.models.generate_content(
            model=self.model,
            contents=text,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=self.voice_name,
                        )
                    )
                ),
            )
        )
        
        # extract functions to call
        # and text to speal here ; should match teh expcted output
    
   