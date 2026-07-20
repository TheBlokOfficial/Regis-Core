import urllib.request
import urllib.error
import json

HA_URL = "http://192.168.0.50:8123"
HA_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJkMzExNzI2ZmU3ZDE0MTQzYjQzYTgxODM3NDI5MzU4MyIsImlhdCI6MTc4NDQ5MDk5OCwiZXhwIjoyMDk5ODUwOTk4fQ.5En3I5XtflXdkuF8h4bU39ot3oHPu_pX-Yj9y6zJ8lc"

# Słownik nadpisujący niezrozumiałe nazwy z Home Assistanta na ludzkie nazwy dla LLMa
ALIASES = {
    "light.yeelight_colorc_0x1e367376": "Lampka Biurkowa (Mój Pokój)",
    "light.yeelight_colorc_0x1e367055": "Oświetlenie LED (Mój Pokój)"
}

def get_headers():
    return {
        "Authorization": f"Bearer {HA_TOKEN}",
        "Content-Type": "application/json"
    }

def get_all_states():
    """Pobiera z Home Assistanta listę wszystkich encji i ich stanów."""
    url = f"{HA_URL}/api/states"
    req = urllib.request.Request(url, headers=get_headers())
    
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            allowed_domains = ["light", "switch", "climate", "media_player"]
            
            filtered_state = {}
            for entity in data:
                entity_id = entity["entity_id"]
                domain = entity_id.split(".")[0]
                
                # Odrzucamy wszystkie encje ukryte oraz sensory (bo śmiecą prompta temperaturami rutera itp.)
                if domain not in allowed_domains:
                    continue
                
                # Zmieniamy surową nazwę na naszą własną, przyjazną z ALIASES (jeśli tam jest)
                original_name = entity["attributes"].get("friendly_name", "Nieznana Nazwa")
                friendly_name = ALIASES.get(entity_id, original_name)
                
                filtered_state[entity_id] = {
                    "state": entity["state"],
                    "friendly_name": friendly_name
                }
                    
            return filtered_state
    except urllib.error.URLError as e:
        print(f"[BŁĄD HA] Nie udało się pobrać stanu: {e}")
        return {}

def execute_action(action, entity_id, parameters=None):
    """Wysyła polecenie do fizycznego Home Assistanta."""
    if parameters is None:
        parameters = {}
        
    # Jeśli Qwen zwrócił tablicę urządzeń (wiele na raz), wykonujemy to w pętli
    if isinstance(entity_id, list):
        # print(f"[HA CLIENT] Wykryto tablicę urządzeń. Wykonuję operację masową na {len(entity_id)} urządzeniach...")
        all_success = True
        for single_id in entity_id:
            if not execute_action(action, single_id, parameters):
                all_success = False
        return all_success
        
    if not isinstance(entity_id, str):
        print("[HA CLIENT] Błąd: entity_id musi być ciągiem znaków lub listą.")
        return False
        
    domain = entity_id.split(".")[0]
    
    if action == "turn_on":
        service = "turn_on"
    elif action == "turn_off":
        service = "turn_off"
    else:
        print(f"[HA CLIENT] Nie obsługuję jeszcze akcji: {action}")
        return False
        
    url = f"{HA_URL}/api/services/{domain}/{service}"
    
    # Budujemy payload, dodając do niego opcjonalne parametry (np. jasność, temperatura)
    payload_dict = {"entity_id": entity_id}
    if isinstance(parameters, dict):
        payload_dict.update(parameters)
        
    payload = json.dumps(payload_dict).encode('utf-8')
    req = urllib.request.Request(url, data=payload, headers=get_headers(), method="POST")
    
    try:
        with urllib.request.urlopen(req) as response:
            if response.getcode() == 200:
                # print(f"[HA CLIENT] Sukces! Wykonano fizycznie {service} na {entity_id} z parametrami {parameters}")
                return True
            else:
                print(f"[HA CLIENT] Błąd serwera HA: {response.getcode()}")
                return False
    except urllib.error.URLError as e:
        print(f"[BŁĄD HA] Wykonanie akcji odrzucone: {e}")
        return False

# Szybki zrzut testowy
if __name__ == "__main__":
    print("Łączę się z Twoim fizycznym Home Assistantem...")
    states = get_all_states()
    print("Udało się! Oto wykryte urządzenia (odfiltrowane do najważniejszych):")
    print(json.dumps(states, indent=2, ensure_ascii=False))
