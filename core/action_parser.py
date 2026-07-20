import json
import logging
from typing import Any, Dict, Optional, Tuple
from core.exceptions import HomeAssistantConnectionError

class ActionResult:
    """Reprezentacja pojedynczej decyzji/akcji systemu bazującej na LLM."""
    def __init__(self, is_valid: bool, error: str = ""):
        self.is_valid = is_valid
        self.error = error
        
        # Oczekiwane dane od LLM
        self.action: str = "none"
        self.entity_id: str | list[str] = "none"
        self.parameters: dict[str, Any] = {}
        self.reply: str = ""
        
        # Wynik po wykonaniu przez HA
        self.ha_execution_attempted: bool = False
        self.ha_success: bool = False
        self.ha_error_msg: str = ""

def parse_llm_response(response_text: str) -> ActionResult:
    """Parsuje tekstową odpowiedź JSON od modelu LLM.
    
    Args:
        response_text (str): Odpowiedź wygenerowana przez model z JSONem w środku.
        
    Returns:
        ActionResult: Obiekt przechowujący spójne dane o intencjach modelu.
    """
    if response_text.startswith("[BŁĄD]"):
        return ActionResult(is_valid=False, error=response_text)
        
    try:
        data = json.loads(response_text)
        result = ActionResult(is_valid=True)
        result.action = data.get("action", "none")
        result.entity_id = data.get("entity_id", "none")
        result.parameters = data.get("parameters", {})
        result.reply = data.get("reply", "")
        return result
    except json.JSONDecodeError as e:
        logging.error(f"Nieprawidłowy JSON od modelu: {response_text}")
        return ActionResult(is_valid=False, error=f"Błąd parsowania JSON: {e}")

def execute_parsed_action(parsed_result: ActionResult, ha_client) -> ActionResult:
    """Wykonuje na Home Assistantcie polecenia ze sparsowanego obiektu.
    
    Args:
        parsed_result (ActionResult): Obiekt z danymi od modelu.
        ha_client (HomeAssistantClient): Aktualny klient HA.
        
    Returns:
        ActionResult: Zaktualizowany obiekt zawierający status wykonania fizycznego.
    """
    if not parsed_result.is_valid or parsed_result.action == "none" or parsed_result.entity_id == "none":
        return parsed_result
        
    parsed_result.ha_execution_attempted = True
    
    try:
        success = ha_client.execute_action(
            parsed_result.action, 
            parsed_result.entity_id, 
            parsed_result.parameters
        )
        parsed_result.ha_success = success
    except HomeAssistantConnectionError as e:
        parsed_result.ha_success = False
        parsed_result.ha_error_msg = str(e)
        logging.error(f"Utracono połączenie podczas wywoływania: {e}")
        
    return parsed_result
