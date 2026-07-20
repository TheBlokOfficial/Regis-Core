import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE_FILE = os.path.join(BASE_DIR, "data", "ha_state.json")

DEFAULT_STATE = {
    "light.salon": "off",
    "light.kuchnia": "off",
    "sensor.temperatura_salon": 21.5,
    "climate.ogrzewanie": "off"
}

def load_state():
    if not os.path.exists(STATE_FILE):
        save_state(DEFAULT_STATE)
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=4)

def execute_action(action, entity_id, parameters=None):
    state = load_state()
    
    if action == "turn_on" and entity_id in state:
        state[entity_id] = "on"
        print(f"[HA-MOCK] Wykonano sprzętowo: Włączono {entity_id}")
    elif action == "turn_off" and entity_id in state:
        state[entity_id] = "off"
        print(f"[HA-MOCK] Wykonano sprzętowo: Wyłączono {entity_id}")
    elif action == "set_temperature":
        print(f"[HA-MOCK] Wykonano sprzętowo: Zmiana temperatury dla {entity_id}")
    else:
        print(f"[HA-MOCK] Błąd: Nieznana akcja {action} dla encji {entity_id}")
        return False
        
    save_state(state)
    return True
