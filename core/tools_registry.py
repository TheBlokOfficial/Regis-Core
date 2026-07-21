import json
import logging
import os
import datetime
import uuid
import requests
from typing import Any, Callable

from core.schemas import BASE_TOOLS_SCHEMA

class ToolsRegistry:
    """Rejestr narzędzi dostarczanych dla modelu LLM."""
    
    def __init__(self, ha_client, tier: str = "regis"):
        self.ha_client = ha_client
        self.tier = tier
        
        # Schematy narzędzi importowane z zewnętrznego pliku
        base_tools_schema = BASE_TOOLS_SCHEMA
        
        # Definicja poziomów uprawnień
        tier_clearance = {
            "butler": 1,
            "regis": 2,
            "prime": 3
        }
        current_clearance = tier_clearance.get(self.tier, 1)
        
        # Filtrowanie narzędzi na podstawie tieru
        filtered_schema = []
        for tool in base_tools_schema:
            req_tier = tool.get("required_tier", "butler")
            tool_clearance = tier_clearance.get(req_tier, 1)
            
            if current_clearance < tool_clearance:
                continue
                
            # Usuwamy niestandardowe pole "required_tier", ponieważ API Ollamy może je odrzucić
            tool_copy = tool.copy()
            if "required_tier" in tool_copy:
                del tool_copy["required_tier"]
            filtered_schema.append(tool_copy)
        self.tools_schema = filtered_schema
        
        # Inicjalizacja biurka dla modelu (Desk Manager)
        self.desk_apps = {}
        
    def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> str:
        """Kieruje wywołanie narzędzia do odpowiedniej logiki."""
        try:
            allowed_tools = [t["function"]["name"] for t in self.tools_schema]
            if tool_name not in allowed_tools:
                return f'{{"error": "Narzędzie {tool_name} nie istnieje lub odmowa dostępu w obecnym trybie."}}'

            if tool_name == "get_devices":
                return self._get_devices(arguments.get("domain"))
            elif tool_name == "get_device_state":
                return self._get_device_state(arguments.get("entity_id"))
            elif tool_name == "execute_ha_action":
                return self._execute_ha_action(arguments.get("action"), arguments.get("entity_id"), arguments.get("parameters"))
            elif tool_name == "get_current_time":
                return self._get_current_time()
            elif tool_name == "get_weather":
                return self._get_weather(arguments.get("location"))
            elif tool_name == "save_note":
                return self._save_note(arguments.get("key", ""), arguments.get("content", ""), arguments.get("clear_queue_ids"))
            elif tool_name == "queue_note":
                return self._queue_note(arguments.get("fact", ""))
            elif tool_name == "open_notes":
                return self._open_notes()
            elif tool_name == "close_notes":
                return self._close_notes()
            elif tool_name == "clear_queue":
                return self._clear_queue(arguments.get("ids", []))
            elif tool_name == "open_notebook_search":
                return self._open_notebook_search(arguments.get("query"))
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
        now = datetime.datetime.now()
        days = ["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek", "Sobota", "Niedziela"]
        day = days[now.weekday()]
        return json.dumps({
            "current_time": now.strftime("%Y-%m-%d %H:%M:%S"),
            "day_of_week": day
        }, ensure_ascii=False)

    def _get_weather(self, location: str) -> str:
        if not location:
            return json.dumps({"error": "Musisz podać nazwę miasta."})
        
        try:
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
        return os.path.join("data", "memory.json")

    def _load_memory(self) -> dict:
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
        path = self._get_memory_path()
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(memory, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            logging.error(f"Błąd zapisywania pamięci: {e}")
            return False

    def _queue_note(self, fact: str) -> str:
        self._ping_app("notatki")
        if not fact:
            return json.dumps({"error": "Brakuje faktu do zapisania."}, ensure_ascii=False)
        
        path = os.path.join("data", "pending_notes.json")
        pending = []
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    pending = json.load(f)
            except Exception:
                pass
                
        pending.append({
            "id": uuid.uuid4().hex[:8],
            "timestamp": datetime.datetime.now().isoformat(),
            "fact": fact
        })
        
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(pending, f, ensure_ascii=False, indent=4)
            self._notes_cache = None
            return json.dumps({"result": "success", "message": "Zapisano fakt w kolejce do przetworzenia."}, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Błąd zapisu do kolejki notatek: {e}")
            return json.dumps({"error": "Nie udało się zapisać faktu do kolejki."}, ensure_ascii=False)

    def tick_desk(self):
        """Zmniejsza TTL wszystkich otwartych aplikacji na biurku i zamyka przeterminowane."""
        expired = []
        for app, data in self.desk_apps.items():
            data["ttl"] -= 1
            if data["ttl"] <= 0:
                expired.append(app)
        for app in expired:
            logging.info(f"Aplikacja '{app}' została zamknięta automatycznie (TTL timeout).")
            del self.desk_apps[app]

    def _ping_app(self, app_name: str):
        if app_name in self.desk_apps:
            self.desk_apps[app_name]["ttl"] = 10

    def get_desk_state(self) -> str:
        """Pobiera aktualny stan biurka z otwartymi aplikacjami."""
        if not self.desk_apps:
            return ""
            
        state_parts = []
        for app, data in self.desk_apps.items():
            content = "Błąd pobierania stanu."
            if "get_state" in data:
                try:
                    content = data["get_state"]()
                except Exception as e:
                    content = f"Błąd wstrzykiwania stanu aplikacji: {e}"
            state_parts.append(f"[Biurko: Aplikacja '{app}' (wygasną za {data['ttl']} tur bezczynności)]\nZawartość:\n{content}")
        
        return "\n\n".join(state_parts)

    def _get_staging_state(self) -> str:
        """Pobiera zawartość brudnopisu używając cache."""
        if getattr(self, '_notes_cache', None) is None:
            path = os.path.join("data", "pending_notes.json")
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        pending = json.load(f)
                        self._notes_cache = json.dumps(pending, ensure_ascii=False, indent=2) if pending else "Kolejka jest pusta."
                except Exception:
                    self._notes_cache = "Błąd odczytu."
            else:
                self._notes_cache = "Kolejka jest pusta."
        return self._notes_cache

    def _open_notes(self) -> str:
        self._notes_cache = None
        self.desk_apps["notatki"] = {
            "ttl": 10,
            "get_state": self._get_staging_state
        }
        
        path = os.path.join("data", "pending_notes.json")
        try:
            with open(path, "r", encoding="utf-8") as f:
                pending = json.load(f)
                preview = {"status": "sukces", "otwarte_elementy": len(pending), "wskazówka": "Pełna treść znajduje się w bloku <desk_state> poniżej."}
        except:
            preview = {"status": "sukces", "otwarte_elementy": 0, "wskazówka": "Brudnopis jest pusty lub wystąpił błąd. Spójrz na <desk_state>."}
            
        return json.dumps(preview, ensure_ascii=False)

    def _close_notes(self) -> str:
        if "notatki" in self.desk_apps:
            del self.desk_apps["notatki"]
        return json.dumps({"result": "success", "message": "Aplikacja Brudnopisu została poprawnie zamknięta i usunięta z biurka."}, ensure_ascii=False)

    def _clear_queue(self, ids: list[str]) -> str:
        self._ping_app("notatki")
        self._notes_cache = None
            
        if not ids or not isinstance(ids, list):
            return json.dumps({"error": "Musisz podać listę 'ids' do usunięcia."}, ensure_ascii=False)
            
        path = os.path.join("data", "pending_notes.json")
        if not os.path.exists(path):
            return json.dumps({"error": "Kolejka nie istnieje."}, ensure_ascii=False)
            
        try:
            with open(path, "r", encoding="utf-8") as f:
                pending = json.load(f)
                
            original_len = len(pending)
            pending = [note for note in pending if note.get("id") not in ids]
            
            with open(path, "w", encoding="utf-8") as f:
                json.dump(pending, f, ensure_ascii=False, indent=4)
                
            removed = original_len - len(pending)
            return json.dumps({"result": "success", "message": f"Usunięto {removed} notatek z kolejki brudnopisu."}, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Błąd czyszczenia kolejki: {e}")
            return json.dumps({"error": "Wystąpił błąd podczas usuwania pozycji z kolejki."}, ensure_ascii=False)

    def _save_note(self, key: str, content: str, clear_queue_ids: list[str] = None) -> str:
        self._ping_app("notatki")
        self._ping_app("wyniki_wyszukiwania")
            
        if not key or not content:
            return json.dumps({"error": "Brakuje klucza lub treści notatki."}, ensure_ascii=False)
        memory = self._load_memory()
        memory[key] = content
        if self._save_memory(memory):
            msg = f"Zapisano notatkę pod kluczem '{key}'."
            if clear_queue_ids:
                clear_res = json.loads(self._clear_queue(clear_queue_ids))
                if "error" not in clear_res:
                    msg += f" {clear_res.get('message', '')}"
            return json.dumps({"result": "success", "message": msg}, ensure_ascii=False)
        return json.dumps({"error": "Nie udało się zapisać notatki na dysku."}, ensure_ascii=False)

    def _open_notebook_search(self, query: str = None) -> str:
        memory = self._load_memory()
        if not memory:
            return json.dumps({"status": "sukces", "znaleziono": 0, "message": "Notatnik jest pusty."}, ensure_ascii=False)
            
        results = {}
        if query:
            if query in memory:
                results = {query: memory[query]}
        else:
            results = {"Dostępne klucze (brak query)": list(memory.keys())}
            
        self.desk_apps["wyniki_wyszukiwania"] = {
            "ttl": 10,
            "get_state": lambda: json.dumps(results, ensure_ascii=False, indent=2)
        }
        
        preview = {
            "status": "sukces",
            "znaleziono": len(results),
            "podglad_kluczy": list(results.keys())[:3],
            "wskazówka": "Wyniki wyszukiwania przypięto do Twojego biurka. Przejdź do bloku <desk_state> na dole, by je przeczytać."
        }
        return json.dumps(preview, ensure_ascii=False)

    def _delete_note(self, key: str) -> str:
        self._ping_app("notatki")
        self._ping_app("wyniki_wyszukiwania")
        if not key:
            return json.dumps({"error": "Brakuje klucza notatki do usunięcia."}, ensure_ascii=False)
        memory = self._load_memory()
        if key in memory:
            del memory[key]
            if self._save_memory(memory):
                return json.dumps({"result": "success", "message": f"Usunięto notatkę '{key}'."}, ensure_ascii=False)
            return json.dumps({"error": "Nie udało się zapisać zmian na dysku."}, ensure_ascii=False)
        return json.dumps({"error": f"Nie znaleziono notatki o kluczu '{key}'."}, ensure_ascii=False)
