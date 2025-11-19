import json
import subprocess
import tempfile


def ask_brain(prompt):
    # pass system + user message into llama.cpp
    full_prompt = open("system_prompt.txt").read() + "\nUSER: " + prompt + "\nASSISTANT:"

    result = subprocess.run(
        [
            "./llama",
            "-m", "models/phi3-mini.gguf",
            "-p", full_prompt,
            "-n", "256",
            "--temp", "0.6"
        ],
        stdout=subprocess.PIPE,
        text=True
    )

    output = result.stdout.strip()

    # get last JSON block llama returns
    try:
        start = output.rindex("{")
        json_str = output[start:]
        return json.loads(json_str)
    except Exception:
        return {"speech": "I couldn't parse that."}
