import json
import urllib.request
import urllib.error

OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_GENERATE_URL = f"{OLLAMA_BASE_URL}/api/generate"
OLLAMA_TAGS_URL = f"{OLLAMA_BASE_URL}/api/tags"

MODEL_NAME = "hf.co/speakleash/Bielik-11B-v3.0-Instruct-GGUF" 

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

def get_available_models():
    """Pobiera z lokalnej instancji Ollamy listę dostępnych modeli."""
    req = urllib.request.Request(OLLAMA_TAGS_URL, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            models = [model['name'] for model in data.get('models', [])]
            return models
    except urllib.error.URLError as e:
        print(f"[BŁĄD] Nie można połączyć się z Ollama: {e}")
        return []

def generate_response(prompt, ha_state):
    system_p = SYSTEM_PROMPT.replace("{ha_state}", json.dumps(ha_state, indent=2))
    
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "system": system_p,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.5
        }
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(OLLAMA_GENERATE_URL, data=data, headers={'Content-Type': 'application/json'})
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result.get("response", "")
    except urllib.error.URLError as e:
        return f'{{"action": "none", "entity_id": "none", "reply": "[BŁĄD] Nie można połączyć się z Ollama: {e}"}}'
