import asyncio
import queue
import threading
import os
import base64

import pyaudio
from elevenlabs import AudioFormat, CommitStrategy, ElevenLabs, RealtimeEvents, RealtimeAudioOptions

import numpy as np
# import scipy.signal

#======= Safely stop ALSA spam==
# import ctypes
# import ctypes.util

# def hide_alsa_errors():
#     ERROR_HANDLER_FUNC = ctypes.CFUNCTYPE(
#         None, ctypes.c_char_p, ctypes.c_int,
#         ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p
#     )
#     def no_errors(*args):
#         pass
#     c_error_handler = ERROR_HANDLER_FUNC(no_errors)
#     asound = ctypes.cdll.LoadLibrary(ctypes.util.find_library('asound'))
#     asound.snd_lib_error_set_handler(c_error_handler)

# hide_alsa_errors()
#==============

def downsample_48k_to_16k(data_bytes):
    # Convert bytes to numpy array
    audio = np.frombuffer(data_bytes, dtype=np.int16)
    # Resample
    # Less accurate, introduces aliasing
    resampled = audio[::3] #scipy.signal.resample_poly(audio, 1, 3)  # 48k -> 16k
    return resampled.tobytes()

class Transcriber:
    def __init__(self, 
                api_key, 
                model_id="scribe_v2_realtime", 
                device_index=0,
                sample_rate=48000, 
                chunk=1024):
        self.api_key = api_key
        self.model_id = model_id
        self.sample_rate = sample_rate
        self.chunk = chunk
        self.device_index = device_index
        self.audio = pyaudio.PyAudio()
        p = self.audio

        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                print(f"Index {i}: {info['name']} ({info['maxInputChannels']} channels)")

        self.stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=sample_rate,
            input=True,
            frames_per_buffer=chunk,
            input_device_index=device_index
        )
        self.audio_queue = queue.Queue()
        # self.audio_queue = asyncio.Queue()

        self.command_callback = None
        self.client = ElevenLabs(api_key=api_key)
        self.connection = None

    def set_command_callback(self, callback):
        """Set a callback function to handle transcribed commands, e.g., send to LLM."""
        self.command_callback = callback

    def _stream_audio(self):
        """Thread: Read mic audio and put in queue."""
        while True:
            try:
                data = self.stream.read(self.chunk, exception_on_overflow=False)
                self.audio_queue.put(data)
            except Exception as e:
                print(f"Audio stream error: {e}")
                break

    def _on_partial_transcript(self, event):
        """Handle partial transcript events for wake word detection."""
        if isinstance(event, dict):
            text = event.get("text", event.get("transcript", "")).strip().lower()
        else:
            text = str(event).strip().lower()
        
        # if text and self.listening_for_wakeword:
            # if self.wake_word in text:
            #     print("🚀 Wake word detected!")
            #     self.listening_for_wakeword = False
            #     print("Now listening for command...")

    def _on_committed_transcript(self, event):
        """Handle committed transcript events for command processing."""
        if isinstance(event, dict):
            text = event.get("text", event.get("transcript", "")).strip()
        else:
            text = str(event).strip()
        
        if text:
            print(f"🎤 Command: {text}")
            if self.command_callback:
                self.command_callback(text)
            else:
                print(f"Transcribed command (send to LLM): {text}")
            # self.listening_for_wakeword = True
            # print("Listening for wake word...")

    def _on_error(self, error):
        """Handle error events."""
        print(f"Error: {error}")

    def _on_close(self):
        """Handle connection close events."""
        print("Connection closed")

    async def run_async(self):
        """Async main loop for SDK connection and audio sending."""
        try:
            self.connection = await self.client.speech_to_text.realtime.connect(RealtimeAudioOptions(
                model_id=self.model_id,
                language_code="en",
                sample_rate=self.sample_rate,
                audio_format=AudioFormat.PCM_16000,
                commit_strategy=CommitStrategy.VAD,
                vad_silence_threshold_secs=1.0,
                vad_threshold=0.5,
                min_speech_duration_ms=250,
                include_timestamps=False,
            ))

            self.connection.on(RealtimeEvents.PARTIAL_TRANSCRIPT, self._on_partial_transcript)
            self.connection.on(RealtimeEvents.COMMITTED_TRANSCRIPT, self._on_committed_transcript)
            self.connection.on(RealtimeEvents.ERROR, self._on_error)
            self.connection.on(RealtimeEvents.CLOSE, self._on_close)

            print("Connected to ElevenLabs STT...")

            while True:
                try:
                    data = self.audio_queue.get(timeout=1)
                    if not data:
                        continue
                    resampled_data = downsample_48k_to_16k(data)

                    # Send audio data to the connection
                    # The SDK connection object should have a send method for audio bytes
                    audio_base_64 = base64.b64encode(resampled_data).decode('utf-8')
                    # audio_base_64 = base64.b64encode(data).decode('utf-8')
                    # await self.connection.send(data)
                    
                    await self.connection.send({
                        "audio_base_64": audio_base_64,
                        "sample_rate": self.sample_rate,
                    })
                    # When ready to finalize the segment
                    # await self.connection.commit()
                except queue.Empty:
                    continue
                except Exception as e:
                    print(f"Send error: {e}")
                    break

        except Exception as e:
            print(f"Connection error: {e}")
        finally:
            if self.connection:
                await self.connection.close()

    def run(self):
        """Start threads and async loop."""
        threading.Thread(target=self._stream_audio, daemon=True).start()
        print("Connecting to ElevenLabs STT...")
        asyncio.run(self.run_async())

    def close(self):
        """Close audio stream and cleanup."""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if self.audio:
            self.audio.terminate()

# Usage example
def example_llm_callback(command):
    # This would be your external LLM pipeline
    print(f"Sending to LLM: {command}")
    # e.g., requests.post('http://your-llm-endpoint', json={'input': command})

if __name__ == '__main__':
    print('Starting listener')
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

    if not ELEVENLABS_API_KEY:
        raise ValueError("Missing ELEVENLABS_API_KEY")
    asr = Transcriber(api_key=ELEVENLABS_API_KEY, device_index=1)
    print('Setup')
    asr.set_command_callback(example_llm_callback)
    print('[Now] - Listening')
    try:
        asr.run()
    except KeyboardInterrupt:
        asr.close()