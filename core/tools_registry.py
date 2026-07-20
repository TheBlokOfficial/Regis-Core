import json
import logging
from typing import Any, Callable

from core.schemas import BASE_TOOLS_SCHEMA

class ToolsRegistry:
    """Rejestr narzędzi dostarczanych dla modelu LLM."""
    
    def __init__(self, ha_client, tier: str = "advanced"):
        self.ha_client = ha_client
        self.tier = tier
        
        # Schematy narzędzi importowane z zewnętrznego pliku
        base_tools_schema = BASE_TOOLS_SCHEMA
        
        # Filtrowanie narzędzi na podstawie tieru
        filtered_schema = []
        for tool in base_tools_schema:
            req_tier = tool.get("required_tier", "basic")
            if self.tier == "basic" and req_tier == "advanced":
                continue
                
            # Usuwamy niestandardowe pole "required_tier", ponieważ API Ollamy może je odrzucić
            tool_copy = tool.copy()
            if "required_tier" in tool_copy:
                del tool_copy["required_tier"]
            filtered_schema.append(tool_copy)
            
        self.tools_schema = filtered_schema
        
    def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> str:
        """Kieruje wywołanie narzędzia do odpowiedniej logiki."""
        try:
            allowed_tools = [t["function"]["name"] for t in self.tools_schema]
            if tool_name not in allowed_tools:
                return f'{{"error": "Narzędzie {tool_name} nie istnieje lub odmowa dostępu w obecnym trybie."}}'

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
        try:
            states = self.ha_client.get_all_states()
        except Exception:
            states = {}
            
        if isinstance(entity_id, list):
            invalid_ids = [eid for eid in entity_id if eid not in states]
            if invalid_ids:
                return json.dumps({"result": "error", "message": f"Błąd: Podane ID {invalid_ids} nie istnieją w systemie! Zanim zgadniesz ID, musisz użyć narzędzia 'get_devices'. WYGENERUJ TERAZ blok JSON wywołujący get_devices, nie tłumacz się użytkownikowi!"}, ensure_ascii=False)
        elif isinstance(entity_id, str):
            if entity_id not in states:
                return json.dumps({"result": "error", "message": f"Błąd: Urządzenie o ID '{entity_id}' nie istnieje w systemie! Zanim zgadniesz ID, musisz użyć narzędzia 'get_devices'. WYGENERUJ TERAZ blok JSON wywołujący get_devices, nie pisz wymówek!"}, ensure_ascii=False)
                
        success = self.ha_client.execute_action(action, entity_id, parameters)
        if success:
            return json.dumps({"result": "success", "message": f"Wykonano akcję {action} na {entity_id}."})
        else:
            return json.dumps({"result": "error", "message": f"Nie udało się wykonać {action} na {entity_id}."})
