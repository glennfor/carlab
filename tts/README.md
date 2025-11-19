# TTS Utilities

This directory contains text-to-speech utilities for the carlab project.

## Examples

See example usage files:

- **Offline TTS**: `example_offline.py` - Examples using Piper TTS (local, no internet)
- **Online TTS**: `example_online.py` - Examples using Google GenAI TTS (cloud-based)

Run examples:

```bash
# Offline examples
python tts/example_offline.py

# Online examples (requires GEMINI_API_KEY)
python tts/example_online.py
```

## Available TTS Engines

### 1. Piper TTS (`speak.py`)

Local, offline TTS using Piper. No internet connection required.

**Usage:**

```python
from tts.speak import speak, speak_async

speak("Hello, world!")
speak_async("This is non-blocking")
```

### 2. Google GenAI TTS (`google_tts.py`)

Low-latency cloud-based TTS using Google GenAI (Gemini) TTS API. Provides high-quality voice synthesis with streaming audio output. Supports both direct text-to-speech and prompt-to-speech modes.

**Setup:**

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Set up Google GenAI API key:
   - Get an API key from [Google AI Studio](https://ai.google.dev/)
   - Set the `GEMINI_API_KEY` environment variable:
     ```bash
     export GEMINI_API_KEY="your-api-key-here"
     ```
   - Or pass the API key directly when using the functions

**Usage:**

#### Direct Text-to-Speech

```python
from tts.google_tts import speak, speak_async, GoogleTTS

# Simple usage (uses singleton instance)
speak("Hello, world!")

# With custom API key
speak("Hello, world!", api_key="your-api-key")

# With custom voice (see available voices below)
speak("Hello, world!", voice_name="Puck")

# Async usage
thread = speak_async("This is non-blocking")
```

#### Prompt-to-Speech

Generate content from a prompt using Gemini, then convert to speech:

```python
from tts.google_tts import speak_from_prompt, speak_from_prompt_async

# Generate and speak from prompt
speak_from_prompt("Tell me a short joke about robots")

# Async prompt-to-speech
thread = speak_from_prompt_async("Explain quantum computing in simple terms")
```

#### Advanced Usage

```python
from tts.google_tts import GoogleTTS

# Create instance with custom settings
tts = GoogleTTS(
    api_key="your-api-key",
    model="gemini-2.5-flash-preview-tts",
    voice_name="Kore"
)

# Direct TTS
tts.speak("Hello, world!")
tts.speak_async("Non-blocking")

# Prompt-to-speech
tts.speak_from_prompt("Generate a motivational quote")
tts.speak_from_prompt_async("Tell me about the weather")

# Clean up resources
tts.close()
```

**Available Voices:**
The TTS supports 30 prebuilt voices. Some popular options:

- **Kore** - Firm
- **Puck** - Upbeat
- **Zephyr** - Bright
- **Fenrir** - Excitable
- **Charon** - Informative
- **Leda** - Youthful
- And 24 more...

See the [full list](https://ai.google.dev/gemini-api/docs/speech-generation#voice-options) for all available voices.

**Supported Models:**

- `gemini-2.5-flash-preview-tts` (default, faster)
- `gemini-2.5-pro-preview-tts` (higher quality)

**Features:**

- Low-latency streaming audio output
- Direct audio playback without intermediate files
- Support for 30+ voices and 24 languages
- Synchronous and asynchronous modes
- Prompt-to-speech mode (generate content then speak)
- Optimized for Raspberry Pi

**Note:** Requires internet connection and Google GenAI API key. The API automatically detects the input language.
