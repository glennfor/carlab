import base64
import os
import threading

import pyaudio
from google import genai
from google.genai import types


class GoogleTTS:
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
        self.voice_name = voice_name
        
        # PyAudio setup for direct streaming
        self.pyaudio_instance = pyaudio.PyAudio()
        self.sample_rate = 24000
        self.channels = 1
        self.format = pyaudio.paInt16
    
    def _synthesize_speech(self, text):
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
        
        # Extract audio data from response
        if not response.candidates or not response.candidates[0].content.parts:
            raise Exception("No audio data in response")
        
        inline_data = response.candidates[0].content.parts[0].inline_data
        if not inline_data or not inline_data.data:
            raise Exception("No audio data in response parts")
        
        # Decode base64 audio data (handle both string and bytes)
        data = inline_data.data
        if isinstance(data, str):
            audio_data = base64.b64decode(data)
        elif isinstance(data, bytes):
            # Try to decode if it looks like base64, otherwise use as-is
            try:
                audio_data = base64.b64decode(data)
            except Exception:
                audio_data = data
        else:
            raise Exception(f"Unexpected audio data type: {type(data)}")
        
        return audio_data
    
    def _play_audio_stream(self, audio_data):
        """
        Play audio data directly from memory stream.
        
        Args:
            audio_data: Raw PCM audio bytes to play
            
        Raises:
            Exception: If audio playback fails
        """
        try:
            stream = self.pyaudio_instance.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                output=True,
            )
            
            try:
                stream.write(audio_data)
            finally:
                stream.stop_stream()
                stream.close()
        except Exception as e:
            raise Exception(f"Audio playback error: {e}")
    
    def speak(self, text):
        """
        Synthesize and play text synchronously.
        
        Args:
            text: Text to speak
            
        Raises:
            Exception: If TTS synthesis or playback fails
        """
        try:
            audio_data = self._synthesize_speech(text)
            self._play_audio_stream(audio_data)
        except Exception as e:
            raise Exception(f"TTS error: {e}")
    
    def speak_from_prompt(self, prompt, generation_model="gemini-2.0-flash"):
        """
        Generate content from a prompt using Gemini, then convert to speech.
        
        Args:
            prompt: Prompt to generate content from
            generation_model: Model to use for text generation (default: "gemini-2.0-flash")
            
        Raises:
            Exception: If generation or TTS fails
        """
        try:
            # First, generate text content from prompt
            text_response = self.client.models.generate_content(
                model=generation_model,
                contents=prompt,
            )
            
            generated_text = text_response.text
            if not generated_text:
                raise Exception("No text generated from prompt")
            
            # Then convert generated text to speech
            self.speak(generated_text)
        except Exception as e:
            raise Exception(f"Prompt-to-speech error: {e}")
    
    def _speak_worker(self, text):
        """Worker function for async speaking."""
        self.speak(text)
    
    def _speak_from_prompt_worker(self, prompt, generation_model):
        """Worker function for async prompt-to-speech."""
        self.speak_from_prompt(prompt, generation_model)
    
    def speak_async(self, text):
        """
        Synthesize and play text asynchronously.
        
        Args:
            text: Text to speak
            
        Returns:
            Thread object
        """
        thread = threading.Thread(target=self._speak_worker, args=(text,))
        thread.start()
        return thread
    
    def speak_from_prompt_async(self, prompt, generation_model="gemini-2.0-flash"):
        """
        Generate content from prompt and speak asynchronously.
        
        Args:
            prompt: Prompt to generate content from
            generation_model: Model to use for text generation (default: "gemini-2.0-flash")
            
        Returns:
            Thread object
        """
        thread = threading.Thread(
            target=self._speak_from_prompt_worker,
            args=(prompt, generation_model)
        )
        thread.start()
        return thread
    
    def close(self):
        """Clean up PyAudio resources."""
        if self.pyaudio_instance:
            self.pyaudio_instance.terminate()
