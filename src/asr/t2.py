import asyncio
import json
import websockets
import pyaudio
import base64  # For encoding audio
import threading
import queue

class ElevenLabsASR:
    def __init__(self, 
                api_key, 
                model_id="eleven_turbo_v2_5", 
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
        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=sample_rate,
            input=True,
            frames_per_buffer=chunk
        )
        self.audio_queue = queue.Queue()
        self.command_callback = None  # Set this to a function that handles the transcribed command
        self.ws_url = (
            f"wss://api.elevenlabs.io/v1/speech-to-text/realtime?"
            f"model_id={self.model_id}&"
            f"xi-api-key={self.api_key}&"
            f"commit_strategy=vad&"
            f"vad_silence_threshold_secs=1.0&"  # Adjust as needed
            f"vad_threshold=0.5&"
            f"min_speech_duration_ms=250&"
            f"language_code=en"  # Set to your language
        )
        print("ElevenLabs ASR ready.")

    def set_command_callback(self, callback):
        """Set a callback function to handle transcribed commands, e.g., send to LLM."""
        self.command_callback = callback

    def _stream_audio(self):
        """Thread: Read mic audio and put in queue."""
        while True:
            data = self.stream.read(self.chunk, exception_on_overflow=False)
            self.audio_queue.put(data)

    async def _receive_transcripts(self, ws):
        """Handle incoming messages from WebSocket."""
        while True:
            try:
                message = await ws.recv()
                evt = json.loads(message)
                evt_type = evt.get("type")
                
                if evt_type == "sessionStarted":
                    print("Session started:", evt)
                
                elif evt_type == "partialTranscript":
                    text = evt.get("transcript", "").strip().lower()
                    if text and self.listening_for_wakeword:
                        if self.wake_word in text:
                            print("🚀 Wake word detected!")
                            self.listening_for_wakeword = False
                            print("Now listening for command...")
                
                elif evt_type == "committedTranscript":
                    text = evt.get("transcript", "").strip()
                    if text and not self.listening_for_wakeword:
                        print(f"🎤 Command: {text}")
                        if self.command_callback:
                            self.command_callback(text)  # Send to LLM pipeline
                        else:
                            print(f"Transcribed command (send to LLM): {text}")
                        self.listening_for_wakeword = True
                        print("Listening for wake word...")
                
                elif "Error" in evt_type:
                    print(f"Error: {evt}")
            
            except Exception as e:
                print(f"Receive error: {e}")
                break

    async def run_async(self):
        """Async main loop for WebSocket connection and audio sending."""
        async with websockets.connect(self.ws_url) as ws:
            # Start receive task
            receive_task = asyncio.create_task(self._receive_transcripts(ws))
            # await ws.send(json.dumps({
            #     "type": "session.start",
            #     "sample_rate": self.sample_rate,
            #     "channels": 1,
            #     "format": "pcm_16"
            # }))

            while True:
                try:
                    data = self.audio_queue.get(timeout=1)
                    if not data:
                        continue
                    # Encode audio to base64 (docs imply binary, but JSON needs encoding; base64 is safe)
                    # Convert raw PCM → base64 string
                    b64_audio = base64.b64encode(data).decode("utf-8")

                    # Send inside JSON envelope (required by ElevenLabs)
                    await ws.send(json.dumps({
                        "type": "input_audio_buffer.append",
                        "audio": b64_audio
                    }))
                    # await ws.send(data)
                except queue.Empty:
                    continue
                except Exception as e:
                    print(f"Send error: {e}")
                    break
            
            await receive_task

    def run(self):
        """Start threads and async loop."""
        threading.Thread(target=self._stream_audio, daemon=True).start()
        print("Connecting to ElevenLabs STT...")
        asyncio.run(self.run_async())

    def close(self):
        self.stream.stop_stream()
        self.stream.close()
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