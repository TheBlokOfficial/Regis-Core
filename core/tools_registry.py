import json
import logging
from typing import Any, Callable

class ToolsRegistry:
    """Rejestr narzędzi dostarczanych dla modelu LLM."""
    
    def __init__(self, ha_client):
        self.ha_client = ha_client
        
        # Schematy narzędzi zgodne z formatem Ollamy (bazującym na OpenAI JSON Schema)
        self.tools_schema = [
            {
                "type": "function",
                "function": {
                    "name": "get_devices",
                    "description": "Zwraca listę dostępnych urządzeń w systemie (np. nazwy świateł, przełączników). Użyj tego, by sprawdzić, czym możesz sterować.",
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
                "function": {
                    "name": "get_device_state",
                    "description": "Zwraca dokładny obecny stan urządzenia dla podanego entity_id.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "entity_id": {
                                "type": "string",
                                "description": "Dokładne ID encji, np. 'light.salon'"
                            }
                        },
                        "required": ["entity_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "execute_ha_action",
                    "description": "Wykonuje fizyczną akcję na urządzeniu. Opcjonalnie podaj parameters np. {'brightness_pct': 50}.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string",
                                "description": "Typ akcji, np. 'turn_on' lub 'turn_off'."
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
            }
        ]
        
    def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> str:
        """Kieruje wywołanie narzędzia do odpowiedniej logiki."""
        try:
            if tool_name == "get_devices":
                return self._get_devices(arguments.get("domain"))
            elif tool_name == "get_device_state":
                return self._get_device_state(arguments.get("entity_id", ""))
            elif tool_name == "execute_ha_action":
                return self._execute_ha_action(
                    arguments.get("action", ""),
                    arguments.get("entity_id", ""),
                    arguments.get("parameters", {})
                )
            else:
                return f'{{"error": "Nieznane narzędzie: {tool_name}"}}'
        except Exception as e:
            logging.error(f"Błąd wykonania narzędzia {tool_name}: {e}")
            return f'{{"error": "Wystąpił błąd podczas wykonania: {str(e)}"}}'

    def _get_devices(self, domain: str = None) -> str:
        states = self.ha_client.get_all_states()
        devices = []
        for entity_id, data in states.items():
            if domain and not entity_id.startswith(f"{domain}."):
                continue
            devices.append({"entity_id": entity_id, "name": data.get("friendly_name")})
        return json.dumps({"devices": devices}, ensure_ascii=False)

    def _get_device_state(self, entity_id: str) -> str:
        states = self.ha_client.get_all_states()
        if entity_id in states:
            return json.dumps(states[entity_id], ensure_ascii=False)
        return json.dumps({"error": f"Urządzenie o ID {entity_id} nie zostało znalezione."}, ensure_ascii=False)

    def _execute_ha_action(self, action: str, entity_id: str, parameters: dict[str, Any]) -> str:
        success = self.ha_client.execute_action(action, entity_id, parameters)
        if success:
            return json.dumps({"result": "success", "message": f"Wykonano akcję {action} na {entity_id}."})
        else:
            return json.dumps({"result": "error", "message": f"Nie udało się wykonać {action} na {entity_id}."})
