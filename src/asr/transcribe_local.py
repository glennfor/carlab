import subprocess


def transcribe(audio_path="audio.wav"):
    result = subprocess.run(
        ["./whisper", "-m", "models/whisper-base.en.bin", "-f", audio_path, "--no-timestamps"],
        stdout=subprocess.PIPE,
        text=True
    )
    return result.stdout.strip()


import pyaudio
import numpy as np
import whisper



# ASR (Automatic Speech Recognition)
# whispercpp needs sample rate 16000 but SPH645 is 48000
class ASR:
    def __init__(self,
                 model_name="base",
                 sample_rate=16000,
                 chunk=1024,
                 device_index=None):

        self.sample_rate = sample_rate
        self.chunk = chunk

        print("Loading Whisper model…")
        self.model = whisper.load_model(model_name)

        # self.model = Whisper(model_path)

        self.audio = pyaudio.PyAudio()

        # Use I2S Mic (usually device index 0)
        if device_index is None:
            device_index = 0

        print(f"Using audio device {device_index}")

        self.stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk,
            input_device_index=device_index
        )

    def listen(self, seconds=3):
        print(f"Listening for {seconds} sec…")
        frames = []

        for _ in range(int(self.sample_rate / self.chunk * seconds)):
            data = self.stream.read(self.chunk, exception_on_overflow=False)
            frames.append(np.frombuffer(data, dtype=np.int16))

        # Convert to a single numpy array
        audio_data = np.hstack(frames).astype(np.float32) / 32768.0
        return audio_data

    def transcribe(self, audio_data):
        print("Transcribing…")
        result = self.model.transcribe(audio_data)
        return result["text"]

    def transcribe_whispercpp(self, audio):
        text = self.model.transcribe(audio)
        return text

    def listen_and_transcribe(self, seconds=3):
        audio = self.listen(seconds)
        text = self.transcribe(audio)
        return text

    def close(self):
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()
