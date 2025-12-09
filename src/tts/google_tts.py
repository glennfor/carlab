
import subprocess
import tempfile
import os
import base64
import base64
import os
# from pydub import AudioSegment
# import subprocess
# import tempfile
import threading
import io
import wave
# import librosa
# import audioop
import pyaudio
from google import genai
from google.genai import types


def wave_file(filename, pcm, channels=1, rate=24000, sample_width=2):
   with wave.open(filename, "wb") as wf:
      wf.setnchannels(channels)
      wf.setsampwidth(sample_width)
      wf.setframerate(rate)
      wf.writeframes(pcm)

class GoogleTTS:
    def __init__(self, api_key=None, model="gemini-2.5-flash-preview-tts", voice_name="Kore"):
        """
        Initialize Google GenAI TTS client.
        
        Args:
            api_key: Google GenAI API key. If None, uses GEMINI_API_KEY env var.
            model: TTS model name (default: "gemini-2.5-flash-preview-tts")
            voice_name: Voice name from available options (default: "Kore")
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key required. Set GEMINI_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        self.client = genai.Client(api_key=self.api_key)
        self.model = model
        self.voice_name = voice_name
        

        
        # PyAudio setup for direct streaming
        self.pyaudio_instance = pyaudio.PyAudio()
        self.sample_rate = 24000
        self.channels = 1
        self.format = pyaudio.paInt16
        # Find your USB sound card index
        self.device_index = self._find_usb_audio_device()
        if self.device_index is None:
            print("Warning: USB audio device not found! Falling back to default.")
            self.device_index = None  # will use default (often wrong)

        print(f"Using audio output device index: {self.device_index}")
    
    def _synthesize_speech(self, text):
        """
        Synthesize speech from text using Gemini TTS API.
        
        Args:
            text: Text to convert to speech
            
        Returns:
            bytes: Raw PCM audio data
        """
        response = self.client.models.generate_content(
            model=self.model,
            contents=text,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=self.voice_name,
                        )
                    )
                ),
            )
        )
        
        # Extract audio data from response
        if not response.candidates or not response.candidates[0].content.parts:
            raise Exception("No audio data in response")
        
        inline_data = response.candidates[0].content.parts[0].inline_data
        if not inline_data or not inline_data.data:
            raise Exception("No audio data in response parts")
        
        # Decode base64 audio data (handle both string and bytes)
        data = inline_data.data
        if isinstance(data, str):
            audio_data = base64.b64decode(data)
        elif isinstance(data, bytes):
            # Try to decode if it looks like base64, otherwise use as-is
            try:
                audio_data = base64.b64decode(data)
            except Exception:
                audio_data = data
        else:
            raise Exception(f"Unexpected audio data type: {type(data)}")
        
        return audio_data
    
    def _play_audio_stream(self, audio_data):
        """
        Play audio data handling both RAW PCM and WAV containers.
        """
        try:
            # Create a virtual file in memory
            file_stream = io.BytesIO(audio_data)
            
            # Try to open it as a WAV file to read the headers
            try:
                wf = wave.open(file_stream, 'rb')
                # If successful, read parameters from the file header
                channels = wf.getnchannels()
                rate = wf.getframerate()
                width = wf.getsampwidth()
                
                # Map wave width to pyaudio format
                pa_format = self.pyaudio_instance.get_format_from_width(width)
                
                # Read the actual audio frames (removing the header)
                chunk_data = wf.readframes(wf.getnframes())
                wf.close()
                
                print(f"DEBUG: Detected WAV. Rate: {rate}, Channels: {channels}, Width: {width}")

            except wave.Error:
                # If it fails, fall back to your hardcoded raw settings
                print("DEBUG: Could not parse WAV header. Playing as Raw PCM.")
                channels = self.channels
                rate = self.sample_rate
                pa_format = self.format
                chunk_data = audio_data

            # Open stream with the CORRECT parameters found above
            stream = self.pyaudio_instance.open(
                format=pa_format,
                channels=channels,
                rate=rate,
                output=True
            )
            
            try:
                stream.write(chunk_data)
            finally:
                stream.stop_stream()
                stream.close()
                
        except Exception as e:
            raise Exception(f"Audio playback error: {e}")
    
    def _play_audio_stream_old(self, audio_data):
        """
        Play audio data directly from memory stream.
        
        Args:
            audio_data: Raw PCM audio bytes to play
            
        Raises:
            Exception: If audio playback fails
        """
        try:
            stream = self.pyaudio_instance.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                output=True,
            )
            
            try:
                stream.write(audio_data)
            finally:
                stream.stop_stream()
                stream.close()
        except Exception as e:
            raise Exception(f"Audio playback error: {e}")
    
    def speak_old(self, text):
        """
        Synthesize and play text synchronously.
        
        Args:
            text: Text to speak
            
        Raises:
            Exception: If TTS synthesis or playback fails
        """
        try:
            audio_data = self._synthesize_speech(text)
            self._play_audio_stream(audio_data)
        except Exception as e:
            raise Exception(f"TTS error: {e}")
    
    # def speak(self, text):
    #     """
    #     Synthesize speech and play using native ALSA 'aplay'.
    #     """
    #     try:
    #         # 1. Generate Content
    #         response = self.client.models.generate_content(
    #             model=self.model,
    #             contents=text,
    #             config=types.GenerateContentConfig(
    #                 response_modalities=["AUDIO"],
    #                 speech_config=types.SpeechConfig(
    #                     voice_config=types.VoiceConfig(
    #                         prebuilt_voice_config=types.PrebuiltVoiceConfig(
    #                             voice_name=self.voice_name,
    #                         )
    #                     )
    #                 ),
    #             )
    #         )
            
    #         if not response.candidates or not response.candidates[0].content.parts:
    #             print("Error: No content returned")
    #             return

    #         inline_data = response.candidates[0].content.parts[0].inline_data
    #         audio_bytes = base64.b64decode(inline_data.data)

    #         # 2. Save to temp WAV file
    #         # aplay requires a file path to read headers correctly
    #         with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
    #             f.write(audio_bytes)
    #             temp_filename = f.name

    #         # 3. Play with aplay
    #         # -q: Quiet mode (suppress text output)
    #         # This call blocks until audio finishes. Use speak_async for non-blocking.
    #         subprocess.run(["aplay", "-q", temp_filename])
            
    #         # 4. Cleanup
    #         os.remove(temp_filename)

    
        # except Exception as e:
        #     print(f"TTS Error: {e}")
    def speak(self, text):
        """
        Speak using aplay (works on 99.9% of Raspberry Pi USB speakers)
        """
        try:
            # 1. Generate 24kHz raw PCM from Gemini
            response = self.client.models.generate_content(
                model=self.model,
                contents=text,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=self.voice_name,
                            )
                        )
                    ),
                )
            )
            
            # audio_data = base64.b64decode(
            #     response.candidates[0].content.parts[0].inline_data.data
            # )
            data = response.candidates[0].content.parts[0].inline_data.data

            file_name='out.wav'
            wave_file(file_name, data)
            # 2. Write to temporary raw file
            # with tempfile.NamedTemporaryFile(suffix=".raw", delete=False) as f:
            #     f.write(audio_data)
            #     temp_path = f.name

            # 3. Play with aplay — this works on ALL USB speakers
            try:
                subprocess.run(["aplay", "-q", file_name], check=True)
                    # subprocess.run([
                    #     "aplay",
                    #     "-q",           # quiet
                    #     "-t", "raw",    # raw PCM
                    #     "-f", "S16_LE", # 16-bit little-endian
                    #     "-r", "24000",  # 24kHz
                    #     "-c", "1",      # mono
                    #     temp_path
                    # ], check=True)

                    
                print(f"Spoke: {text}")
            finally:
                pass
                # os.unlink(temp_path)  # delete temp file

        except Exception as e:
            print(f"TTS Error: {e}")
    def speak222(self, text):
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=text,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(...),
                )
            )
            
            print("DEBUG: Response received")
            raw_pcm = base64.b64decode(response.candidates[0].content.parts[0].inline_data.data)

            # Convert raw 24kHz 16-bit mono PCM → AudioSegment
            print("DEBUG: Converting raw PCM to AudioSegment")
            audio = AudioSegment(
                data=raw_pcm,
                sample_width=2,
                frame_rate=24000,
                channels=1
            )

            # Resample to 48kHz and export as raw again
            print("DEBUG: Resampling to 48kHz")
            audio_48k = audio.set_frame_rate(48000)
            raw_48k = audio_48k.raw_data

            print("DEBUG: Opening PyAudio stream")
            stream = self.pyaudio_instance.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=48000,
                output=True,
                output_device_index=self.device_index
            )
            print("DEBUG: Writing PCM data to stream")
            stream.write(raw_48k)
            print("DEBUG: Stopping stream")
            stream.stop_stream()
            print("DEBUG: Closing stream")
            stream.close()

        except Exception as e:
            print(f"TTS Error: {e}")
    def speak22(self, text):
        """
        Synthesize speech and stream raw PCM to PyAudio.
        """
        try:
            # 1. Generate Audio
            response = self.client.models.generate_content(
                model=self.model,
                contents=text,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=self.voice_name,
                            )
                        )
                    ),
                )
            )
            
            if not response.candidates or not response.candidates[0].content.parts:
                print("Error: No content returned")
                return

            inline_data = response.candidates[0].content.parts[0].inline_data
            audio_bytes = base64.b64decode(inline_data.data)

            # 2. STRIP THE HEADER (The Fix)
            # Gemini sends a WAV file (Linear16 + Header).
            # The header is standard 44 bytes.
            # If we play the header, we hear "TSK". If we skip it, we hear audio.
            # if audio_bytes.startswith(b'RIFF'):
            #     # Skip the first 44 bytes (WAV Header)
            #     pcm_data = audio_bytes[44:]
            # else:
            #     # If no header (rare), play as is
            #     pcm_data = audio_bytes

            # # 3. Stream to PyAudio
            # stream = self.pyaudio_instance.open(
            #     format=self.format,
            #     channels=self.channels,
            #     rate=self.sample_rate,
            #     output=True
            # )

            # print("DEBUG: Streaming audio to PyAudio")
            # with io.BytesIO(audio_bytes) as wav_io:
            #     with wave.open(wav_io, 'rb') as wf:
            #         pcm_data = wf.readframes(wf.getnframes())   # this is pure PCM

            # print("DEBUG: Opening PyAudio stream")
            # stream = self.pyaudio_instance.open(
            #     format=self.pyaudio_instance.get_format_from_width(wf.getsampwidth()),
            #     channels=wf.getnchannels(),
            #     rate=wf.getframerate(),
            #     output=True,
            # )
            
            # print("DEBUG: Writing PCM data to stream")
            # stream.write(pcm_data)
            # print("DEBUG: Stopping stream")
            # stream.stop_stream()
            # print("DEBUG: Closing stream")
            # stream.close()


            


            # inline_data = response.candidates[0].content.parts[0].inline_data
            # audio_bytes = base64.b64decode(inline_data.data)

            # # Gemini TTS returns raw 24kHz, 16-bit, mono PCM (little-endian)
            # # No WAV header → treat as raw PCM directly
            # print("DEBUG: Opening PyAudio stream")
            # stream = self.pyaudio_instance.open(
            #     format=pyaudio.paInt16,        # 16-bit
            #     channels=1,                    # mono
            #     rate=24000,                    # fixed sample rate
            #     output=True,
            #     output_device_index=self.device_index
            # )

            #==
            inline_data = response.candidates[0].content.parts[0].inline_data
            audio_24khz = base64.b64decode(inline_data.data)  # 24kHz, 16-bit, mono

            # 2. RESAMPLE from 24kHz → 48kHz (most USB devices support this)
            audio_48khz = audioop.ratecv(
                audio_24khz, 
                2,              # sample width (2 bytes = 16-bit)
                1,              # mono
                24000,          # source rate
                48000,          # target rate
                None            # no state
            )[0]

            # 3. Play at 48kHz (almost all USB devices support this)
            stream = self.pyaudio_instance.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=48000,                    # ← now 48kHz
                output=True,
                output_device_index=self.device_index
            )

            print("DEBUG: Writing PCM data to stream")
            stream.write(audio_48khz)   # direct raw PCM write

            print("DEBUG: Stopping stream")
            stream.stop_stream()
            print("DEBUG: Closing stream")
            stream.close()

        except Exception as e:
            print(f"TTS Error: {e}")

    def _find_usb_audio_device(self):
        """Auto-detect USB sound card (skip HDMI and built-in analog)"""
        info = self.pyaudio_instance.get_host_api_info_by_index(0)
        num_devices = info.get('deviceCount')

        for i in range(num_devices):
            device = self.pyaudio_instance.get_device_info_by_index(i)
            if (device['maxOutputChannels'] > 0 and 
                'USB' in device['name'] and 
                'bcm2835' not in device['name'].lower()):  # skip built-in
                print(f"Found USB audio device: {device['name']} (index {i})")
                return i
        return None

    def speak_from_prompt(self, prompt, generation_model="gemini-2.0-flash"):
        """
        Generate content from a prompt using Gemini, then convert to speech.
        
        Args:
            prompt: Prompt to generate content from
            generation_model: Model to use for text generation (default: "gemini-2.0-flash")
            
        Raises:
            Exception: If generation or TTS fails
        """
        try:
            # First, generate text content from prompt
            text_response = self.client.models.generate_content(
                model=generation_model,
                contents=prompt,
            )
            
            generated_text = text_response.text
            if not generated_text:
                raise Exception("No text generated from prompt")
            
            # Then convert generated text to speech
            self.speak(generated_text)
        except Exception as e:
            raise Exception(f"Prompt-to-speech error: {e}")
    
    def _speak_worker(self, text):
        """Worker function for async speaking."""
        self.speak(text)
    
    def _speak_from_prompt_worker(self, prompt, generation_model):
        """Worker function for async prompt-to-speech."""
        self.speak_from_prompt(prompt, generation_model)
    
    def speak_async(self, text):
        """
        Synthesize and play text asynchronously.
        
        Args:
            text: Text to speak
            
        Returns:
            Thread object
        """
        thread = threading.Thread(target=self._speak_worker, args=(text,))
        thread.start()
        return thread
    
    def speak_from_prompt_async(self, prompt, generation_model="gemini-2.0-flash"):
        """
        Generate content from prompt and speak asynchronously.
        
        Args:
            prompt: Prompt to generate content from
            generation_model: Model to use for text generation (default: "gemini-2.0-flash")
            
        Returns:
            Thread object
        """
        thread = threading.Thread(
            target=self._speak_from_prompt_worker,
            args=(prompt, generation_model)
        )
        thread.start()
        return thread
    
    def close(self):
        """Clean up PyAudio resources."""
        if self.pyaudio_instance:
            self.pyaudio_instance.terminate()
