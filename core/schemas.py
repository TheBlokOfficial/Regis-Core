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
            "description": "Zwraca aktualne informacje o pogodzie w podanym mieście. Jeśli użytkownik nie podał miasta — najpierw sprawdź Notatnik (read_notes), a jeśli pusty — zapytaj go o to wprost. Nie zgaduj miasta.",
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
    },
    {
        "type": "function",
        "required_tier": "butler",
        "function": {
            "name": "read_notes",
            "description": "Zwraca notatki z Pamięci Długoterminowej (Notatnika). Używaj tego, aby odświeżyć pamięć o użytkowniku po rozpoczęciu nowej sesji. ZAWSZE preferuj wywołanie tego narzędzia bez argumentu 'key', aby otrzymać pełen spis dostępnych kluczy, z których następnie wybierzesz właściwy.",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "description": "Opcjonalny klucz notatki do odczytania. Jeśli nie masz 100% pewności jak nazywa się klucz, zignoruj ten argument i wywołaj read_notes bez niego, by zdobyć listę wszystkich kluczy."
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
            "name": "queue_note",
            "description": "Zapisuje nową notatkę do kolejki buforowej (Staging). Używaj tego, aby zapamiętywać fakty o użytkowniku po usłyszeniu ich w rozmowie. Notatka zostanie później zweryfikowana przez system.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fact": {
                        "type": "string",
                        "description": "Treść faktu do zapamiętania, np. 'Mieszka w Nysie', 'Nie lubi wstawania wcześnie'."
                    }
                },
                "required": ["fact"]
            }
        }
    },
    {
        "type": "function",
        "required_tier": "regis",
        "function": {
            "name": "read_queue",
            "description": "Odczytuje zawartość kolejki brudnopisu (Staging).",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "required_tier": "regis",
        "function": {
            "name": "clear_queue",
            "description": "Usuwa przetworzone i zarchiwizowane notatki z kolejki brudnopisu na podstawie podanych ID. Używaj tego narzędzia tylko PO otrzymaniu wyniku potwierdzającego sukces z narzędzia save_note.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ids": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "Lista identyfikatorów (ID) notatek do usunięcia z kolejki."
                    }
                },
                "required": ["ids"]
            }
        }
    },
    {
        "type": "function",
        "required_tier": "regis",
        "function": {
            "name": "save_note",
            "description": "Zapisuje nową notatkę lub nadpisuje istniejącą w Pamięci Długoterminowej. Używaj tego do zapamiętywania preferencji użytkownika.",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "description": "Klucz notatki (np. 'pogoda_miasto', 'ulubiony_kolor'). Bez spacji, z użyciem podkreślników."
                    },
                    "content": {
                        "type": "string",
                        "description": "Treść notatki do zapamiętania. Twórz wyczerpujące wpisy, preferuj zapisywanie całych zdań z kontekstem (np. 'Użytkownik aktualnie mieszka w Nysie, ale rzadko bywa w centrum'), a nie pojedynczych słów."
                    }
                },
                "required": ["key", "content"]
            }
        }
    },
    {
        "type": "function",
        "required_tier": "regis",
        "function": {
            "name": "delete_note",
            "description": "Usuwa notatkę z Pamięci Długoterminowej.",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "description": "Klucz notatki do usunięcia."
                    }
                },
                "required": ["key"]
            }
        }
    }
]
