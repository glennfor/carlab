import numpy as np
import pyaudio
import time
import torch
import queue
from whispercpp import Whisper
import threading
# import soundfile as sf
import webrtcvad


# -----------------------
#   Load  VAD
# -----------------------
vad = webrtcvad.Vad(2)  # aggressiveness 0-3

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
        p = self.audio_interface

        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                print(f"Index {i}: {info['name']} ({info['maxInputChannels']} channels)")

        # self.stream = self.audio_interface.open(
        #     format=pyaudio.paInt16,
        #     channels=1,
        #     rate=sample_rate,
        #     input=True,
        #     frames_per_buffer=chunk,
        #     input_device_index=device_index
        # )

        self.stream = self.audio_interface.open(
            format=pyaudio.paInt32,    # 32-bit PCM
            channels=1,                # mono
            rate=48000,                # 48 kHz
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
        self.whisper = Whisper.from_pretrained(whisper_model)

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
    # def _is_speech(self, audio_chunk):
    #     # audio_tensor = torch.from_numpy(audio_chunk).float()
    #     # prob = vad_model(audio_tensor, self.sample_rate).item()
    #     # return prob > 0.5
    #         # Ensure float32, mono
    #     audio_tensor = torch.tensor(audio_chunk, dtype=torch.float32)
        
    #     # Silero VAD expects shape [samples], no torchaudio needed
    #     speech_timestamps = get_speech_timestamps(audio_tensor, vad_model, sampling_rate=self.sample_rate)
        
    #     return len(speech_timestamps) > 0
    
    def _is_speech(self, audio_chunk):
        # Convert float32 [-1,1] to int16
        pcm16 = (audio_chunk * 32767).astype('int16').tobytes()
        return vad.is_speech(pcm16, sample_rate=self.sample_rate)

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