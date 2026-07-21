import json

BASE_TOOLS_SCHEMA = [
    {
        "type": "function",
        "required_tier": "butler",
        "function": {
            "name": "get_devices",
            "description": "Zwraca listę dostępnych urządzeń w systemie (np. nazwy świateł, przełączników). Zawsze używaj tego narzędzia przed próbą manipulacji nowym urządzeniem, by poznać poprawne entity_id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "Opcjonalna domena, np. 'light' lub 'media_player', aby przefiltrować urządzenia."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "required_tier": "butler",
        "function": {
            "name": "get_device_state",
            "description": "Zwraca dokładny obecny stan urządzenia dla podanego entity_id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "entity_id": {
                        "type": ["string", "array"],
                        "items": {
                            "type": "string"
                        },
                        "description": "Dokładne ID encji (np. 'light.salon') lub lista ID (np. ['light.1', 'light.2'])."
                    }
                },
                "required": ["entity_id"]
            }
        }
    },
    {
        "type": "function",
        "required_tier": "butler",
        "function": {
            "name": "execute_ha_action",
            "description": "Wykonuje fizyczną akcję na urządzeniach. Nigdy nie zgaduj entity_id — zawsze najpierw wywołaj get_devices. Jeśli ustawiasz parametry (np. jasność), akcja musi być 'turn_on'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["turn_on", "turn_off", "toggle"],
                        "description": "Typ akcji: 'turn_on', 'turn_off' lub 'toggle'."
                    },
                    "entity_id": {
                        "type": ["string", "array"],
                        "items": {
                            "type": "string"
                        },
                        "description": "Dokładne ID encji (np. 'light.salon') lub lista ID."
                    },
                    "parameters": {
                        "type": "object",
                        "description": "Dodatkowe parametry akcji, np. zmiana jasności."
                    }
                },
                "required": ["action", "entity_id"]
            }
        }
    },
    {
        "type": "function",
        "required_tier": "butler",
        "function": {
            "name": "get_current_time",
            "description": "Zwraca bieżącą datę i czas systemowy (razem z dniem tygodnia).",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "required_tier": "butler",
        "function": {
            "name": "get_weather",
            "description": "Zwraca aktualne informacje o pogodzie w podanym mieście.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "Nazwa miasta, np. 'Warszawa'."
                    }
                },
                "required": ["location"]
            }
        }
    }
]


def get_tools_for_tier(tier: str) -> list[dict]:
    """Filtruje schematy narzędzi na podstawie poziomu uprawnień (tier).
    Zwraca kopię bez niestandardowego pola 'required_tier'."""
    tier_clearance = {"butler": 1, "regis": 2, "prime": 3}
    current_clearance = tier_clearance.get(tier, 1)
    
    filtered = []
    for tool in BASE_TOOLS_SCHEMA:
        req_tier = tool.get("required_tier", "butler")
        if tier_clearance.get(req_tier, 1) <= current_clearance:
            tool_copy = tool.copy()
            tool_copy.pop("required_tier", None)
            filtered.append(tool_copy)
    return filtered


def render_tools_for_prompt(tier: str) -> str:
    """Renderuje schematy narzędzi do formatu tekstowego kompatybilnego z Hermes/Qwen.
    
    Zamiast wysyłać pole 'tools' do API Ollamy (co powoduje kolizję z natywnym
    blokiem instrukcji), wstrzykujemy opisy narzędzi bezpośrednio do system promptu
    w formacie natywnym dla treningu Qwen 2.5 (tagi <tools>).
    """
    tools = get_tools_for_tier(tier)
    tools_json = json.dumps(tools, ensure_ascii=False, indent=2)
    
    return f"""## Dostępne Narzędzia

Masz do dyspozycji narzędzia opisane poniżej w bloku `<tools>`. Aby użyć narzędzia, wygeneruj wywołanie w tagach:
<tool_call>
{{"name": "nazwa_narzędzia", "arguments": {{"parametr": "wartość"}}}}
</tool_call>

W jednej iteracji używaj dokładnie jednego narzędzia. Po wywołaniu otrzymasz wynik i możesz kontynuować.

<tools>
{tools_json}
</tools>"""
