import json
import logging
import requests
from requests.exceptions import RequestException
from typing import Any

from core.exceptions import HomeAssistantConnectionError

class HomeAssistantClient:
    """Klient zarządzający komunikacją z fizycznym serwerem Home Assistant REST API."""

    def __init__(self, url: str, token: str, aliases: dict[str, str] = None):
        """Inicjalizuje klienta HA.
        
        Args:
            url (str): Adres URL serwera Home Assistanta.
            token (str): Długoterminowy token dostępu z HA.
            aliases (dict[str, str], optional): Słownik mapujący skomplikowane nazwy encji na przyjazne.
        """
        self.url = url.rstrip("/")
        self.token = token
        self.aliases = aliases or {}
        logging.info(f"Zainicjalizowano HomeAssistantClient dla URL: {self.url}")

    def _get_headers(self) -> dict[str, str]:
        """Pobiera nagłówki wymagane do autoryzacji żądań HTTP."""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def get_all_states(self) -> dict[str, dict[str, Any]]:
        """Pobiera z Home Assistanta listę wszystkich encji i ich stanów.
        
        Returns:
            dict[str, dict[str, Any]]: Słownik z aktualnymi stanami odfiltrowanych urządzeń.
        Raises:
            HomeAssistantConnectionError: W przypadku błędu połączenia z HA.
        """
        url = f"{self.url}/api/states"
        
        try:
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            data = response.json()
            
            allowed_domains = ["light", "switch", "climate", "media_player"]
            filtered_state = {}
            
            for entity in data:
                entity_id = entity["entity_id"]
                domain = entity_id.split(".")[0]
                
                if domain not in allowed_domains:
                    continue
                
                original_name = entity["attributes"].get("friendly_name", "Nieznana Nazwa")
                friendly_name = self.aliases.get(entity_id, original_name)
                
                filtered_state[entity_id] = {
                    "state": entity["state"],
                    "friendly_name": friendly_name
                }
                    
            return filtered_state
        except RequestException as e:
            logging.error(f"[BŁĄD HA] Nie udało się pobrać stanu: {e}")
            raise HomeAssistantConnectionError(f"Nie można pobrać stanów HA: {e}")

    def execute_action(self, action: str, entity_id: str | list[str], parameters: dict[str, Any] | None = None) -> bool:
        """Wysyła polecenie zmiany stanu do fizycznego Home Assistanta.
        
        Args:
            action (str): Typ akcji (np. 'turn_on', 'turn_off').
            entity_id (str | list[str]): Identyfikator/y encji w HA (np. 'light.salon').
            parameters (dict, optional): Dodatkowe parametry przekazywane do usługi (np. {'brightness_pct': 50}).
            
        Returns:
            bool: True jeśli akcja została przyjęta do realizacji.
        Raises:
            HomeAssistantConnectionError: Przy utracie połączenia z serwerem.
        """
        if parameters is None:
            parameters = {}
            
        if isinstance(entity_id, list):
            all_success = True
            for single_id in entity_id:
                if not self.execute_action(action, single_id, parameters):
                    all_success = False
            return all_success
            
        if not isinstance(entity_id, str):
            logging.warning("[HA CLIENT] Oczekiwano stringa lub listy jako entity_id.")
            return False
            
        domain = entity_id.split(".")[0]
        
        if action == "turn_on":
            service = "turn_on"
        elif action == "turn_off":
            service = "turn_off"
        else:
            logging.warning(f"[HA CLIENT] Nie obsługiwana akcja: {action}")
            return False
            
        url = f"{self.url}/api/services/{domain}/{service}"
        
        payload_dict = {"entity_id": entity_id}
        if parameters:
            payload_dict.update(parameters)
            
        try:
            response = requests.post(url, json=payload_dict, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            logging.debug(f"[HA CLIENT] Pomyślnie wysłano akcję {service} dla {entity_id}.")
            return True
        except RequestException as e:
            logging.error(f"[BŁĄD HA] Wykonanie akcji odrzucone: {e}")
            raise HomeAssistantConnectionError(f"Home Assistant odrzucił akcję: {e}")
