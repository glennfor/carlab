import asyncio
import os
import queue
import threading
import time

import numpy as np
import pyaudio
from elevenlabs import ElevenLabs
from scipy.signal import resample


def resample_audio(chunk: bytes, orig_sr: int, target_sr: int) -> bytes:
    """Resample PCM16 audio chunk from orig_sr to target_sr."""
    audio = np.frombuffer(chunk, dtype=np.int16)
    num_samples = int(len(audio) * target_sr / orig_sr)
    resampled = resample(audio, num_samples)
    resampled = np.clip(resampled, -32768, 32767).astype(np.int16)
    return resampled.tobytes()


class Vocalizer:
    def __init__(self, 
                 api_key=None,
                 voice_id="JBFqnCBsd6RMkjVDRZzb",
                 model_id="eleven_multilingual_v2",
                 device_index=None,
                 sample_rate=44100,
                 output_format="pcm_16000"):
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        if not self.api_key:
            raise ValueError("Missing ELEVENLABS_API_KEY. Provide it as parameter or set as environment variable.")
        
        self.voice_id = voice_id
        self.model_id = model_id
        self.device_index = device_index
        self.sample_rate = sample_rate
        self.output_format = output_format
        
        self.client = ElevenLabs(api_key=self.api_key)
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.audio_queue = queue.Queue()
        self.running = False

        p = self.audio
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            print(i, info["name"], info["maxOutputChannels"])
     

    def _setup_audio_stream(self):
        """Setup PyAudio output stream."""
        if self.stream:
            return
        
        stream_kwargs = {
            "format": pyaudio.paInt16,
            "channels": 1,
            "rate": self.sample_rate,
            "output": True,
        }
        
        if self.device_index is not None:
            stream_kwargs["output_device_index"] = self.device_index
        
        self.stream = self.audio.open(**stream_kwargs)

    def _close_audio_stream(self):
        """Close PyAudio output stream."""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

    def speak(self, text):
        """Convert text to speech and play it directly."""
        if not text or not text.strip():
            return
        print('Speaking.........>>> '+ text)
        self._setup_audio_stream()
        
        try:
            # Stream audio from ElevenLabs
            audio_stream = self.client.text_to_speech.stream(
                text=text,
                voice_id=self.voice_id,
                model_id=self.model_id,
                output_format=self.output_format
            )
            print('Speaking Chunks.....')
            # Play audio chunks as they arrive
            for chunk in audio_stream:
                if isinstance(chunk, bytes):
                    chunk = resample_audio(chunk, 16000, self.sample_rate)
                    self.stream.write(chunk)
            
            # Flush any remaining buffer
            self.stream.write(b"")
            print('Speaking Chunks..33333 end...')

        except Exception as e:
            print(f"Error during speech synthesis: {e}")
            raise
        finally:
            # Keep stream open for potential reuse
            pass

    def speak_async(self, text):
        """Convert text to speech asynchronously (non-blocking)."""        
        def _speak_thread():
            try:
                self.speak(text)
            except Exception as e:
                print(f"Error in async speech: {e}")
        
        thread = threading.Thread(target=_speak_thread)
        thread.start()
        return thread
    
    # def run(self):
    #     """Run the vocalizer."""
    #     """Thread: Process audio queue."""
    #     while self.running:
    #         try:
    #             text = self.queue.get(timeout=1)
    #             if text is None:
    #                 continue
    #             self.speak(text)
    #         except queue.Empty:
    #             time.sleep(0.1)
    #             continue
    #         except Exception as e:
    #             print(f"Error in vocalizer: {e}")
    #             break
    
    def _run_loop(self):
        """Private method: processes the queue in a loop."""
        while self.running:
            try:
                text = self.audio_queue.get(timeout=1)
                if text is None:
                    continue
                print('Have to say>>> '+ text)
                self.speak(text)
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error in vocalizer loop: {e}")

    def run(self):
        """Start the vocalizer queue loop in a background thread."""
        if self.running:
            return  # Already running
        self.running = True
        self._thread = threading.Thread(target=self._run_loop)
        self._thread.start()
    
    def queue(self, text):
        """Add text to the vocalizer queue."""
        self.audio_queue.put(text)
    
    def stop(self):
        """Stop the vocalizer."""
        self.running = False
        

    def close(self):
        """Close audio stream and cleanup."""
        self.running = False
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
    
    vocalizer = Vocalizer(api_key=ELEVENLABS_API_KEY, sample_rate=48000, device_index=4)
    print('[Vocalizer] Initialised')
    try:
        print("Speaking: Hello, this is a test of the vocalizer.")
        vocalizer.speak("Hello, this is a test of the vocalizer.")
        
        print("Speaking asynchronously: This is an async test.")
        thread = vocalizer.speak_async("This is an async test.")
        thread.join()
        pass
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    finally:
        vocalizer.close()
