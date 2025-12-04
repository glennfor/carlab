import numpy as np
import pyaudio
import time
import torch
import queue
from whispercpp import Whisper

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


class ASR:
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

        # Whisper model
        print("Loading Whisper.cpp model…")
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
    #  Whisper streaming decode
    # -----------------------
    def _whisper_transcribe(self, audio_data):
        return self.whisper.transcribe(audio_data).strip()

    # -----------------------
    #  Listen for wake word
    # -----------------------
    def _detect_wake_word(self, text):
        return self.wake_word in text.lower()

    # -----------------------
    #  Main loop
    # -----------------------
    def run(self):
        import threading
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


## Usage
from asr_pipeline import ASR

asr = ASR(
    wake_word="hey pi",
    whisper_model="ggml-base.en.bin",
    device_index=0  # SPH0645 I2S mic
)

asr.run()


##
# 🗣️ How It Works
# 1. Continuous audio streaming

# A background thread reads from the I²S mic.

# 2. VAD filters silence

# Only voice regions are kept.

# 3. Whisper does small streaming transcriptions

# Every ~0.5 seconds of speech, partial Whisper results appear.

# 4. Wake word detection

# When Whisper outputs something containing "hey pi" → activation happens.

# 5. Command mode

# After wake word, the next speech chunk is recorded fully and sent to Whisper for a final, accurate transcription.

# 6. System resets back to wake-word mode