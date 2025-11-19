import subprocess


def transcribe(audio_path="audio.wav"):
    result = subprocess.run(
        ["./whisper", "-m", "models/whisper-base.en.bin", "-f", audio_path, "--no-timestamps"],
        stdout=subprocess.PIPE,
        text=True
    )
    return result.stdout.strip()
