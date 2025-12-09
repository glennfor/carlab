import pvporcupine
import pyaudio


def listen_for_wakeword(keyword_path="robot.ppn"):
    porcupine = pvporcupine.create(keyword_paths=[keyword_path])
    audio = pyaudio.PyAudio()

    stream = audio.open(
        rate=porcupine.sample_rate,
        channels=1,
        format=pyaudio.paInt16,
        input=True,
        frames_per_buffer=porcupine.frame_length
    )

    print("Listening for wakeword...")

    while True:
        pcm = stream.read(porcupine.frame_length, exception_on_overflow=False)
        pcm = bytearray(pcm)

        if porcupine.process(pcm) >= 0:
            return True
