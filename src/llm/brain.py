import json

from openai import OpenAI

client = OpenAI()

def ask_brain(text):
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": open("system_prompt.txt").read()},
            {"role": "user", "content": text}
        ]
    )
    raw = resp.choices[0].message.content
    return json.loads(raw)
