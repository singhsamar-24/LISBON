"""Voice Synthesis (TTS) and Speech Recognition (STT) for LISBON Butler."""

import queue
import re
import threading
from typing import Callable, List, Optional


def clean_for_speech(text: str) -> str:
    """Prepares text for natural speech synthesis by removing markdown and code artifacts."""
    if not text:
        return ""
    # Remove code blocks
    cleaned = re.sub(r"```[\s\S]*?```", " [code snippet omitted] ", text)
    # Remove inline code
    cleaned = re.sub(r"`([^`]+)`", r"\1", cleaned)
    # Remove markdown link URLs, keep anchor text
    cleaned = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", cleaned)
    # Remove header markers, bold/italics, bullet dashes
    cleaned = re.sub(r"[#*_~>]+", "", cleaned)
    # Remove emojis and special graphical unicode characters
    cleaned = re.sub(r"[^\x00-\x7F]+", " ", cleaned)
    # Clean bullet points and excessive whitespace
    cleaned = re.sub(r"^\s*[-•]\s*", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


class LisbonVoice:
    """Provides speech synthesis and voice input for the LISBON butler."""

    def __init__(
        self,
        enabled: bool = False,
        rate: int = 180,
        volume: float = 0.95,
        voice_id: Optional[str] = None,
    ):
        self.enabled = enabled
        self.rate = rate
        self.volume = max(0.0, min(1.0, volume))
        self.voice_id = voice_id
        self._speech_queue: queue.Queue = queue.Queue()
        self._worker_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._engine_lock = threading.Lock()
        self._start_worker()

    def _start_worker(self) -> None:
        """Starts the dedicated background TTS worker thread to prevent UI freezing."""
        if self._worker_thread is None or not self._worker_thread.is_alive():
            self._stop_event.clear()
            self._worker_thread = threading.Thread(target=self._tts_worker, daemon=True)
            self._worker_thread.start()

    def _tts_worker(self) -> None:
        """Worker loop that handles speech requests in sequence."""
        engine = None
        try:
            import pyttsx3

            engine = pyttsx3.init()
            engine.setProperty("rate", self.rate)
            engine.setProperty("volume", self.volume)
            if self.voice_id:
                try:
                    engine.setProperty("voice", self.voice_id)
                except Exception:
                    pass
        except Exception:
            engine = None

        while not self._stop_event.is_set():
            try:
                text = self._speech_queue.get(timeout=0.2)
            except queue.Empty:
                continue

            if text is None:  # Sentinel value to exit
                break

            if engine and text:
                try:
                    with self._engine_lock:
                        # Re-apply properties in case they changed
                        engine.setProperty("rate", self.rate)
                        engine.setProperty("volume", self.volume)
                        engine.say(text)
                        engine.runAndWait()
                except Exception:
                    # Fallback to SAPI via win32com if pyttsx3 encounters a COM loop issue
                    try:
                        import win32com.client

                        speaker = win32com.client.Dispatch("SAPI.SpVoice")
                        speaker.Rate = 0  # Normal rate
                        speaker.Volume = int(self.volume * 100)
                        speaker.Speak(text)
                    except Exception:
                        pass
            self._speech_queue.task_done()

    def speak(self, text: str, async_mode: bool = True) -> None:
        """Speaks the provided text aloud if voice is enabled."""
        if not self.enabled or not text:
            return

        speech_text = clean_for_speech(text)
        if not speech_text:
            return

        if async_mode:
            self._speech_queue.put(speech_text)
        else:
            # Synchronous direct speech via SAPI
            try:
                import win32com.client

                speaker = win32com.client.Dispatch("SAPI.SpVoice")
                speaker.Volume = int(self.volume * 100)
                speaker.Speak(speech_text)
            except Exception:
                self._speech_queue.put(speech_text)

    @staticmethod
    def get_best_microphone_index() -> Optional[int]:
        """Automatically selects the best physical microphone, avoiding dead virtual devices like Iriun."""
        try:
            import speech_recognition as sr
            mics = sr.Microphone.list_microphone_names()
            # 1. First priority: Realtek Microphone Array
            for i, name in enumerate(mics):
                nl = name.lower()
                if "iriun" in nl or "virtual" in nl or "mapper" in nl:
                    continue
                if "realtek" in nl and ("array" in nl or "mic" in nl):
                    return i
            # 2. Second priority: Any physical microphone
            for i, name in enumerate(mics):
                nl = name.lower()
                if "iriun" in nl or "virtual" in nl or "mapper" in nl or "stereo mix" in nl:
                    continue
                if "mic" in nl or "audio" in nl:
                    return i
            return None
        except Exception:
            return None

    def listen(self, phrase_time_limit: int = 10, timeout: int = 8, device_index: Optional[int] = None) -> Optional[str]:
        """Listens from the microphone and transcribes user speech to text."""
        try:
            import speech_recognition as sr
        except ImportError:
            return None

        recognizer = sr.Recognizer()
        recognizer.energy_threshold = 200
        recognizer.dynamic_energy_threshold = True

        if device_index is None:
            device_index = self.get_best_microphone_index()

        try:
            with sr.Microphone(device_index=device_index) as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.4)
                audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
                text = recognizer.recognize_google(audio)
                return text.strip()
        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            return ""  # Heard something but could not discern words
        except Exception:
            return None

    def toggle(self) -> bool:
        """Toggles voice synthesis on/off and returns the new state."""
        self.enabled = not self.enabled
        return self.enabled

    def get_available_voices(self) -> List[dict]:
        """Returns list of all installed system TTS voices."""
        try:
            import pyttsx3

            engine = pyttsx3.init()
            voices = engine.getProperty("voices")
            res = []
            for v in voices:
                res.append({"id": v.id, "name": v.name, "languages": getattr(v, "languages", [])})
            return res
        except Exception:
            return []

    def set_voice(self, voice_id: str) -> None:
        """Sets the active TTS voice ID."""
        self.voice_id = voice_id

    def stop(self) -> None:
        """Clears pending speech and stops the worker."""
        while not self._speech_queue.empty():
            try:
                self._speech_queue.get_nowait()
                self._speech_queue.task_done()
            except queue.Empty:
                break
        self._stop_event.set()
        self._speech_queue.put(None)
