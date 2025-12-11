import asyncio
import json
import os
import queue
import threading

import numpy as np
import pyaudio
from deepgram import DeepgramClient
from deepgram.core.events import EventType
from deepgram.extensions.types.sockets import ListenV1SocketClientResponse


def downsample_48k_to_16k(data_bytes):
    """Downsample audio from 48kHz to 16kHz."""
    audio = np.frombuffer(data_bytes, dtype=np.int16)
    resampled = audio[::3]
    return resampled.tobytes()


class DeepgramTranscriber:
    def __init__(
        self,
        api_key=None,
        model="nova-3",
        language="en-US",
        device_index=0,
        sample_rate=48000,
        chunk=1024,
        utterance_end_ms=1000,
        smart_format=True,
        interim_results=True,
    ):
        self.api_key = api_key or os.getenv("DEEPGRAM_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key required. Set DEEPGRAM_API_KEY environment variable "
                "or pass api_key parameter."
            )

        print(f"key={self.api_key[:6]}...")
        self.model = model
        self.language = language
        self.sample_rate = sample_rate
        self.chunk = chunk
        self.device_index = device_index
        self.utterance_end_ms = utterance_end_ms
        self.smart_format = smart_format
        self.interim_results = interim_results

        self.audio = pyaudio.PyAudio()
        p = self.audio

        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if info["maxInputChannels"] > 0:
                print(
                    f"Index {i}: {info['name']} ({info['maxInputChannels']} channels)"
                )

        self.stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=sample_rate,
            input=True,
            frames_per_buffer=chunk,
            input_device_index=device_index,
        )
        self.audio_queue = queue.Queue()

        self.command_callback = None
        self.client = None
        self.connection = None
        self.last_transcript = ""
        self.utterance_ended = False

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

    def _on_message(self, message: ListenV1SocketClientResponse):
        """Handle messages from Deepgram connection."""
        msg_type = getattr(message, "type", "Unknown")

        if msg_type == "Results":
            if hasattr(message, "channel") and hasattr(message.channel, "alternatives"):
                if len(message.channel.alternatives) > 0:
                    transcript = message.channel.alternatives[0].transcript
                    is_final = getattr(message, "is_final", False)
                    speech_final = getattr(message, "speech_final", False)

                    if transcript:
                        self.last_transcript = transcript

                        if is_final or speech_final:
                            self._on_final_transcript(transcript)
                        else:
                            self._on_partial_transcript(transcript)

        elif msg_type == "UtteranceEnd":
            self._on_utterance_end(message)

    def _on_partial_transcript(self, text):
        """Handle partial/interim transcript events."""
        text = text.strip().lower()
        if text:
            print(f"🎤 Partial: {text}")

    def _on_final_transcript(self, text):
        """Handle final transcript events for command processing."""
        text = text.strip()
        print(f"Catch insts? = {text}")

        if text:
            print(f"🎤 Final: {text}")
            is_command = "open" in text.lower()
            if not is_command:
                return

            if self.command_callback:
                self.command_callback(text)
            else:
                print(f"Transcribed command (send to LLM): {text}")

    def _on_utterance_end(self, message):
        """Handle UtteranceEnd event when speaker stops talking."""
        print("🔇 Utterance ended")
        self.utterance_ended = True

        if self.last_transcript:
            text = self.last_transcript.strip()
            if text:
                is_command = "open" in text.lower()
                if is_command and self.command_callback:
                    self.command_callback(text)

    def _on_open(self, _):
        """Handle connection open event."""
        print("Connected to Deepgram STT...")

    def _on_close(self, _):
        """Handle connection close event."""
        print("Connection closed")

    def _on_error(self, error):
        """Handle error events."""
        print(f"Error: {error}")

    async def run_async(self):
        """Async main loop for Deepgram connection and audio sending."""
        try:
            self.client = DeepgramClient(self.api_key)

            options = {
                "model": self.model,
                "language": self.language,
                "smart_format": self.smart_format,
                "interim_results": self.interim_results,
                "utterance_end_ms": self.utterance_end_ms,
            }

            with self.client.listen.v1.connect(**options) as connection:
                self.connection = connection

                connection.on(EventType.OPEN, self._on_open)
                connection.on(EventType.MESSAGE, self._on_message)
                connection.on(EventType.CLOSE, self._on_close)
                connection.on(EventType.ERROR, self._on_error)

                lock_exit = threading.Lock()
                exit_flag = False

                def listening_thread():
                    try:
                        connection.start_listening()
                    except Exception as e:
                        print(f"Error in listening thread: {e}")

                listen_thread = threading.Thread(target=listening_thread, daemon=True)
                listen_thread.start()

                while True:
                    try:
                        data = self.audio_queue.get(timeout=1)
                        if not data:
                            continue

                        resampled_data = downsample_48k_to_16k(data)
                        connection.send_media(resampled_data)

                        lock_exit.acquire()
                        if exit_flag:
                            break
                        lock_exit.release()

                    except queue.Empty:
                        continue
                    except Exception as e:
                        print(f"Send error: {e}")
                        break

                lock_exit.acquire()
                exit_flag = True
                lock_exit.release()

                listen_thread.join(timeout=5.0)

        except Exception as e:
            print(f"Connection error: {e}")
        finally:
            if self.connection:
                try:
                    self.connection.finish()
                except:
                    pass

    def run(self):
        """Start threads and async loop."""
        threading.Thread(target=self._stream_audio, daemon=True).start()
        print("Connecting to Deepgram STT...")
        asyncio.run(self.run_async())

    def close(self):
        """Close audio stream and cleanup."""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if self.audio:
            self.audio.terminate()

    def stop(self):
        """Close audio stream and cleanup."""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if self.audio:
            self.audio.terminate()


def example_llm_callback(command):
    """Example callback function to handle transcribed commands."""
    print(f"Sending to LLM: {command}")


if __name__ == "__main__":
    print("Starting Deepgram listener")
    DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

    if not DEEPGRAM_API_KEY:
        raise ValueError("Missing DEEPGRAM_API_KEY")

    transcriber = DeepgramTranscriber(api_key=DEEPGRAM_API_KEY, device_index=1)
    print("Setup complete")
    transcriber.set_command_callback(example_llm_callback)
    print("[Now] - Listening")
    try:
        transcriber.run()
    except KeyboardInterrupt:
        transcriber.close()
