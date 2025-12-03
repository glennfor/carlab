import subprocess
import threading
import random
from piper import PiperVoice,SynthesisConfig
import wave
import os

# voice = PiperVoice.load("./models/en_US-lessac-medium.onnx")


# Load the model (use a medium or low model for max speed)
# model_path = "./tts/models/en_US-lessac-medium.onnx"   # or any .onnx you downloaded
model_path = "./tts/models/en_US-amy-medium.onnx"   # or any .onnx you downloaded
syn_config = SynthesisConfig(
    volume=2.0,  # half as loud
    length_scale=1.0,  # twice as slow
    noise_scale=1.0,  # more audio variation
    noise_w_scale=1.0,  # more speaking variation
    normalize_audio=False, # use raw audio from voice
)
voice = PiperVoice.load(model_path)

# pyaudio setup
# p = pyaudio.PyAudio()
# stream = p.open(format=pyaudio.paInt16,
#                 channels=1,
#                 rate=voice.config.sample_rate,   # usually 22050 or 24000
#                 output=True,
#                 frames_per_buffer=1024)

def speak(text):
    filename = '{}.wav'.format(random.random())
    with wave.open(filename, "wb") as wav_file:
        voice.synthesize_wav(text, wav_file, syn_config=syn_config)
    try:
        subprocess.run(["aplay", "-q", filename], check=True)
        print(f"Spoke: {text}")
    finally:
        os.unlink(filename)  # delete temp file



    # # Small trick: flush any remaining buffer (optional but helps)
    # stream.write(b"")


    # audio_gen = voice.synthesize(text)  # may be bytes or generator
    # try:
    #     for chunk in audio_gen:
    #         stream.write(chunk)
    # except TypeError:
    #     stream.write(audio_gen)
    # stream.write(b"")

    # audio_gen = voice.synthesize(text)

    # for chunk in audio_gen:
    #     # Convert numpy array to bytes
    #     if isinstance(chunk, np.ndarray):
    #         stream.write(chunk.tobytes())
    #     else:
    #         # If it’s already bytes
    #         stream.write(chunk)

def speak22(text):
    subprocess.run(
        ["piper", "--model", "en_US-amy-medium.onnx", "--output", "speech.wav"],
        input=text.encode("utf-8")
    )
    subprocess.run(["aplay", "speech.wav"])


def _speak_worker(text):
    subprocess.run(
        ["piper", "--model", "models/piper-voice.onnx", "--output", "speech.wav"],
        input=text.encode("utf-8")
    )
    subprocess.run(["aplay", "speech.wav"])

def speak_async(text):
    thread = threading.Thread(target=_speak_worker, args=(text,))
    thread.start()
    return thread