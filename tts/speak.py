import subprocess
import threading


def speak(text):
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