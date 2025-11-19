import sounddevice as sd
from scipy.io.wavfile import write

from actions.engine import execute
from asr.transcribe import transcribe
from llm.brain import ask_brain
from tts.speak import speak
from wakeword.hotword import listen_for_wakeword


def record_command():
    print("Listening...")
    fs = 16000
    duration = 4
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()
    write("audio.wav", fs, audio)

while True:
    listen_for_wakeword()
    speak("Yes?")
    record_command()

    text = transcribe("audio.wav")
    print("You said:", text)

    resp = ask_brain(text)
    speak(resp["speech"])

    if "action" in resp:
        execute(resp["action"], resp["value"])
