import io
import logging

from core.llm_engine import LLMEngine
from core.stt_engine import STTEngine


class WorkerNode:
    """Węzeł Roboczy — hostuje model LLM i silnik STT.

    Odpowiada wyłącznie za inferencję: pętlę ReAct/NLU oraz transkrypcję audio.
    Nie zawiera żadnej logiki HTTP, routingu ani integracji z Home Assistant.
    Te odpowiedzialności należą do Kontrolera (apps/controller/).

    W przyszłości (po wdrożeniu Rejestru Encji) WorkerNode będzie działać
    jako osobny proces i komunikować się z Kontrolerem przez własne API HTTP.
    Na tym etapie Kontroler importuje go bezpośrednio.
    """

    def __init__(self, model_name: str, tier: str, temperature: float, history_limit: int):
        """Inicjalizuje silniki LLM i STT.

        Args:
            model_name: Nazwa modelu w Ollamie (np. 'qwen2.5:14b-instruct').
            tier: Klasa modelu ('butler', 'regis', 'prime').
            temperature: Temperatura modelu (0.1 dla tool callingu).
            history_limit: Maksymalna liczba zapamiętanych tur konwersacji.
        """
        self.llm_engine = LLMEngine(
            model_name=model_name,
            tier=tier,
            temperature=temperature,
            history_limit=history_limit
        )
        self.stt_engine = STTEngine(model_size="small", language="pl")
        logging.info(f"WorkerNode uruchomiony. Model={model_name}, Tier={tier}")

    def handle_chat(
        self,
        message: str,
        tools_registry,
        on_tool_call=None,
        on_thought_token=None,
        on_content_token=None
    ) -> str:
        """Obsługuje zapytanie tekstowe — deleguje do pętli ReAct/NLU silnika LLM.

        Args:
            message: Polecenie użytkownika (tekst).
            tools_registry: Rejestr narzędzi z Kontrolera.
            on_tool_call: Callback logowania użycia narzędzia.
            on_thought_token: Callback tokenu wewnętrznego monologu.
            on_content_token: Callback tokenu odpowiedzi końcowej.

        Returns:
            Pełna tekstowa odpowiedź modelu.
        """
        return self.llm_engine.generate_response(
            message,
            tools_registry,
            on_tool_call=on_tool_call,
            on_thought_token=on_thought_token,
            on_content_token=on_content_token
        )

    def handle_audio(
        self,
        audio_bytes: bytes,
        tools_registry,
        on_stt_result=None,
        on_tool_call=None,
        on_thought_token=None,
        on_content_token=None
    ) -> str:
        """Obsługuje zapytanie audio — STT, a następnie deleguje do handle_chat.

        Args:
            audio_bytes: Surowe bajty pliku WAV.
            tools_registry: Rejestr narzędzi z Kontrolera.
            on_stt_result: Callback z wynikiem transkrypcji (tekst rozpoznanej mowy).
            on_tool_call: Callback logowania użycia narzędzia.
            on_thought_token: Callback tokenu wewnętrznego monologu.
            on_content_token: Callback tokenu odpowiedzi końcowej.

        Returns:
            Pełna tekstowa odpowiedź modelu, lub komunikat błędu STT.
        """
        audio_io = io.BytesIO(audio_bytes)
        text = self.stt_engine.transcribe_audio_file(audio_io)

        if not text:
            return "Nie rozpoznano żadnego tekstu ze strumienia audio."

        if on_stt_result:
            on_stt_result(text)

        return self.handle_chat(
            text,
            tools_registry,
            on_tool_call=on_tool_call,
            on_thought_token=on_thought_token,
            on_content_token=on_content_token
        )

    def clear_history(self) -> None:
        """Czyści historię konwersacji silnika LLM."""
        self.llm_engine.clear_history()
