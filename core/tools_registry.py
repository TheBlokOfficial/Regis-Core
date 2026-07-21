import json
import logging
import os
import datetime
import uuid
import requests
from typing import Any

from core.schemas import BASE_TOOLS_SCHEMA


class ToolsRegistry:
    """Rejestr narzędzi dostarczanych dla modelu LLM."""
    
    def __init__(self, ha_client, tier: str = "regis"):
        self.ha_client = ha_client
        self.tier = tier
        
    def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> str:
        """Kieruje wywołanie narzędzia do odpowiedniej logiki."""
        try:
            # Weryfikacja uprawnień na podstawie tieru
            tier_clearance = {"butler": 1, "regis": 2, "prime": 3}
            current_clearance = tier_clearance.get(self.tier, 1)
            
            tool_def = None
            for t in BASE_TOOLS_SCHEMA:
                if t["function"]["name"] == tool_name:
                    tool_def = t
                    break
                    
            if tool_def is None:
                return json.dumps({"error": f"Narzędzie '{tool_name}' nie istnieje."}, ensure_ascii=False)
            
            req_tier = tool_def.get("required_tier", "butler")
            if tier_clearance.get(req_tier, 1) > current_clearance:
                return json.dumps({"error": f"Odmowa dostępu do '{tool_name}' w obecnym trybie."}, ensure_ascii=False)

            dispatch = {
                "get_devices": lambda: self._get_devices(arguments.get("domain")),
                "get_device_state": lambda: self._get_device_state(arguments.get("entity_id")),
                "execute_ha_action": lambda: self._execute_ha_action(
                    arguments.get("action"), arguments.get("entity_id"), arguments.get("parameters")),
                "get_current_time": lambda: self._get_current_time(),
                "get_weather": lambda: self._get_weather(arguments.get("location")),
            }
            
            handler = dispatch.get(tool_name)
            if handler:
                return handler()
            return json.dumps({"error": f"Nieznane narzędzie: {tool_name}"}, ensure_ascii=False)
            
        except Exception as e:
            logging.error(f"Błąd wykonania narzędzia {tool_name}: {e}")
            return json.dumps({"error": f"Wystąpił błąd podczas wykonania: {str(e)}"}, ensure_ascii=False)

    # ─── Home Assistant ───────────────────────────────────────────────

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
            return json.dumps({"error": f"Urządzenie o ID '{entity_id}' nie zostało znalezione."}, ensure_ascii=False)

    def _execute_ha_action(self, action: str, entity_id: str, parameters: dict[str, Any]) -> str:
        try:
            states = self.ha_client.get_all_states()
        except Exception:
            states = {}
            
        if action not in ["turn_on", "turn_off", "toggle"]:
            return json.dumps({"error": f"Nieprawidłowa akcja: '{action}'. Dozwolone: 'turn_on', 'turn_off', 'toggle'. Użyj 'turn_on' do zmiany jasności/koloru."}, ensure_ascii=False)

        if isinstance(entity_id, list):
            invalid_ids = [eid for eid in entity_id if eid not in states]
            if invalid_ids:
                return json.dumps({"error": f"Nieistniejące entity_id: {invalid_ids}. Użyj najpierw narzędzia 'get_devices'."}, ensure_ascii=False)
        elif isinstance(entity_id, str):
            if entity_id not in states:
                return json.dumps({"error": f"Nieistniejące entity_id: '{entity_id}'. Użyj najpierw narzędzia 'get_devices'."}, ensure_ascii=False)
                
        success = self.ha_client.execute_action(action, entity_id, parameters)
        if success:
            return json.dumps({"result": "success", "message": f"Wykonano {action} na {entity_id}."}, ensure_ascii=False)
        else:
            return json.dumps({"error": f"Akcja {action} nie powiodła się dla {entity_id}."}, ensure_ascii=False)

    # ─── Narzędzia ogólne ─────────────────────────────────────────────

    def _get_current_time(self) -> str:
        now = datetime.datetime.now()
        days = ["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek", "Sobota", "Niedziela"]
        day = days[now.weekday()]
        return json.dumps({
            "current_time": now.strftime("%Y-%m-%d %H:%M:%S"),
            "day_of_week": day
        }, ensure_ascii=False)

    def _get_weather(self, location: str) -> str:
        if not location:
            return json.dumps({"error": "Musisz podać nazwę miasta."}, ensure_ascii=False)
        
        try:
            url = f"https://wttr.in/{location}?format=j1"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            current = data.get("current_condition", [{}])[0]
            if not current:
                return json.dumps({"error": "Nie znaleziono danych o pogodzie dla podanej lokalizacji."}, ensure_ascii=False)
                
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


