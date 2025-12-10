import numpy as np
import pyaudio
import time
import torch
import queue
import threading
from pywhispercpp import Whisper

# -----------------------
#   Load Silero VAD
# -----------------------
vad_model, vad_utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                                      model='silero_vad',
                                      force_reload=False)
(get_speech_timestamps,
 save_audio,
 read_audio,
 VADIterator,
 collect_chunks) = vad_utils


class Trancriber:
    def __init__(self,
                 wake_word="hey pi",
                 whisper_model="ggml-base.en.bin",
                 device_index=0,
                 sample_rate=16000,
                 chunk=1024):

        # Audio setup
        self.sample_rate = sample_rate
        self.chunk = chunk
        self.device_index = device_index
        self.audio_interface = pyaudio.PyAudio()

        self.stream = self.audio_interface.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=sample_rate,
            input=True,
            frames_per_buffer=chunk,
            input_device_index=device_index
        )

        # Buffers
        self.audio_queue = queue.Queue()
        self.speech_buffer = []
        self.listening_for_wakeword = True
        self.wake_word = wake_word.lower()

        # Whisper model (pywhispercpp)
        print("Loading pywhispercpp model…")
        self.whisper = Whisper(whisper_model)

        print("ASR system ready.")

    # -----------------------
    #  Read raw mic audio
    # -----------------------
    def _stream_audio(self):
        while True:
            data = self.stream.read(self.chunk, exception_on_overflow=False)
            audio = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
            self.audio_queue.put(audio)

    # -----------------------
    #  Check if audio contains speech (VAD)
    # -----------------------
    def _is_speech(self, audio_chunk):
        audio_tensor = torch.from_numpy(audio_chunk).float()
        prob = vad_model(audio_tensor, self.sample_rate).item()
        return prob > 0.5

    # -----------------------
    #  Whisper streaming decode (pywhispercpp)
    # -----------------------
    def _whisper_transcribe(self, audio_data):
        """
        pywhispercpp expects 16-bit PCM numpy arrays
        """
        # Convert float32 [-1, 1] to int16
        int16_audio = (np.array(audio_data) * 32767).astype(np.int16)
        text = self.whisper.transcribe(int16_audio)
        return text.strip()

    # -----------------------
    #  Listen for wake word
    # -----------------------
    def _detect_wake_word(self, text):
        return self.wake_word in text.lower()

    # -----------------------
    #  Main loop
    # -----------------------
    def run(self):
        threading.Thread(target=self._stream_audio, daemon=True).start()

        print("Listening for wake word…")

        audio_accum = []

        while True:
            chunk = self.audio_queue.get()

            # VAD — only collect speech
            if self._is_speech(chunk):
                audio_accum.extend(chunk)

                # Do small streaming inference every 0.5s of speech
                if len(audio_accum) > self.sample_rate // 2:
                    text = self._whisper_transcribe(np.array(audio_accum))

                    if text:
                        print("[STREAM]", text)

                        # Wake word stage
                        if self.listening_for_wakeword:
                            if self._detect_wake_word(text):
                                print("🚀 Wake word detected!")
                                self.listening_for_wakeword = False
                                audio_accum = []
                                print("Now listening for command…")
                        else:
                            # Command stage
                            if self._is_speech(chunk):
                                continue  # keep collecting
                            else:
                                final_text = self._whisper_transcribe(np.array(audio_accum))
                                print("🎤 Command:", final_text)
                                self.listening_for_wakeword = True
                                print("Listening for wake word…")
                                audio_accum = []

            else:
                # No speech → reset local buffer slowly
                if len(audio_accum) > 0:
                    audio_accum = audio_accum[-self.sample_rate*2:]  # keep last 2 sec

    def close(self):
        self.stream.stop_stream()
        self.stream.close()
        self.audio_interface.terminate()
