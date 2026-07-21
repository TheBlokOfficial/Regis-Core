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
            "name": "open_notebook_search",
            "description": "Przeszukuje Notatnik użytkownika (Pamięć Długoterminowa) w poszukiwaniu konkretnych informacji i kładzie wyniki na Twoim biurku. ZAWSZE preferuj wywołanie tego narzędzia bez argumentu 'query', aby otrzymać pełen spis dostępnych kluczy. TWARDA DYREKTYWA: Po użyciu tego narzędzia NIE wywołuj go ponownie ani nie używaj innych narzędzi do odczytu. Przejdź od razu do analizy bloku <desk_state>, który zaktualizował się na końcu Twojego kontekstu.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Opcjonalny klucz notatki do odczytania. Jeśli nie masz 100% pewności jak nazywa się klucz, zignoruj ten argument i wywołaj bez niego, by zdobyć listę wszystkich kluczy."
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
                        "description": "Treść faktu do zapamiętania. KATEGORYCZNY NAKAZ: Nie wklejaj suchych wycinków tekstu. Zawsze redaguj fakt jako pełne, obiektywne zdanie w 3. osobie z bogatym kontekstem. Zamiast 'Nysa' napisz 'Użytkownik poinformował, że obecnie mieszka w Nysie'."
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
            "name": "open_notes",
            "description": "Otwiera aplikację Brudnopisu (Staging) z zanotowanymi wcześniej szkicami i kładzie ją na Twoim biurku. Będziesz widział zawartość aplikacji dopóki jej nie zamkniesz. TWARDA DYREKTYWA: PO UŻYCIU TEGO NARZĘDZIA NIE WYWOŁUJ ŻADNYCH INNYCH NARZĘDZI ODCZYTU (ani open_notes, ani open_notebook_search). Przejdź od razu do analizy nowo wstrzykniętego bloku <desk_state>.",
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
            "name": "close_notes",
            "description": "Zamyka aplikację Brudnopisu, uwalniając Twoją pamięć operacyjną ze zbędnych danych. Używaj po skończonej pracy z notatkami.",
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
                        "description": "Klucz notatki. Bez spacji, z użyciem podkreślników."
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
