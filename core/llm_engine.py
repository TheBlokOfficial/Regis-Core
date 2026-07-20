import json
import logging
import requests
from requests.exceptions import RequestException
from typing import Any

from core.exceptions import LLMConnectionError

OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_GENERATE_URL = f"{OLLAMA_BASE_URL}/api/generate"
OLLAMA_TAGS_URL = f"{OLLAMA_BASE_URL}/api/tags"

SYSTEM_PROMPT = """Jesteś inteligentnym lokajem domowym o imieniu Regis.
Oto obecny stan domu (w formacie JSON):
{ha_state}

Zasada Krytyczna: TWOJA ODPOWIEDŹ ZAWSZE MUSI BYĆ W FORMACIE JSON. Nigdy nie pisz zwykłego tekstu!
Struktura Twojej odpowiedzi musi wyglądać dokładnie tak:
{
  "action": "turn_on" | "turn_off" | "none",
  "entity_id": "<TUTAJ_WPISZ_DOKŁADNE_ID_ENCJI_ZE_STANU_DOMU>" | "none",
  "parameters": {"brightness_pct": 10}, 
  "reply": "Tutaj krótko i zwięźle napisz to, co odpowiadasz na głos po polsku."
}
*Uwaga: Klucz 'parameters' dodawaj tylko, gdy użytkownik prosi o zmianę jasności:
- użyj `brightness_pct: 30` aby ustawić jasność dokładnie na 30%
- użyj `brightness_step_pct: 10` aby zwiększyć obecną jasność o 10% (lub -10 aby zmniejszyć o 10%).
Jeśli nie ma takich wymagań, daj po prostu pusty obiekt {}.

Przykłady:
Użytkownik: Włącz telewizor.
Wygeneruj: {"action": "turn_on", "entity_id": "media_player.telewizor_w_sypialni", "parameters": {}, "reply": "Zrobiłem to."}

Użytkownik: Włącz światło w salonie na 30%.
Wygeneruj: {"action": "turn_on", "entity_id": "light.salon", "parameters": {"brightness_pct": 30}, "reply": "Zrobiłem to."}

Użytkownik: Siema, co tam?
Wygeneruj: {"action": "none", "entity_id": "none", "parameters": {}, "reply": "Witaj! Czekam na Twoje polecenia."}
"""

class LLMEngine:
    """Silnik odpowiadający za komunikację z lokalnym serwerem Ollama."""

    def __init__(self, model_name: str, temperature: float = 0.5):
        """Inicjalizuje silnik z odpowiednim modelem.
        
        Args:
            model_name (str): Nazwa modelu używanego w Ollamie.
            temperature (float): Poziom losowości generowanych odpowiedzi.
        """
        self.model_name = model_name
        self.temperature = temperature
        logging.info(f"Zainicjalizowano LLMEngine: Model={model_name}, Temp={temperature}")

    @staticmethod
    def get_available_models() -> list[str]:
        """Pobiera z lokalnej instancji Ollamy listę dostępnych modeli.
        
        Returns:
            list[str]: Lista pobranych modeli.
        Raises:
            LLMConnectionError: Gdy nie można nawiązać połączenia z serwerem Ollama.
        """
        try:
            response = requests.get(OLLAMA_TAGS_URL, timeout=5)
            response.raise_for_status()
            data = response.json()
            models = [model['name'] for model in data.get('models', [])]
            return models
        except RequestException as e:
            logging.error(f"Nie można połączyć się z serwerem Ollama: {e}")
            raise LLMConnectionError(f"Ollama API Error: {e}")

    def generate_response(self, prompt: str, ha_state: dict[str, Any]) -> str:
        """Generuje zapytanie do modelu LLM i formatuje odpowiedź.
        
        Args:
            prompt (str): Polecenie od użytkownika.
            ha_state (dict[str, Any]): Aktualny stan urządzeń Home Assistanta.
            
        Returns:
            str: JSON w postaci stringa zwrócony przez model.
        Raises:
            LLMConnectionError: Jeśli wygenerowanie odpowiedzi się nie powiodło.
        """
        system_p = SYSTEM_PROMPT.replace("{ha_state}", json.dumps(ha_state, indent=2))
        
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "system": system_p,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": self.temperature
            }
        }
        
        try:
            logging.debug(f"Wysyłam prompt do Ollamy ({self.model_name}): {prompt}")
            response = requests.post(OLLAMA_GENERATE_URL, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")
        except RequestException as e:
            logging.error(f"Ollama Generation Error: {e}")
            raise LLMConnectionError(f"Nie udało się wygenerować odpowiedzi od modelu: {e}")
