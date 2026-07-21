import json
import logging
from typing import Any, Callable

from core.schemas import BASE_TOOLS_SCHEMA

class ToolsRegistry:
    """Rejestr narzędzi dostarczanych dla modelu LLM."""
    
    def __init__(self, ha_client, tier: str = "regis"):
        self.ha_client = ha_client
        self.tier = tier
        
        # Schematy narzędzi importowane z zewnętrznego pliku
        base_tools_schema = BASE_TOOLS_SCHEMA
        
        # Filtrowanie narzędzi na podstawie tieru
        filtered_schema = []
        for tool in base_tools_schema:
            req_tier = tool.get("required_tier", "butler")
            if self.tier == "butler" and req_tier == "regis":
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
            elif tool_name == "get_current_time":
                return self._get_current_time()
            elif tool_name == "get_weather":
                return self._get_weather(arguments.get("location", ""))
            elif tool_name == "save_note":
                return self._save_note(arguments.get("key", ""), arguments.get("content", ""))
            elif tool_name == "read_notes":
                return self._read_notes(arguments.get("key"))
            elif tool_name == "delete_note":
                return self._delete_note(arguments.get("key", ""))
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

    def _get_device_state(self, entity_id: str | list[str]) -> str:
        states = self.ha_client.get_all_states()
        if isinstance(entity_id, list):
            results = {}
            for eid in entity_id:
                if eid in states:
                    results[eid] = states[eid]
                else:
                    results[eid] = {"error": "Urządzenie nie znalezione."}
            return json.dumps(results, ensure_ascii=False)
        else:
            if entity_id in states:
                return json.dumps(states[entity_id], ensure_ascii=False)
            return json.dumps({"error": f"Urządzenie o ID {entity_id} nie zostało znalezione."}, ensure_ascii=False)

    def _execute_ha_action(self, action: str, entity_id: str, parameters: dict[str, Any]) -> str:
        try:
            states = self.ha_client.get_all_states()
        except Exception:
            states = {}
            
        if action not in ["turn_on", "turn_off", "toggle"]:
            return json.dumps({"error": f"Invalid Action Error. You provided '{action}'. Only 'turn_on', 'turn_off', and 'toggle' are allowed. Fix your JSON and use 'turn_on' if you meant to change brightness/color."}, ensure_ascii=False)

        if isinstance(entity_id, list):
            invalid_ids = [eid for eid in entity_id if eid not in states]
            if invalid_ids:
                return json.dumps({"error": f"Invalid Entity Error. You provided non-existent IDs: {invalid_ids}. You MUST use 'get_devices' tool first to find correct entity IDs before trying to execute action."}, ensure_ascii=False)
        elif isinstance(entity_id, str):
            if entity_id not in states:
                return json.dumps({"error": f"Invalid Entity Error. You provided non-existent ID: '{entity_id}'. You MUST use 'get_devices' tool first to find correct entity IDs before trying to execute action."}, ensure_ascii=False)
                
        success = self.ha_client.execute_action(action, entity_id, parameters)
        if success:
            return json.dumps({"result": "success", "message": f"Wykonano akcję {action} na {entity_id}."})
        else:
            return json.dumps({"error": f"Execution Failed. Action {action} failed to apply on {entity_id}. Ensure parameters are correct for this device type."})

    def _get_current_time(self) -> str:
        import datetime
        now = datetime.datetime.now()
        return json.dumps({
            "current_time": now.strftime("%Y-%m-%d %H:%M:%S"),
            "weekday": now.strftime("%A")
        }, ensure_ascii=False)

    def _get_weather(self, location: str) -> str:
        if not location:
            return json.dumps({"error": "Brak lokalizacji. Opowiedz użytkownikowi, że potrzebujesz nazwy miasta."}, ensure_ascii=False)
        
        try:
            import requests
            # Używamy serwisu wttr.in dla prostych danych pogodowych
            url = f"https://wttr.in/{location}?format=j1"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Wyciąganie kluczowych danych, by nie przeciążyć tokenów
            current = data.get("current_condition", [{}])[0]
            if not current:
                return json.dumps({"error": "Nie znaleziono danych o pogodzie dla podanej lokalizacji."})
                
            weather_desc_pl_list = current.get("lang_pl", [])
            weather_desc = weather_desc_pl_list[0].get("value") if weather_desc_pl_list else current.get("weatherDesc", [{}])[0].get("value")
            
            result = {
                "location": location,
                "description": weather_desc,
                "temperature_C": current.get("temp_C"),
                "feels_like_C": current.get("FeelsLikeC"),
                "humidity_percent": current.get("humidity"),
                "wind_speed_kmh": current.get("windspeedKmph")
            }
            return json.dumps(result, ensure_ascii=False)
            
        except requests.exceptions.RequestException as e:
            return json.dumps({"error": f"Nie udało się połączyć z serwisem pogodowym: {str(e)}"}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": f"Błąd parsowania danych o pogodzie: {str(e)}"}, ensure_ascii=False)

    def _get_memory_path(self) -> str:
        import os
        return os.path.join("data", "memory.json")

    def _load_memory(self) -> dict:
        import os, json
        path = self._get_memory_path()
        if not os.path.exists(path):
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Błąd wczytywania pamięci: {e}")
            return {}

    def _save_memory(self, memory: dict) -> bool:
        import os, json
        path = self._get_memory_path()
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(memory, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            logging.error(f"Błąd zapisywania pamięci: {e}")
            return False

    def _save_note(self, key: str, content: str) -> str:
        if not key or not content:
            return json.dumps({"error": "Brakuje klucza lub treści notatki."}, ensure_ascii=False)
        memory = self._load_memory()
        memory[key] = content
        if self._save_memory(memory):
            return json.dumps({"result": "success", "message": f"Zapisano notatkę pod kluczem '{key}'."}, ensure_ascii=False)
        return json.dumps({"error": "Nie udało się zapisać notatki na dysku."}, ensure_ascii=False)

    def _read_notes(self, key: str = None) -> str:
        memory = self._load_memory()
        if not memory:
            return json.dumps({"message": "Notatnik jest pusty."}, ensure_ascii=False)
        if key:
            if key in memory:
                return json.dumps({key: memory[key]}, ensure_ascii=False)
            else:
                return json.dumps({"error": f"Nie znaleziono notatki o kluczu '{key}'."}, ensure_ascii=False)
        else:
            return json.dumps({"keys": list(memory.keys())}, ensure_ascii=False)

    def _delete_note(self, key: str) -> str:
        if not key:
            return json.dumps({"error": "Brakuje klucza notatki do usunięcia."}, ensure_ascii=False)
        memory = self._load_memory()
        if key in memory:
            del memory[key]
            if self._save_memory(memory):
                return json.dumps({"result": "success", "message": f"Usunięto notatkę '{key}'."}, ensure_ascii=False)
            return json.dumps({"error": "Nie udało się zapisać zmian na dysku."}, ensure_ascii=False)
        return json.dumps({"error": f"Nie znaleziono notatki o kluczu '{key}'."}, ensure_ascii=False)
