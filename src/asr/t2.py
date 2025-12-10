import asyncio
import queue
import threading

import pyaudio
from elevenlabs import ElevenLabs, RealtimeEvents


class ElevenLabsASR:
    def __init__(self, 
                api_key, 
                model_id="scribe_v2_realtime", 
                wake_word="hey pi", 
                device_index=0,
                sample_rate=16000, 
                chunk=1024):
        self.api_key = api_key
        self.model_id = model_id
        self.wake_word = wake_word.lower()
        self.listening_for_wakeword = True
        self.sample_rate = sample_rate
        self.chunk = chunk
        self.device_index = device_index
        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=sample_rate,
            input=True,
            frames_per_buffer=chunk,
            input_device_index=device_index
        )
        self.audio_queue = queue.Queue()
        self.command_callback = None
        self.client = ElevenLabs(api_key=api_key)
        self.connection = None
        print("ElevenLabs ASR ready.")

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
        
        if text and self.listening_for_wakeword:
            if self.wake_word in text:
                print("🚀 Wake word detected!")
                self.listening_for_wakeword = False
                print("Now listening for command...")

    def _on_committed_transcript(self, event):
        """Handle committed transcript events for command processing."""
        if isinstance(event, dict):
            text = event.get("text", event.get("transcript", "")).strip()
        else:
            text = str(event).strip()
        
        if text and not self.listening_for_wakeword:
            print(f"🎤 Command: {text}")
            if self.command_callback:
                self.command_callback(text)
            else:
                print(f"Transcribed command (send to LLM): {text}")
            self.listening_for_wakeword = True
            print("Listening for wake word...")

    def _on_error(self, error):
        """Handle error events."""
        print(f"Error: {error}")

    def _on_close(self):
        """Handle connection close events."""
        print("Connection closed")

    async def run_async(self):
        """Async main loop for SDK connection and audio sending."""
        try:
            self.connection = await self.client.speech_to_text.realtime.connect(
                model_id=self.model_id,
                language_code="en",
                sample_rate=self.sample_rate,
                audio_format="pcm_16000",
                vad_silence_threshold_secs=1.0,
                vad_threshold=0.5,
                min_speech_duration_ms=250,
                commit_strategy="vad"
            )

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
                    # Send audio data to the connection
                    # The SDK connection object should have a send method for audio bytes
                    await self.connection.send(data)
                except queue.Empty:
                    continue
                except AttributeError:
                    # If send doesn't work, try alternative method names
                    if hasattr(self.connection, 'send_audio'):
                        await self.connection.send_audio(data)
                    elif hasattr(self.connection, 'append_audio'):
                        await self.connection.append_audio(data)
                    else:
                        print("Error: No audio sending method found on connection")
                        break
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
    asr = ElevenLabsASR(api_key="xxx", device_index=1)
    print('Setup')
    asr.set_command_callback(example_llm_callback)
    print('[Now] - Listening')
    try:
        asr.run()
    except KeyboardInterrupt:
        asr.close()