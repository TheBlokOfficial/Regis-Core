BASE_TOOLS_SCHEMA = [
    {
        "type": "function",
        "required_tier": "basic",
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
        "required_tier": "basic",
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
        "required_tier": "basic",
        "function": {
            "name": "execute_ha_action",
            "description": "Wykonuje fizyczną akcję na urządzeniach. NIGDY nie zgaduj entity_id! Zawsze najpierw wywołaj narzędzie `get_devices`, przeczytaj wyniki i dopiero z nich skopiuj właściwe identyfikatory. Jeśli używasz parametrów (np. zmiana jasności oświetlenia), akcja zawsze musi być ustawiona na 'turn_on'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["turn_on", "turn_off", "toggle"],
                        "description": "Typ akcji. DOZWOLONE SĄ WYŁĄCZNIE WARTOSCI: 'turn_on', 'turn_off', 'toggle'. NIE UŻYWAJ INNYCH."
                    },
                    "entity_id": {
                        "type": ["string", "array"],
                        "items": {
                            "type": "string"
                        },
                        "description": "Dokładne ID encji (np. 'light.salon') lub lista ID (np. ['light.1', 'light.2'])."
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
        "required_tier": "basic",
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
        "required_tier": "basic",
        "function": {
            "name": "get_weather",
            "description": "Zwraca aktualne informacje o pogodzie w podanej lokalizacji (mieście). Używaj, gdy użytkownik pyta o pogodę.",
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
