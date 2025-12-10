import asyncio
import os
from io import BytesIO

import pyaudio
from elevenlabs import ElevenLabs
from pydub import AudioSegment


class Vocalizer:
    def __init__(self, 
                 api_key=None,
                 voice_id="JBFqnCBsd6RMkjVDRZzb",
                 model_id="eleven_multilingual_v2",
                 device_index=None,
                 sample_rate=44100,
                 output_format=None):
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        if not self.api_key:
            raise ValueError("Missing ELEVENLABS_API_KEY. Provide it as parameter or set as environment variable.")
        
        self.voice_id = voice_id
        self.model_id = model_id
        self.device_index = device_index
        self.sample_rate = sample_rate
        # Use None or "mp3_44100_128" for free tier (PCM requires Pro tier)
        self.output_format = output_format
        
        self.client = ElevenLabs(api_key=self.api_key)
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.current_stream_rate = None
        self.current_stream_channels = None
        
        # List available output devices
        p = self.audio
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if info['maxOutputChannels'] > 0:
                print(f"Output Device {i}: {info['name']} ({info['maxOutputChannels']} channels)")

    def _setup_audio_stream(self, rate=None, channels=1):
        """Setup PyAudio output stream."""
        rate = rate or self.sample_rate
        
        # Reuse stream if rate and channels match
        if self.stream and self.current_stream_rate == rate and self.current_stream_channels == channels:
            return
        
        self._close_audio_stream()
        
        stream_kwargs = {
            "format": pyaudio.paInt16,
            "channels": channels,
            "rate": rate,
            "output": True,
        }
        
        if self.device_index is not None:
            stream_kwargs["output_device_index"] = self.device_index
        
        self.stream = self.audio.open(**stream_kwargs)
        self.current_stream_rate = rate
        self.current_stream_channels = channels

    def _close_audio_stream(self):
        """Close PyAudio output stream."""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
            self.current_stream_rate = None
            self.current_stream_channels = None

    def speak(self, text):
        """Convert text to speech and play it directly."""
        if not text or not text.strip():
            return
        
        try:
            # Stream audio from ElevenLabs (defaults to MP3 for free tier)
            stream_kwargs = {
                "text": text,
                "voice_id": self.voice_id,
                "model_id": self.model_id,
            }
            
            # Only add output_format if specified (None means default MP3)
            if self.output_format:
                stream_kwargs["output_format"] = self.output_format
            
            audio_stream = self.client.text_to_speech.stream(**stream_kwargs)
            
            # Collect all MP3 chunks
            mp3_data = BytesIO()
            for chunk in audio_stream:
                if isinstance(chunk, bytes):
                    mp3_data.write(chunk)
            
            # Reset to beginning for reading
            mp3_data.seek(0)
            
            # Decode MP3 to PCM
            audio_segment = AudioSegment.from_file(mp3_data, format="mp3")
            
            # Convert to raw PCM data
            raw_audio = audio_segment.raw_data
            
            # Setup audio stream with the actual sample rate and channels from decoded audio
            self._setup_audio_stream(rate=audio_segment.frame_rate, channels=audio_segment.channels)
            
            # Play the decoded PCM audio
            chunk_size = 1024
            for i in range(0, len(raw_audio), chunk_size):
                chunk = raw_audio[i:i + chunk_size]
                self.stream.write(chunk)
            
            # Flush any remaining buffer
            self.stream.write(b"")
            
        except Exception as e:
            print(f"Error during speech synthesis: {e}")
            raise

    def speak_async(self, text):
        """Convert text to speech asynchronously (non-blocking)."""
        import threading
        
        def _speak_thread():
            try:
                self.speak(text)
            except Exception as e:
                print(f"Error in async speech: {e}")
        
        thread = threading.Thread(target=_speak_thread, daemon=True)
        thread.start()
        return thread

    def close(self):
        """Close audio stream and cleanup."""
        self._close_audio_stream()
        if self.audio:
            self.audio.terminate()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Usage example
if __name__ == '__main__':
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    
    if not ELEVENLABS_API_KEY:
        raise ValueError("Missing ELEVENLABS_API_KEY")
    
    vocalizer = Vocalizer(api_key=ELEVENLABS_API_KEY, device_index=None)
    
    try:
        print("Speaking: Hello, this is a test of the ElevenLabs vocalizer.")
        vocalizer.speak("Hello, this is a test of the ElevenLabs vocalizer.")
        
        print("Speaking asynchronously: This is an async test.")
        thread = vocalizer.speak_async("This is an async test.")
        thread.join()
        
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    finally:
        vocalizer.close()
