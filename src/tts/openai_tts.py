import os
import threading

import pyaudio
from openai import OpenAI


class OpenAITTS:
    def __init__(self, api_key=None, model="gpt-4o-mini-tts", voice="alloy"):
        """
        Initialize OpenAI TTS client.
        
        Args:
            api_key: OpenAI API key. If None, uses OPENAI_API_KEY env var.
            model: TTS model name (default: "gpt-4o-mini-tts")
            voice: Voice name from available options (default: "alloy")
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key required. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = model
        self.voice = voice
        
        # PyAudio setup for direct streaming
        self.pyaudio_instance = pyaudio.PyAudio()
        self.sample_rate = 24000
        self.channels = 1
        self.format = pyaudio.paInt16
    
    def _synthesize_speech(self, text):
        """
        Synthesize speech from text using OpenAI TTS API.
        
        Args:
            text: Text to convert to speech
            
        Returns:
            bytes: Raw PCM audio data
        """
        try:
            response = self.client.audio.speech.create(
                model=self.model,
                voice=self.voice,
                input=text,
                response_format="pcm",  # Use PCM for direct playback
                speed=1.0,
            )
            
            # Read audio data from response stream
            audio_data = b""
            for chunk in response.iter_bytes():
                audio_data += chunk
            
            return audio_data
        except Exception as e:
            raise Exception(f"OpenAI TTS API error: {e}")
    
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
    
    def speak_from_prompt(self, prompt, generation_model="gpt-4o-mini"):
        """
        Generate content from a prompt using OpenAI, then convert to speech.
        
        Args:
            prompt: Prompt to generate content from
            generation_model: Model to use for text generation (default: "gpt-4o-mini")
            
        Raises:
            Exception: If generation or TTS fails
        """
        try:
            # First, generate text content from prompt
            response = self.client.chat.completions.create(
                model=generation_model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
            )
            
            generated_text = response.choices[0].message.content
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
    
    def speak_from_prompt_async(self, prompt, generation_model="gpt-4o-mini"):
        """
        Generate content from prompt and speak asynchronously.
        
        Args:
            prompt: Prompt to generate content from
            generation_model: Model to use for text generation (default: "gpt-4o-mini")
            
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


# Convenience functions for backward compatibility
_tts_instance = None


def get_tts_instance(api_key=None, model="gpt-4o-mini-tts", voice="alloy"):
    """Get or create a singleton TTS instance."""
    global _tts_instance
    if _tts_instance is None:
        _tts_instance = OpenAITTS(api_key, model, voice)
    return _tts_instance


def speak(text, api_key=None, model="gpt-4o-mini-tts", voice="alloy"):
    """
    Convenience function to speak text using OpenAI TTS.
    
    Args:
        text: Text to speak
        api_key: OpenAI API key (optional, uses OPENAI_API_KEY env var if not provided)
        model: TTS model name (default: "gpt-4o-mini-tts")
        voice: Voice name (default: "alloy")
    """
    tts = get_tts_instance(api_key, model, voice)
    tts.speak(text)


def speak_async(text, api_key=None, model="gpt-4o-mini-tts", voice="alloy"):
    """
    Convenience function to speak text asynchronously using OpenAI TTS.
    
    Args:
        text: Text to speak
        api_key: OpenAI API key (optional, uses OPENAI_API_KEY env var if not provided)
        model: TTS model name (default: "gpt-4o-mini-tts")
        voice: Voice name (default: "alloy")
        
    Returns:
        Thread object
    """
    tts = get_tts_instance(api_key, model, voice)
    return tts.speak_async(text)


def speak_from_prompt(
    prompt,
    api_key=None,
    model="gpt-4o-mini-tts",
    voice="alloy",
    generation_model="gpt-4o-mini"
):
    """
    Generate content from prompt and speak it using OpenAI TTS.
    
    Args:
        prompt: Prompt to generate content from
        api_key: OpenAI API key (optional, uses OPENAI_API_KEY env var if not provided)
        model: TTS model name (default: "gpt-4o-mini-tts")
        voice: Voice name (default: "alloy")
        generation_model: Model to use for text generation (default: "gpt-4o-mini")
    """
    tts = get_tts_instance(api_key, model, voice)
    tts.speak_from_prompt(prompt, generation_model)


def speak_from_prompt_async(
    prompt,
    api_key=None,
    model="gpt-4o-mini-tts",
    voice="alloy",
    generation_model="gpt-4o-mini"
):
    """
    Generate content from prompt and speak it asynchronously using OpenAI TTS.
    
    Args:
        prompt: Prompt to generate content from
        api_key: OpenAI API key (optional, uses OPENAI_API_KEY env var if not provided)
        model: TTS model name (default: "gpt-4o-mini-tts")
        voice: Voice name (default: "alloy")
        generation_model: Model to use for text generation (default: "gpt-4o-mini")
        
    Returns:
        Thread object
    """
    tts = get_tts_instance(api_key, model, voice)
    return tts.speak_from_prompt_async(prompt, generation_model)

