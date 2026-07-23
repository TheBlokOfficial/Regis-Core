import logging
from faster_whisper import WhisperModel
import io

class STTEngine:
    def __init__(self, model_size="small", language="pl"):
        logging.info(f"Ładowanie modelu STT Faster-Whisper ({model_size})...")
        self.model = WhisperModel(model_size, device="cpu", compute_type="int8")
        self.language = language

    def transcribe_audio_file(self, file_like_object) -> str:
        logging.info("Rozpoczęto transkrypcję po stronie serwera...")
        segments, info = self.model.transcribe(
            file_like_object, 
            beam_size=5, 
            language=self.language,
            condition_on_previous_text=False,
            initial_prompt="Zgaś światło. Włącz światło. Ustaw jasność. Otwórz rolety. Jaka jest pogoda?"
        )
        text = " ".join([segment.text for segment in segments]).strip()
        return text
